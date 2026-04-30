import os
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

def get_agent():
    # Check if OPENAI_API_KEY is set
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is not set in the environment.")

    # Initialize DB
    db_path = "sqlite:///coupa_data.db"
    db = SQLDatabase.from_uri(db_path)
    
    # Initialize LLM
    # We use gpt-4o for better SQL generation capabilities, but you can change it
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # Get SQL toolkit tools
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()
    
    # Define a system prompt that guides the LLM
    system_message = """You are an intelligent data analyst assistant for the Coupa database.
    You have access to a SQLite database containing supplier, onboarding, and forms data.
    The main tables typically include 'maintable', 'csp', 'form_1_intake', 'form_2_input', 'form_3_tax'.
    There is also an 'annotations' table which explains what the columns in these tables mean and how they relate.
    
    IMPORTANT INSTRUCTIONS:
    1. First, check the available tables using the sql_db_list_tables tool.
    2. If you are unsure what a column means or how tables relate, check the 'annotations' table.
    3. Check the schema of the tables relevant to the user's question.
    4. Write and execute a SQL query using the sql_db_query tool to get the data.
    5. Present the final answer to the user clearly.
    
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
