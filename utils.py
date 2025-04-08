import streamlit as st
import sounddevice as sd
import numpy as np
import wave
import os
import time
import whisper
# from langchain.prompts.prompt import PromptTemplate
from langchain.schema.runnable import RunnableMap, RunnableLambda
from langchain.schema.output_parser import StrOutputParser

from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq

import re

import mysql.connector
import global_variables
from langchain.sql_database import SQLDatabase
# from langchain.chains import SQLDatabaseChain
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")



model = whisper.load_model("base")
db = SQLDatabase.from_uri("mysql+pymysql://root:admin@localhost/BankDB")
llm = ChatGroq(model="gemma2-9b-it", groq_api_key=groq_api_key)
schema = db.get_table_info()


def record_audio(duration=5, sample_rate=44100):
    st.write(f"Preparing microphone...")
    
    # Generate and play a short silence/noise burst to activate the mic
    warmup_noise = np.zeros(int(1 * sample_rate), dtype=np.int16)  # 1 sec of silence
    sd.play(warmup_noise, samplerate=sample_rate)
    sd.wait()

    st.write(f"🔴 Speak now for {duration} seconds...")
    
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=2, dtype=np.int16)
    sd.wait()  # Wait for recording to finish
    return audio_data, sample_rate


# Function to save WAV file in a given directory
def save_wav(filename, data, sample_rate, SAVE_DIR):
    filepath = os.path.join(SAVE_DIR, filename)
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(2)  # Stereo
        wf.setsampwidth(2)  # 16-bit audio
        wf.setframerate(sample_rate)
        wf.writeframes(data.tobytes())
    return filepath  # Return the file path

# Function to transcribe audio
def transcribe_audio(filepath):
    result = model.transcribe(filepath)
    return result["text"]


def handle_intent(intent, entities):
    if intent == "check_balance":
        return check_balance(entities)
    elif intent == "transfer_funds":
        return transfer_funds(entities)
    elif intent == "get_statement":
        return get_statement(entities)
    else:
        return "Sorry, I didn’t understand your request."
    


def groq_api_call(user_text, user_mpin):
    print('groq_api_1..........')

    prompt = PromptTemplate(
    input_variables=["customer_input","mpin"],
    template="""
                You are an intelligent SQL generation assistant for a banking system. Use the database schema below to generate SQL queries **only if the MPIN is correct**.

                ⚠️ IMPORTANT RULES:
                - Only use MPIN to identify or authenticate the user. Ignore any other user-provided details like name, email, or customer ID.
                - Never generate queries based on names, phone numbers, or email addresses.
                - If the MPIN is missing or invalid, respond with a polite message like "Please provide a valid MPIN to proceed."


                Database Schema: '''{schema}'''

                The user's MPIN is: "{mpin}"

                If the MPIN is correct, proceed to generate a SQL query for the user input below. If the MPIN is incorrect or missing, respond with: "Access Denied: Invalid MPIN."


                Customer Input: '''{customer_input}'''

                Respond Only raw SQL without any formatting and no additional explanation.
                Only generate SQL queries using SELECT statements. Do not use DELETE, DROP, ALTER, or UPDATE.
                Do NOT include comments or notes. Just return the query.
                """
                )



    # Create a processing chain using RunnableMap
    chain = (
    RunnableMap({
        "customer_input": lambda x: x["user_text"],
        "mpin": lambda x: x["user_mpin"],
        "schema": lambda x:x["schema"]
    })
    | prompt             # uses the inputs to build the prompt
    | llm                # sends to Groq or GPT
    | StrOutputParser()  # extracts plain string (SQL)
    | RunnableLambda(run_sql_query)  # executes SQL and returns results
    )


    user_inputs = {
    "user_text": user_text,
    "user_mpin": user_mpin,
    "schema": schema
    }

    print('user_inputs: ', user_inputs)
    response = chain.invoke(user_inputs)
   
    return response


