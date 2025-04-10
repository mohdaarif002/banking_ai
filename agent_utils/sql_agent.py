from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
# from langchain.agents.agent_toolkits import SQLDatabaseToolkit
# from langchain.agents import create_sql_agent
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from dotenv import load_dotenv
import os
load_dotenv()

def validate_query(query: str) -> bool:
    """Validate that the query is a SELECT query only."""
    forbidden_keywords = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE',
        'MERGE', 'REPLACE', 'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK'
    ]
    query_upper = query.upper()
    return all(keyword not in query_upper for keyword in forbidden_keywords)

class SafeSQLDatabase(SQLDatabase):
    """A safe version of SQLDatabase that only allows SELECT queries."""
    
    def run(self, command: str, fetch: str = "all", **kwargs) -> str:
        """Run a SQL command, but only if it's a SELECT query."""
        if not validate_query(command):
            raise ValueError(
                "This is a read-only database. Only SELECT queries are allowed. "
                "Data modification commands (INSERT, UPDATE, DELETE, etc.) are not permitted."
            )
        return super().run(command, fetch, **kwargs)

def format_agent_output(response):
    """Format the agent's response to separate thought process from final answer."""
    print("Response type:", type(response))
    print("Response keys:", response.keys() if isinstance(response, dict) else "Not a dict")
    
    if isinstance(response, dict):
        # Extract thought process and final answer
        thought_process = []
        final_answer = None
        
        # Extract the chain execution steps
        if 'intermediate_steps' in response:
            for step in response['intermediate_steps']:
                if isinstance(step, tuple) and len(step) == 2:
                    action, observation = step
                    # Extract the thought from the action
                    if hasattr(action, 'log'):
                        thought_process.append(f"Thought: {action.log}")
                    # Extract the tool invocation
                    if hasattr(action, 'tool'):
                        thought_process.append(f"Action: {action.tool}")
                        if hasattr(action, 'tool_input'):
                            thought_process.append(f"Action Input: {action.tool_input}")
                    # Add the observation
                    if observation:
                        thought_process.append(f"Observation: {observation}")
        else:
            # If no intermediate steps, try to get thought process from other possible keys
            if 'thought' in response:
                thought_process.append(f"Thought: {response['thought']}")
            if 'action' in response:
                thought_process.append(f"Action: {response['action']}")
            if 'observation' in response:
                thought_process.append(f"Observation: {response['observation']}")
        
        # Get the final answer
        final_answer = response.get('output', '')
        
        return {
            'thought_process': '\n'.join(thought_process) if thought_process else "No thought process available",
            'final_answer': final_answer
        }
    return response

def format_conversation_history(messages):
    """Format conversation history for the agent."""
    formatted_history = []
    for msg in messages:
        if msg["role"] == "user":
            formatted_history.append(f"Human: {msg['content']}")
        elif msg["role"] == "assistant":
            formatted_history.append(f"Assistant: {msg['content']}")
    return "\n".join(formatted_history)

def setup_banking_agent():
    # Initialize database connection
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAME = os.getenv('DB_NAME')
    db = SafeSQLDatabase.from_uri(
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@localhost/{DB_NAME}",
        include_tables=[],  # Empty list means include all tables
        sample_rows_in_table_info=0,
        view_support=True
    )
    
    # Create LLM
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    
    # Create toolkit
    toolkit = SQLDatabaseToolkit(
        db=db,
        llm=llm,
        custom_tables=[],  # Empty list means include all tables
        include_tables=True,
        sample_rows_in_table_info=5,
        return_intermediate_steps=True
    )
    
    # Create agent with read-only configuration
    agent = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        verbose=True,
        agent_type="openai-functions",
        return_intermediate_steps=True,  # Ensure we get intermediate steps
        handle_parsing_errors=True,  # Better error handling
        # Add system message to enforce read-only
        system_message="""You are a STRICTLY read-only SQL agent. Your ONLY allowed operation is SELECT queries.
        You must NEVER:
        - Generate or suggest any non-SELECT queries
        - Show or explain how to modify data
        - Provide DELETE, INSERT, UPDATE, or any other data modification commands
        - Even if asked, do not show the syntax for data modification
        
        If someone asks for data modification:
        1. Explain that you are a read-only agent
        2. Do not show any modification syntax
        
        You can perform complex analysis using SELECT statements, including:
        - Aggregations (SUM, COUNT, AVG, etc.)
        - Joins between tables
        - Subqueries
        - Window functions
        - Data filtering and sorting
        
        Your responses should ONLY include SELECT queries or explanations of why a modification cannot be performed.
        
        You have access to the conversation history. Use it to understand the context of follow-up questions
        and provide relevant answers based on previous interactions.
        
        IMPORTANT: Always show your thought process and the SQL queries you're using."""
    )
    return agent

