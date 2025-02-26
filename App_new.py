import streamlit as st
import requests
import pandas as pd
import os
from io import BytesIO
import uuid

BASE_API_URL = "https://flex.aidevlab.com"
FLOW_ID = "bd5b90b3-d1a9-4439-bdd6-9022e1c6ce38"
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
                print(file_path)
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

def query_csv_agent(file_path, query, prompt_type):
    """
    Sends a query to Langflow API using the uploaded CSV file and handles different prompts for each case.
    """
    url = f"{BASE_API_URL}/api/v1/run/{ENDPOINT}?stream=false"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }

    # Define prompts
    if prompt_type == "keyword":
        prompt = {
            "template": """Role: You are an advanced AI assistant specializing in business referrals and service provider search based on a user-provided query. Your goal is to efficiently analyze business profiles and identify the top three matches, ensuring precision, clarity, and professionalism in your output.

Instructions:

If the users query or keyword is unrelated to finding businesses or professionals entries, politely guide them toward submitting a relevant request. If the query does not find any entry, do not generate anything from yourself.
Evaluate the provided business data and rank the top three most relevant service providers based on the query.
If the user provides only keywords (e.g., "Healthcare insurance," "Finance manager", or even single word like healthcare, health etc, or may be long sentence or question), extract relevant unique entries from the database or file content and list them in the same structured format.
Present the results in a structured, easy-to-read format.
For each top-ranked business or professional, include:

- Person name: who owns or leads the business.
- Business Name: Full name of the business or service provider and some of its details.
- Match Percentage: A score (0-100%) reflecting how well the business aligns with the query. Rank them in percentage order (Higher to Lower).
- Business Overview: A brief yet informative summary of the business, its key services, and expertise.
- Justification: A concise explanation of why the business was ranked, highlighting specific services, skills, or credentials that contribute to the match percentage.

Input Data:

Query: {question}
Business Database: {context}"""
        }
    else:
        # Retrieve profile details from the DataFrame if it's a profile comparison
        profile_data = df[df['referralEmail'] == profile_email].iloc[0]  # Retrieve details based on email
        # profile_name = profile_data['name']
        # profile_experience = profile_data['experience']  # Adjust these based on your CSV columns
        # profile_skills = profile_data['skills']  # Adjust these based on your CSV columns
        # profile_hobbies = profile_data['hobbies']  # Adjust these based on your CSV columns

        prompt = {
            "template": """ If the users query is an email address associated with any entry in the csv, then firstly find its busniness name. and then from this busniness name e.g (Healthcare or finance etc) find Best Three relevant matches from all the entries and List them.
         Do not generate anything beyond the matches.

For each of the top-ranked businesses or professionals, include the following details:

- **Person's Name**: The name of the individual who owns or leads the business.
- **Business Name**: The full name of the business or service provider, along with relevant details.
- **Match Percentage**: A score ranging from 0 to 100% that reflects how closely the business matches the provided query (the business associated with the given email). Rank the businesses in descending order of their match percentage.
- **Business Overview**: A brief and informative summary of the business, including its key services and areas of expertise.
- **Justification**: A concise explanation of why each business was ranked, highlighting specific services, skills, or credentials that contributed to its match percentage.

**Query**: {question}

**Business Database**: {context}  
(Ensure that dont generate anything from yourself. if you can't able to find all three then just list that are found and leave note in the end)

            """
        }

    tweaks = {
        "ChatInput-vngYL": {
            "input_value": query,  # Input query or profile name
            # "text": query,  # Text field for ChatInput (required)
            # "sender": "User",  # Sender of the query
            # "sender_name": "User",  # Sender name (required)
        },
        "File-AwXub": {"path": file_path},
        "Chroma-Zzwzr": {"allow_duplicates": False, "persist_directory": str(uuid.uuid4())},
        "Prompt-HORny": prompt  # Use the updated prompt
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

st.set_page_config(page_title="pitch-59", layout="wide")
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
            profile_selected = st.checkbox("Select a Profile to Compare")

            if profile_selected:
                profile_email = st.selectbox("Select a profile:", df['referralEmail'].tolist())  # Adjust based on your CSV column
                st.text_input("Query", "This field is disabled as you're comparing a specific profile.", disabled=True)

                context = "Provide relevant context about this profile and comparison, if needed."  # Add some context here.

                if st.button("Match"):
                    if profile_email:
                        response = query_csv_agent(file_path, profile_email,prompt_type="COMPARE")
                        print("response", response)

                        st.subheader("Top 3 Matching Profiles:")

                        if "error" in response:
                            print("error running")
                            st.error(response["error"])
                            st.write(response["details"])
                        else:
                            matches = response.get("outputs", [])[0].get("outputs", [])[0].get("results", {}).get("message", {}).get("text", "")
                            st.write(matches)
                    else:
                        st.warning("⚠️ Please select a profile before submitting.")
            else:
                query = st.text_input("Enter your query:", placeholder="Search for attributes, experience, hobbies, etc.")
                
                if st.button("Submit Query"):
                    if query.strip():
                        response = query_csv_agent(file_path, query, prompt_type="keyword")

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

st.sidebar.markdown("")
st.sidebar.markdown("-----------------------")
st.sidebar.markdown("")
