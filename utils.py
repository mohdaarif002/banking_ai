import streamlit as st
import sounddevice as sd
import numpy as np
import wave
import os
import time
import whisper
# from langchain.prompts.prompt import PromptTemplate
from langchain.schema.runnable import RunnableMap
from langchain.schema.output_parser import StrOutputParser

from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq

import re

import mysql.connector
import global_variables



model = whisper.load_model("base")


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
    


def groq_api_call(user_text, user_mpin, groq_api_key):
    print('groq_api_call...........')
    # print('groq_api_key ',groq_api_key)
    llm = ChatGroq(model="gemma2-9b-it", groq_api_key=groq_api_key )

    prompt = PromptTemplate(
    input_variables=["customer_input","mpin"],
    template="""
                You are an intelligent SQL generation assistant for a banking system. Use the database schema below to generate SQL queries **only if the MPIN is correct**.

                ⚠️ IMPORTANT RULES:
                - Only use MPIN to identify or authenticate the user. Ignore any other user-provided details like name, email, or customer ID.
                - Never generate queries based on names, phone numbers, or email addresses.
                - If the MPIN is missing or invalid, respond with a polite message like "Please provide a valid MPIN to proceed."


                Database: `BankDB`

                Tables:

                1. `Customers`
                - `customer_id` (INT, Primary Key)
                - `first_name` (VARCHAR)
                - `last_name` (VARCHAR)
                - `dob` (DATE)
                - `phone_number` (VARCHAR, Unique)
                - `email` (VARCHAR, Unique)
                - `address` (TEXT)
                - `created_at` (TIMESTAMP)
                - `mpin` (VARCHAR,Unique)

                2. `Accounts`
                - `account_id` (INT, Primary Key)
                - `customer_id` (INT, Foreign Key referencing Customers.customer_id)
                - `account_type` (ENUM: 'Savings', 'Checking', 'Loan', 'Credit Card')
                - `balance` (DECIMAL)
                - `currency` (VARCHAR)
                - `status` (ENUM: 'Active', 'Inactive', 'Closed', 'Frozen')
                - `opened_at` (TIMESTAMP)

                3. `Transactions`
                - `transaction_id` (INT, Primary Key)
                - `account_id` (INT, Foreign Key referencing Accounts.account_id)
                - `transaction_type` (ENUM: 'Deposit', 'Withdrawal', 'Transfer', 'Payment')
                - `amount` (DECIMAL)
                - `currency` (VARCHAR)
                - `transaction_date` (TIMESTAMP)
                - `status` (ENUM: 'Pending', 'Completed', 'Failed', 'Reversed')

                ---

                The user's MPIN is: "{mpin}"

                If the MPIN is correct, proceed to generate a SQL query for the user input below. If the MPIN is incorrect or missing, respond with: "Access Denied: Invalid MPIN."


                Customer Input: "{customer_input}"

                Respond Only raw SQL without any formatting and no additional explanation.
                Do NOT include comments or notes. Just return the query.
                """
                )



    # Create a processing chain using RunnableMap
    chain = RunnableMap({
        "customer_input": lambda x: x["user_text"],
        "mpin":lambda x: x["user_mpin"],
    }) | prompt | llm | StrOutputParser()

    user_inputs = {
    "user_text": user_text,
    "user_mpin": user_mpin
    }

    print('user_inputs: ', user_inputs)
    response = chain.invoke(user_inputs)

   
    # response_2 = groq_api_call_2(user_text,response, groq_api_key)

    return response

def groq_api_call_2(user_text, response, groq_api_key):
    print('groq_api_call_2...........')
    # print('groq_api_key ',groq_api_key)
    llm = ChatGroq(model="gemma2-9b-it", groq_api_key=groq_api_key)

    prompt = PromptTemplate(
    input_variables=["user_text","response"],
    template="""
                You are an assistant for a conversational banking chatbot. Convert the MySQL query result into a clear and human-friendly answer for the user based on their question.

                Database: `BankDB`

                Tables:

                1. `Customers`
                - `customer_id` (INT, Primary Key)
                - `first_name` (VARCHAR)
                - `last_name` (VARCHAR)
                - `dob` (DATE)
                - `phone_number` (VARCHAR, Unique)
                - `email` (VARCHAR, Unique)
                - `address` (TEXT)
                - `created_at` (TIMESTAMP)
                - `mpin` (VARCHAR,Unique)

                2. `Accounts`
                - `account_id` (INT, Primary Key)
                - `customer_id` (INT, Foreign Key referencing Customers.customer_id)
                - `account_type` (ENUM: 'Savings', 'Checking', 'Loan', 'Credit Card')
                - `balance` (DECIMAL)
                - `currency` (VARCHAR)
                - `status` (ENUM: 'Active', 'Inactive', 'Closed', 'Frozen')
                - `opened_at` (TIMESTAMP)

                3. `Transactions`
                - `transaction_id` (INT, Primary Key)
                - `account_id` (INT, Foreign Key referencing Accounts.account_id)
                - `transaction_type` (ENUM: 'Deposit', 'Withdrawal', 'Transfer', 'Payment')
                - `amount` (DECIMAL)
                - `currency` (VARCHAR)
                - `transaction_date` (TIMESTAMP)
                - `status` (ENUM: 'Pending', 'Completed', 'Failed', 'Reversed')

                ---

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
    }) | prompt | llm | StrOutputParser()

    user_inputs = {
    "user_text": user_text,
    "response": response
    }

    print('user_inputs: ', user_inputs)
    response = chain.invoke(user_inputs)

    return response



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