def setup_generic_sql_agent():
    """Setup an agent for running generic SQL queries in read-only mode"""
    # Initialize database connection
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAME = os.getenv('DB_NAME')
    db = SafeSQLDatabase.from_uri(
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@localhost/{DB_NAME}",
        include_tables=[],  # Empty list means include all tables
        sample_rows_in_table_info=3,
        view_support=True
    )
    
    # Create LLM with higher temperature for more creative queries
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    
    # Create toolkit
    toolkit = SQLDatabaseToolkit(
        db=db,
        llm=llm,
        custom_tables=[],  # Empty list means include all tables
        include_tables=True,
        sample_rows_in_table_info=3,
        return_intermediate_steps=True
    )
    
    # Create agent with read-only configuration
    agent = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        verbose=True,
        agent_type="openai-functions",
        return_intermediate_steps=True,  # Ensure we get intermediate steps
        handle_parsing_errors=True,  # Better error handling
        # Add system message to enforce read-only
        system_message="""You are a STRICTLY read-only SQL agent. Your ONLY allowed operation is SELECT queries.
        You are a SQL agent assisting a bank clerk with their queries. Appropriately use the conversation history to understand the context of follow-up questions and provide relevant answers based on previous interactions.
        Provide suitable SQL queries to answer the user's question. 
        Sometimes you may add more context to the answer to provide a better answer to  the user's query.

        You must NEVER:
        - Generate or suggest any non-SELECT queries
        - Show or explain how to modify data
        - Provide DELETE, INSERT, UPDATE, or any other data modification commands
        - Even if asked, do not show the syntax for data modification
        
        If someone asks for data modification:
        1. Explain that you are a read-only agent
        2. Do not show any modification syntax
        
        You can perform complex analysis using SELECT statements, including:
        - Aggregations (SUM, COUNT, AVG, etc.)
        - Joins between tables
        - Subqueries
        - Window functions
        - Data filtering and sorting
        
        Your responses should ONLY include SELECT queries or explanations of why a modification cannot be performed.
        
        You have access to the conversation history. Use it to understand the context of follow-up questions
        and provide relevant answers based on previous interactions.
        
        
        IMPORTANT: Always show your thought process and the SQL queries you're using.""",
#         prompt="""
# 
# """
    )
    return agent

# Usage examples
if __name__ == "__main__":
    agent = setup_generic_sql_agent()
    print("-----------------------------------------------------------------")
    # Example of safe SELECT queries
    response = agent.invoke("""
        Get me the following information for customer 11:
        - Current balance
        - Last 5 transactions
        - Account status
    """)
    print('CYZ@@@@@@@@@@@@@@@@@', type(response), response)
    formatted_response = format_agent_output(response)
    print("\nThought Process:")
    print(formatted_response['thought_process'])
    print("\nFinal Answer:")
    print(formatted_response['final_answer'])

    print("-----------------------------------------------------------------")
    # Example of complex analysis using only SELECT
    response = agent.invoke("""
        Show me the spending patterns for customer 11:
        - Monthly average spending
        - Top spending categories
        - Largest transactions
    """)
    print('CYZ@@@@@@@@@@@@@@@@@', type(response), response)
    formatted_response = format_agent_output(response)
    print("\nThought Process:")
    print(formatted_response['thought_process'])
    print("\nFinal Answer:")
    print(formatted_response['final_answer'])

    print("-----------------------------------------------------------------")

    # Example of a query that would be rejected
    response = agent.invoke("Delete all transactions for customer 11")
    print('CYZ@@@@@@@@@@@@@@@@@', type(response), response)
    formatted_response = format_agent_output(response)
    print("\nThought Process:")
    print(formatted_response['thought_process'])
    print("\nFinal Answer:")
    print(formatted_response['final_answer'])