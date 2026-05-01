"""
tools.py – Deterministic Plotly chart tool for the Coupa LangChain React Agent.

Architecture: "LLM decides WHAT. Tool executes HOW."

The LLM is responsible for choosing chart_type, columns, and title.
This tool only parses, validates, builds, and returns a confirmation.
The Plotly JSON is stored in a side-channel buffer so it never enters
the LLM's conversation context.
Zero inference. Zero guessing. Fail-fast on bad input.
"""

import json
from typing import Optional, Literal

import pandas as pd
import plotly.express as px
import plotly.io as pio
from pydantic import BaseModel, Field
from langchain.tools import tool


# ---------------------------------------------------------------------------
# Pydantic input schema – enforces structure at the LangChain level
# ---------------------------------------------------------------------------

class ChartInput(BaseModel):
    """Strict schema for the generate_chart tool."""

    data: str = Field(
        description=(
            "JSON string — a list of objects (records) from a SQL query. "
            'Example: \'[{"supplier": "Acme", "total": 500}]\''
        )
    )
    chart_type: Literal["bar", "line", "pie", "histogram"] = Field(
        description=(
            "The type of chart to create. Must be one of: "
            '"bar", "line", "pie", "histogram".'
        )
    )
    x_column: str = Field(
        description="The column name to use for the x-axis (or labels in a pie chart)."
    )
    y_column: Optional[str] = Field(
        default=None,
        description=(
            "The column name to use for the y-axis (values). "
            "Required for bar and line charts. Optional for histogram and pie."
        ),
    )
    color_column: Optional[str] = Field(
        default=None,
        description="Optional column name to group/color the data by.",
    )
    title: Optional[str] = Field(
        default=None,
        description="Optional chart title. If omitted a default is generated.",
    )


# ---------------------------------------------------------------------------
# Validation helpers – fail loud, fail fast
# ---------------------------------------------------------------------------

def _parse_data(raw: str) -> pd.DataFrame:
    """Parse the JSON string into a DataFrame. Raises on bad input."""
    raw = raw.strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"'data' is not valid JSON. First 200 chars: {raw[:200]}"
        ) from exc

    if isinstance(parsed, dict):
        parsed = [parsed]

    if not isinstance(parsed, list) or len(parsed) == 0:
        raise ValueError("'data' must be a non-empty JSON array of objects.")

    return pd.DataFrame(parsed)


def _validate_columns(df: pd.DataFrame, chart_type: str,
                       x_column: str, y_column: Optional[str]) -> None:
    """Ensure the requested columns exist and have compatible dtypes."""
    if x_column not in df.columns:
        raise ValueError(
            f"x_column '{x_column}' not found. "
            f"Available columns: {df.columns.tolist()}"
        )

    if chart_type in ("bar", "line") and y_column is None:
        raise ValueError(
            f"y_column is required for '{chart_type}' charts but was not provided."
        )

    if y_column is not None:
        if y_column not in df.columns:
            raise ValueError(
                f"y_column '{y_column}' not found. "
                f"Available columns: {df.columns.tolist()}"
            )
        if chart_type in ("bar", "line") and not pd.api.types.is_numeric_dtype(df[y_column]):
            raise ValueError(
                f"y_column '{y_column}' must be numeric for a {chart_type} chart, "
                f"but has dtype '{df[y_column].dtype}'."
            )


# ---------------------------------------------------------------------------
# Chart builders – one pure function per chart type, no guessing
# ---------------------------------------------------------------------------

_LAYOUT_DEFAULTS = dict(
    template="plotly_white",
    margin=dict(l=50, r=30, t=60, b=50),
    font=dict(family="Inter, sans-serif", size=13),
    title_x=0.5,                       # centred title
    title_font_size=16,
    xaxis_title_font_size=13,
    yaxis_title_font_size=13,
    legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
)


def _build_bar(df: pd.DataFrame, x: str, y: str,
               color: Optional[str], title: str) -> px.bar:
    fig = px.bar(
        df.sort_values(y, ascending=False),
        x=x, y=y, color=color,
        title=title,
        text_auto=".2s",
    )
    fig.update_layout(**_LAYOUT_DEFAULTS)
    fig.update_traces(textposition="outside")
    return fig


def _build_line(df: pd.DataFrame, x: str, y: str,
                color: Optional[str], title: str) -> px.line:
    # Attempt datetime conversion for proper time-axis ordering
    if not pd.api.types.is_datetime64_any_dtype(df[x]):
        try:
            df = df.copy()
            df[x] = pd.to_datetime(df[x])
        except (ValueError, TypeError):
            pass
    fig = px.line(
        df.sort_values(x),
        x=x, y=y, color=color,
        title=title,
        markers=True,
    )
    fig.update_layout(**_LAYOUT_DEFAULTS)
    return fig


