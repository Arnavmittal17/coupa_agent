import os
from datetime import datetime, timezone
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from tools import generate_chart

def get_agent():
    # Check if OPENAI_API_KEY is set
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is not set in the environment.")

    # Initialize DB
    db_path = "sqlite:///coupa_data.db"
    db = SQLDatabase.from_uri(db_path)
    
    # Initialize LLM
    # We use gpt-4o for better SQL generation capabilities, but you can change it
    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    
    # Get SQL toolkit tools
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()
    # Add custom plotting tool to visualize SQL results
    tools.append(generate_chart)
    
    # Define a system prompt that guides the LLM
    now = datetime.now(timezone.utc)
    system_message = f"""You are an intelligent data analyst assistant for the Coupa database.
    
    CURRENT DATE AND TIME: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC
    Use this as the reference for any time-relative queries (e.g. "last month", "this year", "recent").
    
    You have access to a SQLite database containing supplier, onboarding, and forms data.
    The main tables typically include 'maintable', 'csp', 'form_1_intake', 'form_2_input', 'form_3_tax'.
    There is also an 'annotations' table which explains what the columns in these tables mean and how they relate.
    
    DATABASE DATETIME FORMAT:
    All date/datetime columns in this database are stored as TEXT in the format 'YYYY-MM-DD HH:MM:SS' (e.g. '2025-04-30 14:22:00').
    When filtering by date, use string comparison or SQLite date functions like date(), strftime().
    Example: WHERE CREATED_DATE >= '2025-01-01' AND CREATED_DATE < '2025-02-01'
    
    IMPORTANT INSTRUCTIONS:
    1. First, check the available tables using the sql_db_list_tables tool.
    2. If you are unsure what a column means or how tables relate, check the 'annotations' table.
    3. Check the schema of the tables relevant to the user's question.
    4. Write and execute a SQL query using the sql_db_query tool to get the data.
    5. Present the final answer to the user clearly.
    
    CHARTING INSTRUCTIONS:
    When the user asks for a chart, plot, graph, or visual comparison:
    1. First run the SQL query to get the data.
    2. Choose the correct chart_type based on the user's request:
       - Trends over time → "line"
       - Comparing categories → "bar"
       - Showing proportions → "pie"
       - Showing distributions → "histogram"
    3. Call generate_chart with ALL required parameters:
       - data: the SQL query results as a JSON string
       - chart_type: one of "bar", "line", "pie", "histogram"
       - x_column: exact column name from the query results
       - y_column: exact column name (REQUIRED for bar and line)
       - title: a clear, descriptive title
    4. Do NOT send raw data without specifying chart_type and columns.
    5. Keep the SQL result set small (use LIMIT, GROUP BY, aggregations).
    
    RESPONSE RULES (STRICT):
    - NEVER generate base64-encoded images. NEVER include "data:image" in your response.
    - NEVER reproduce or echo the JSON output from generate_chart in your response.
    - After calling generate_chart, the frontend renders the chart automatically.
    - Your response should ONLY contain a brief text summary of the data (e.g. key numbers, insights).
    - Keep your final response short and concise.
    
    Always prioritize correctness in your SQL queries. If an error occurs, look at the error message, correct your query, and try again.
    """
    
    # Create Checkpointer for short-term memory
    memory = MemorySaver()
    
    # Create the React Agent using LangGraph
    agent_executor = create_react_agent(
        llm, 
        tools, 
        checkpointer=memory, 
        prompt=system_message
    )
    
    return agent_executor