def run_sql_query(query: str) -> str:
    blocked_keywords = ["ALTER", "DROP", "DELETE", "TRUNCATE", "UPDATE"]
    if any(word in query.upper() for word in blocked_keywords):
        return "⚠️ Unsafe SQL query detected. Only SELECT queries are allowed."
    
    try:
        result = db.run(query)
        return result
    except SQLAlchemyError as e:
        return f"SQL Error: {str(e)}"    
    

def groq_api_call_2(user_text, response):
    print('groq_api_2...........')

    prompt = PromptTemplate(
    input_variables=["user_text","response"],
    template="""
                You are an assistant for a conversational banking chatbot. Convert the MySQL query result into a clear and human-friendly answer for the user based on their question.

                Database Schema: '''{schema}'''

                User Question: "{user_text}"

                MySQL Output: "{response}"

                Rules:
                - Do not mention SQL or databases.
                - Summarize the answer in clear, natural English.
                - Be concise but helpful.
                - If the result is empty or has no data, provide a polite message like "No records found" or something user-friendly.

                Now respond to the user:
              
                """
                )



    # Create a processing chain using RunnableMap
    chain = RunnableMap({
        "user_text": lambda x: x["user_text"],
        "response":lambda x: x["response"],
        "schema":lambda x: x["schema"]
    }) | prompt | llm | StrOutputParser()

    user_inputs = {
    "user_text": user_text,
    "response": response,
    "schema": schema 
    }

    print('user_inputs: ', user_inputs)
    response = chain.invoke(user_inputs)

    return response


def fetch_data_from_db_2(query):
    

    # Format: "mysql+pymysql://<username>:<password>@<host>/<database>"
    db = SQLDatabase.from_uri("mysql+pymysql://root:admin@localhost/BankDB")

    # Optional: Print available tables
    # st.text_area("db.get_table_names()", db.get_table_names())

    # Optional: Get schema for prompt use
    # st.text_area("db.get_table_info()", db.get_table_info())
    schema = db.get_table_info()

    try:
        # Ensure query does not contain restricted commands
        forbidden_keywords = ["DELETE", "DROP", "ALTER", "TRUNCATE"]
        if any(re.search(rf"\b{keyword}\b", query, re.IGNORECASE) for keyword in forbidden_keywords):

            print("Error: DELETE, DROP, ALTER, and TRUNCATE commands are not allowed.")
            return None
        
        # Establish connection
        conn = mysql.connector.connect(
            host="localhost",          
            user="root",    
            password="admin",  
            database="BankDB"          
        )

        cursor = conn.cursor()

        try:
            cursor.execute(query)
            results = cursor.fetchall()
            return results

        except mysql.connector.Error as e:
            print(f"Database error: {e}")
            return None  # Return None or handle as needed

        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

        finally:
            cursor.close()
            conn.close()

    except mysql.connector.Error as e:
        print(f"Connection error: {e}")
        return None  # Return None or an appropriate response

    except Exception as e:
        print(f"Unexpected error while connecting: {e}")
        return None    

def fetch_data_from_db(query):
    try:
        # Ensure query does not contain restricted commands
        forbidden_keywords = ["DELETE", "DROP", "ALTER", "TRUNCATE"]
        if any(re.search(rf"\b{keyword}\b", query, re.IGNORECASE) for keyword in forbidden_keywords):

            print("Error: DELETE, DROP, ALTER, and TRUNCATE commands are not allowed.")
            return None
        
        # Establish connection
        conn = mysql.connector.connect(
            host="localhost",          
            user="root",    
            password="admin",  
            database="BankDB"          
        )

        cursor = conn.cursor()

        try:
            cursor.execute(query)
            results = cursor.fetchall()
            return results

        except mysql.connector.Error as e:
            print(f"Database error: {e}")
            return None  # Return None or handle as needed

        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

        finally:
            cursor.close()
            conn.close()

    except mysql.connector.Error as e:
        print(f"Connection error: {e}")
        return None  # Return None or an appropriate response

    except Exception as e:
        print(f"Unexpected error while connecting: {e}")
        return None
