from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from typing import List, Optional
import os
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory

# Load environment variables
load_dotenv()

# Initialize the game board
board = [[" " for _ in range(3)] for _ in range(3)]

@tool
def make_move(row: int, col: int) -> str:
    """Make a move on the Tic Tac Toe board at the specified position.
    
    Args:
        row: The row number (0-2)
        col: The column number (0-2)
    
    Returns:
        str: A message indicating the move was made
    """
    if row < 0 or row > 2 or col < 0 or col > 2:
        return "Invalid move: Position out of bounds"
    
    if board[row][col] != " ":
        return "Invalid move: Position already taken"
    
    board[row][col] = "X"  # Agent plays as X
    print(f"Agent placed X at position ({row}, {col})")
    print_board()
    return f"Placed X at position ({row}, {col})"

def print_board():
    """Print the current state of the Tic Tac Toe board."""
    print("\nCurrent Board:")
    for row in board:
        print(" | ".join(row))
        print("-" * 9)

def check_winner() -> Optional[str]:
    """Check if there's a winner on the board.
    
    Returns:
        Optional[str]: The winning player ("X" or "O") or None if no winner
    """
    # Check rows
    for row in board:
        if row[0] == row[1] == row[2] != " ":
            return row[0]
    
    # Check columns
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] != " ":
            return board[0][col]
    
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != " ":
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != " ":
        return board[0][2]
    
    return None

def is_board_full() -> bool:
    """Check if the board is full.
    
    Returns:
        bool: True if the board is full, False otherwise
    """
    return all(cell != " " for row in board for cell in row)

def main():
    # Initialize the language model
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    
    # Define the tools
    tools = [make_move]
    
    # Create memory for chat history
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    # Create the prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Tic Tac Toe playing agent. You play as X.
        The board is a 3x3 grid with positions (0,0) to (2,2).
        Make moves by calling the make_move tool with row and column numbers.
        Try to win the game by getting three X's in a row, column, or diagonal.
        If you can't win, try to block the opponent from winning.
        If neither is possible, make the best strategic move."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # Create the agent
    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, memory=memory)
    
    print("Welcome to Tic Tac Toe! You are playing as O, and the AI is playing as X.")
    print("The board positions are numbered from (0,0) to (2,2).")
    print_board()
    
    while True:
        # Get human player's move
        while True:
            try:
                row = int(input("Enter row (0-2): "))
                col = int(input("Enter column (0-2): "))
                if 0 <= row <= 2 and 0 <= col <= 2 and board[row][col] == " ":
                    board[row][col] = "O"
                    break
                else:
                    print("Invalid move. Try again.")
            except ValueError:
                print("Please enter valid numbers.")
        
        print_board()
        
        # Check for winner after human move
        winner = check_winner()
        if winner:
            print(f"Player {winner} wins!")
            break
        if is_board_full():
            print("It's a tie!")
            break
        
        # Get AI's move
        print("\nAI's turn...")
        response = agent_executor.invoke({"input": "Make your move"})
        print(response["output"])
        
        # Check for winner after AI move
        winner = check_winner()
        if winner:
            print(f"Player {winner} wins!")
            break
        if is_board_full():
            print("It's a tie!")
            break

if __name__ == "__main__":
    main() 