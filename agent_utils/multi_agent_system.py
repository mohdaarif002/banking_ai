from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the language model
llm = ChatOpenAI(model="gpt-4o", temperature=0)

class AgentRouter:
    """Routes tasks to specialized agents based on the task type."""
    
    def __init__(self):
        self.agents: Dict[str, AgentExecutor] = {}
        self.initialize_agents()
    
    def initialize_agents(self):
        """Initialize all specialized agents."""
        # Data Processing Agent
        data_tools = [
            self.process_data,
            self.analyze_data,
            self.visualize_data
        ]
        self.agents["data"] = self.create_agent(
            "data_processing_agent",
            "You are a data processing specialist. You handle data cleaning, analysis, and visualization tasks.",
            data_tools
        )
        
        # File Management Agent
        file_tools = [
            self.read_file,
            self.write_file,
            self.delete_file
        ]
        self.agents["file"] = self.create_agent(
            "file_management_agent",
            "You are a file management specialist. You handle file operations like reading, writing, and deleting files.",
            file_tools
        )
        
        # API Management Agent
        api_tools = [
            self.call_api,
            self.process_api_response,
            self.handle_api_error
        ]
        self.agents["api"] = self.create_agent(
            "api_management_agent",
            "You are an API management specialist. You handle API calls, response processing, and error handling.",
            api_tools
        )
        
        # Router Agent
        router_tools = [self.route_task]
        self.agents["router"] = self.create_agent(
            "router_agent",
            """You are a task router. Your job is to analyze incoming tasks and route them to the appropriate specialist agent.
            Available agents:
            - data: For data processing, analysis, and visualization
            - file: For file operations
            - api: For API-related tasks
            
            Always route the task to the most appropriate agent based on the task description.""",
            router_tools
        )
    
    def create_agent(self, name: str, system_prompt: str, tools: List[Any]) -> AgentExecutor:
        """Create a specialized agent with its own memory and tools."""
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        agent = create_openai_functions_agent(llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True, memory=memory)
    
    @tool
    def route_task(self, task_description: str) -> str:
        """Route a task to the appropriate specialized agent.
        
        Args:
            task_description: Description of the task to be performed
            
        Returns:
            str: The name of the agent that should handle the task
        """
        # This is a simplified routing logic. In a real system, you might want to use
        # more sophisticated routing based on task content, agent capabilities, etc.
        if any(keyword in task_description.lower() for keyword in ["data", "analyze", "process", "visualize"]):
            return "data"
        elif any(keyword in task_description.lower() for keyword in ["file", "read", "write", "delete"]):
            return "file"
        elif any(keyword in task_description.lower() for keyword in ["api", "endpoint", "request", "response"]):
            return "api"
        else:
            return "data"  # Default to data agent if no clear match
    
    # Data Processing Tools
    @tool
    def process_data(self, data: str) -> str:
        """Process and clean data."""
        return f"Processed data: {data}"
    
    @tool
    def analyze_data(self, data: str) -> str:
        """Analyze data and generate insights."""
        return f"Analysis results for: {data}"
    
    @tool
    def visualize_data(self, data: str) -> str:
        """Create visualizations from data."""
        return f"Created visualization for: {data}"
    
    # File Management Tools
    @tool
    def read_file(self, file_path: str) -> str:
        """Read content from a file."""
        return f"Reading file: {file_path}"
    
    @tool
    def write_file(self, file_path: str, content: str) -> str:
        """Write content to a file."""
        return f"Writing to file: {file_path}"
    
    @tool
    def delete_file(self, file_path: str) -> str:
        """Delete a file."""
        return f"Deleting file: {file_path}"
    
    # API Management Tools
    @tool
    def call_api(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Make an API call."""
        return f"Calling API endpoint: {endpoint}"
    
    @tool
    def process_api_response(self, response: str) -> str:
        """Process API response data."""
        return f"Processing API response: {response}"
    
    @tool
    def handle_api_error(self, error: str) -> str:
        """Handle API errors."""
        return f"Handling API error: {error}"
    
    def handle_task(self, task_description: str) -> str:
        """Handle a task by routing it to the appropriate agent."""
        # First, use the router agent to determine which agent should handle the task
        router_response = self.agents["router"].invoke({"input": task_description})
        target_agent = router_response["output"]
        
        # Then, pass the task to the appropriate agent
        if target_agent in self.agents:
            response = self.agents[target_agent].invoke({"input": task_description})
            return response["output"]
        else:
            return f"Error: No agent found for task type: {target_agent}"

def main():
    # Initialize the agent router
    router = AgentRouter()
    
    # Example tasks
    tasks = [
        "Process and analyze the sales data from last quarter",
        "Read the configuration file and update the settings",
        "Call the weather API and process the response",
        "Create a visualization of the user engagement metrics"
    ]
    
    # Process each task
    for task in tasks:
        print(f"\nProcessing task: {task}")
        result = router.handle_task(task)
        print(f"Result: {result}")

if __name__ == "__main__":
    main() 