def _build_histogram(df: pd.DataFrame, x: str,
                     color: Optional[str], title: str) -> px.histogram:
    fig = px.histogram(
        df, x=x, color=color,
        title=title,
        nbins=30,
    )
    fig.update_layout(**_LAYOUT_DEFAULTS, bargap=0.05)
    return fig


def _build_pie(df: pd.DataFrame, x: str, y: Optional[str],
               color: Optional[str], title: str) -> px.pie:
    if y is not None:
        # Use the provided values column
        fig = px.pie(df, names=x, values=y, title=title)
    else:
        # Count occurrences of x_column
        counts = df[x].value_counts().reset_index()
        counts.columns = [x, "count"]
        fig = px.pie(counts, names=x, values="count", title=title)

    fig.update_layout(**_LAYOUT_DEFAULTS)
    fig.update_traces(textinfo="label+percent", pull=[0.03] * len(df))
    return fig


_BUILDERS = {
    "bar": lambda df, x, y, c, t: _build_bar(df, x, y, c, t),
    "line": lambda df, x, y, c, t: _build_line(df, x, y, c, t),
    "histogram": lambda df, x, y, c, t: _build_histogram(df, x, c, t),
    "pie": lambda df, x, y, c, t: _build_pie(df, x, y, c, t),
}


# ---------------------------------------------------------------------------
# Side-channel chart buffer – keeps Plotly JSON out of the LLM context
# ---------------------------------------------------------------------------

_chart_buffer: list[str] = []


def get_pending_charts() -> list[str]:
    """Drain and return all chart JSON strings accumulated during the current
    agent run.  Called by app.py after the agent finishes."""
    charts = list(_chart_buffer)
    _chart_buffer.clear()
    return charts


# ---------------------------------------------------------------------------
# LangChain tool – the only public export
# ---------------------------------------------------------------------------

@tool("generate_chart", args_schema=ChartInput)
def generate_chart(
    data: str,
    chart_type: str,
    x_column: str,
    y_column: Optional[str] = None,
    color_column: Optional[str] = None,
    title: Optional[str] = None,
) -> str:
    """Create a Plotly chart and return it as a JSON string for Streamlit.

    USE THIS TOOL ONLY when the user asks for a chart, graph, plot, or
    visual comparison. Do NOT use it for plain-text answers.

    You MUST supply: data, chart_type, and x_column.
    You MUST supply y_column for bar and line charts.
    color_column and title are optional.

    CORRECT USAGE EXAMPLES:

    Example 1 – Bar chart of supplier counts by status:
        {
            "data": "[{\\"status\\": \\"Active\\", \\"count\\": 120}, {\\"status\\": \\"Inactive\\", \\"count\\": 45}]",
            "chart_type": "bar",
            "x_column": "status",
            "y_column": "count",
            "title": "Suppliers by Status"
        }

    Example 2 – Line chart of monthly spend:
        {
            "data": "[{\\"month\\": \\"2025-01\\", \\"spend\\": 50000}, {\\"month\\": \\"2025-02\\", \\"spend\\": 62000}]",
            "chart_type": "line",
            "x_column": "month",
            "y_column": "spend",
            "title": "Monthly Spend Trend"
        }

    Example 3 – Pie chart of form completion:
        {
            "data": "[{\\"form\\": \\"Intake\\", \\"completed\\": 80}, {\\"form\\": \\"Tax\\", \\"completed\\": 55}]",
            "chart_type": "pie",
            "x_column": "form",
            "y_column": "completed",
            "title": "Form Completion Breakdown"
        }

    NEVER omit chart_type or x_column. NEVER send empty data.
    """
    # 1. Parse ---------------------------------------------------------------
    df = _parse_data(data)

    # 2. Validate ------------------------------------------------------------
    _validate_columns(df, chart_type, x_column, y_column)

    if color_column and color_column not in df.columns:
        raise ValueError(
            f"color_column '{color_column}' not found. "
            f"Available columns: {df.columns.tolist()}"
        )

    # 3. Default title -------------------------------------------------------
    if not title:
        title = f"{chart_type.capitalize()} chart – {x_column}"
        if y_column:
            title += f" vs {y_column}"

    # 4. Build figure --------------------------------------------------------
    builder = _BUILDERS[chart_type]
    fig = builder(df, x_column, y_column, color_column, title)

    # 5. Store in side-channel, return short confirmation to LLM ------------
    _chart_buffer.append(pio.to_json(fig))

    return (
        f"Chart created successfully. Type: {chart_type}, "
        f"x: {x_column}, y: {y_column or 'N/A'}, title: {title}. "
        f"The chart is now displayed to the user."
    )
