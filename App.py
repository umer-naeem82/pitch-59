import streamlit as st
import requests
import json
import pandas as pd
import os
from io import BytesIO

BASE_API_URL = "https://flex.aidevlab.com"
FLOW_ID = "8ecd8f19-cec8-4230-929f-04f68c78a38b"
ENDPOINT = FLOW_ID
API_KEY = "sk-NIdHHr50vHYaoekjq9c7I-XlOULm4W02BKErIIx0D28" 

def upload_file_to_langflow(file):
    """
    Uploads a CSV file to Langflow and returns the uploaded file path.
    """
    file_bytes = file.getvalue()  # Get bytes from file
    file_obj = BytesIO(file_bytes)  # Convert to a file-like object

    files = {"file": (file.name, file_obj)}
    url = f"{BASE_API_URL}/api/v1/upload/{ENDPOINT}"
    headers = {"x-api-key": API_KEY}

    try:
        response = requests.post(url, files=files, headers=headers)
        
        if response.status_code == 201:
            response_json = response.json()
            file_path = response_json.get("file_path")

            if file_path:
                st.success(f"File uploaded successfully!")
                return file_path
            else:
                st.error("Error: File uploaded, but no path returned.")
                return None
        else:
            st.error(f"File upload failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error uploading file: {e}")
        return None

def query_csv_agent(file_path, query):
    """
    Sends a query to Langflow API using the uploaded CSV file.
    """
    url = f"{BASE_API_URL}/api/v1/run/{ENDPOINT}?stream=false"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }

    tweaks = {
        "ChatInput-Sk8Ga": {"input_value": query},
        "File-dSAMa": {"path": file_path},  
        "CSVAgent-ji2No": {"path": file_path} 
    }

    payload = {
        "output_type": "chat",
        "input_type": "chat",
        "tweaks": tweaks
    }

    try:
        st.write("Sending query to API...")
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Request failed with status code {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": "An error occurred while connecting to the API", "details": str(e)}


st.set_page_config(page_title="CSV Query Agent", layout="wide")
st.title("Pitch59")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.write("Preview of uploaded file:")
        st.dataframe(df)
        st.write("Please wait File is Uploading to Server...")
        file_path = upload_file_to_langflow(uploaded_file)

        if file_path:

            query = st.text_input("Enter your query:", placeholder="What is the CSV about?")

            if st.button("Submit Query"):
                if query.strip():
                    response = query_csv_agent(file_path, query)

                    st.subheader("Response:")
                    if "error" in response:
                        st.error(response["error"])
                        st.write(response["details"])
                    else:
                        st.write(response["outputs"][0]["outputs"][0]["results"]["message"]["text"])
                else:
                    st.warning("⚠️ Please enter a query before submitting.")
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
st.sidebar.markdown("Pitch59")
st.sidebar.markdown("-----------------------")
st.sidebar.markdown("Your Pitch, Your Power!")
