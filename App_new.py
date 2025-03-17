import streamlit as st
import requests
import pandas as pd
import os
from io import BytesIO
import uuid




BASE_API_URL = "https://flex.aidevlab.com"
FLOW_ID_DB="82f62119-9a91-42be-be2b-6b7422d3a104"
FLOW_ID_RUN="f66aa5d8-fe7c-4674-8571-44f9f338ccc7"
ENDPOINT_DB = FLOW_ID_DB
ENDPOINT_RUN = FLOW_ID_RUN
API_KEY = "sk-NIdHHr50vHYaoekjq9c7I-XlOULm4W02BKErIIx0D28"

def upload_file_to_langflow(file):
    """
    Uploads a CSV file to Langflow and returns the uploaded file path.
    """
    print("upload")
    file_bytes = file.getvalue() 
    file_obj = BytesIO(file_bytes)  

    files = {"file": (file.name, file_obj)}
    url = f"{BASE_API_URL}/api/v1/upload/{ENDPOINT_DB}"
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


def db_flow(file_path):
    """
    Sends a query to Langflow API using the uploaded CSV file and handles different prompts for each case.
    """
    print("db_flow")
    url = f"{BASE_API_URL}/api/v1/run/{ENDPOINT_DB}?stream=false"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }
    My_uuid=str(uuid.uuid4())
    tweaks = {
        "File-TDfyH": {"path": file_path},
        "Chroma-ZF86p": {"allow_duplicates": False, "persist_directory": My_uuid},
    }

    payload = {
        "output_type": "chat",
        "input_type": "chat",
        "tweaks": tweaks
    }

    try:
        st.write("Please wait while CSV file is being Parsing. Iterating through row by row, scraping each given website link. (under 2 min process)")
        response = requests.post(url, json=payload, headers=headers)
        print(response)
        if response.status_code == 200:
            print("Yes True DB")
            st.success("File has been Parsed Successfully")
            temp_json=response.json()
            temp_json["UUID"]=My_uuid
            print(temp_json)
            return temp_json
        else:
            print("No DB")
            st.error(f"Error From Server side.{response.status_code}")
            return {"error": f"Request failed with status code {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": "An error occurred while connecting to the API", "details": str(e)}



def run_flow(query,My_uuid,prompt_type):
    """
    Sends a query to Langflow API using the uploaded CSV file and handles different prompts for each case.
    """
    print("run_flow")
    url = f"{BASE_API_URL}/api/v1/run/{ENDPOINT_RUN}?stream=false"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }

    if prompt_type == "keyword":
        print("==(keyword)==")
        prompt = """Role: You are an advanced AI assistant specializing in business referrals and service provider searches based on a user-provided query. Your goal is to efficiently analyze business profiles and identify the top three matches, ensuring precision, clarity, and professionalism in your output.

Instructions:

1. If the user's query or keyword is unrelated to finding businesses or professional entries, kindly guide them to submit a relevant request. If the query does not find any entries, do not generate anything yourself.

2. **First step:** Evaluate the provided business data from the Chroma DB and rank the top 10 most relevant service providers based on the query. These 10 entries should be the most relevant to the query, considering all available data such as business names, expertise, services, etc.

3. **Second step:** Once the top 10 entries have been identified, extract the LinkedIn IDs for these 10 businesses. Go to the LinkedIn profiles of these 10 service providers and gather more information from their profiles.

4. **Third step:** If LinkedIn does not provide sufficient or relevant information, proceed to use the **Tavily Search Tool** for additional data on those 10 entries. 

5. **Final step:** After gathering data from LinkedIn or Tavily Search (if needed), narrow down the 10 entries to the top 3 businesses. The top 3 should be the most relevant based on the user query, business expertise, available data, and profile information.

6. If the user provides only keywords (e.g., "Healthcare insurance," "Finance manager," or even single words like healthcare, health, etc., or a long sentence or question), extract relevant unique entries from the database or file content and list them in the same structured format. Consider all available data (websites, business pitch, etc.) to ensure an accurate listing. If a business doesn't have a website, it doesn't necessarily mean it is of lower value—evaluate other attributes.

7. **First priority** should be to use the **LinkedIn Search Tool**. If LinkedIn cannot provide sufficient information, use the **Tavily Search Tool** to gather more data.
Note: - **If you cant find then just tell you cant find any. but dont generate any wrong information.

8. Present the results in a structured, easy-to-read format. For each top-ranked business or professional, include the following details:

- **Person Name:** Name of the person who owns or leads the business.
- **Business Name:** Full name of the business or service provider, along with key details.
- **Website Link:** Website link of the business if present. If no link is available, state "No Link" and provide a brief but relevant summary of the business based on available data.
- **LinkedIn Link:** LinkedIn profile link of the person or business.
- **Location:** Physical location of the business (city, state, country).
- **Match Percentage:** A score (0-100%) reflecting how well the business aligns with the query. Rank the businesses in order of percentage (highest to lowest).
- **Business Overview:** A concise yet informative summary of the business, its key services, and expertise.
- **Justification:** A brief explanation of why the business was ranked in the given position, highlighting specific services, skills, or credentials that contribute to the match percentage.

Note: Always use the **LinkedIn Search Tool** as your first priority. If LinkedIn fails to provide the necessary information, use the **Tavily Search Tool** to gather additional data and refine your results.
"""

    else:
        print("==(match)==")
        prompt = """ 
Role: You are an advanced AI assistant specializing in business referrals and service provider searches based on a user-provided query. Your goal is to efficiently analyze business profiles and identify the top three matches, ensuring precision, clarity, and professionalism in your output.
There are two cases to handle when a user provides an email address:

**Case 1:**
When a user provides only an email address (e.g., xxxxxx@xxxx.com), extract the business details associated with that email and identify the three best external matches. These external businesses must not be part of the same company, parent brand, franchise, or company network as the provided email. Rank the businesses based on the following factors: similarity in industry, services, attributes, and overall business approach.

**Case 2:**
When a user provides an email address with additional instructions (e.g., "Find the person in USA (xxxxxx@xxxx.com)"), extract the business details of the person associated with the email and identify three external matches that align with the specific instruction provided (e.g., location, service type, etc.). Ensure these external businesses are not part of the same company, parent brand, franchise, or network as the given email address. Rank these businesses based on how closely they align with both the person's business and the specific instructions given.

**Important Steps:**

1. **First step:** Evaluate the provided business data from the Chroma DB and rank the top 10 most relevant businesses based on the email address and query. For **Case 1**, this would mean extracting businesses similar in industry, services, and approach. For **Case 2**, you will also factor in the specific instruction provided (such as location, service type, etc.).
2. **Second step:** Once the top 10 entries have been identified, extract the LinkedIn IDs for these 10 businesses. Go to the LinkedIn profiles of these 10 businesses and gather more information from their profiles.
3. **Third step:** If LinkedIn does not provide sufficient or relevant information, proceed to use the **Tavily Search Tool** for additional data on those 10 entries.
4. **Final step:** After gathering data from LinkedIn or Tavily Search (if needed), narrow down the 10 entries to the top 3 businesses that best match the email address or the provided instruction. Rank these businesses based on how closely they align with the industry, services, location, and other criteria specified in the query.

**Important Notes:**
- **Exclude Businesses from the Same Parent Brand/Franchise:** If the provided email address corresponds to a business that is part of a larger franchise or parent company (e.g., EXIT Realty), do not include businesses from the same network or brand in the list of matches. These businesses may share too many common elements.
- **Relevant Matching Criteria:** Focus on businesses that have similar industries, complementary services, or a comparable business approach. This could include related industries such as real estate agencies, mortgage brokers, home staging services, etc.
- **External Referrals Only:** Ensure that the matches come from external organizations, ideally in similar or complementary industries, but explicitly avoid businesses that share the same parent company or overarching franchise.
- **If you cant find then just tell you cant find any. but dont generate any wrong information.
**Results Presentation:**
For each of the top-ranked businesses (if any), provide the following details:

- **Person's Name:** The name of the individual who owns or leads the business.
- **Business Name:** The full name of the business, including any relevant details.
- **Website Link:** Website link of the business if present. If no link is available, state "No Link" and provide a brief but relevant summary of the business based on available data.
- **LinkedIn Link:** LinkedIn profile link of the person or business.
- **Location:** The physical location of the business (city, state, country).
- **Match Percentage:** A score between 0-100% indicating how closely the business matches the provided query. Rank the businesses in descending order of match percentage.
- **Business Overview:** A brief description of the business, including key services, areas of expertise, and industry focus.
- **Justification:** A concise explanation of why this business is a strong match. The justification should focus on factors such as similar work, complementary services, or shared industry focus.

**Important Guidelines:**
- **Exclude Businesses from the Same Parent Brand/Franchise:** If the provided email address corresponds to a business that is part of a larger franchise or parent company (e.g., EXIT Realty), do not include businesses from the same network or brand in the list of matches. These businesses may share too many common elements.
- **Relevant Matching Criteria:** Focus on businesses that have similar industries, complementary services, or a comparable business approach. This could include related industries such as real estate agencies, mortgage brokers, home staging services, etc.
- **External Referrals Only:** Ensure that the matches come from external organizations, ideally in similar or complementary industries, but explicitly avoid businesses that share the same parent company or overarching franchise.

**Note:** Always use the **LinkedIn Search Tool** as your first priority. If LinkedIn fails to provide the necessary information, use the **Tavily Search Tool** to gather additional data and refine your results.
"""

    tweaks = {
        "ChatInput-6ZCEt": {
            "input_value": query,  
        },
        "Chroma-qMdCm": {"allow_duplicates": False, "persist_directory": My_uuid},
        "Agent-PorIY": {"system_prompt":prompt} 
    }

    payload = {
        "output_type": "chat",
        "input_type": "chat",
        "tweaks": tweaks
    }

    try:
        st.write("Please wait! Agent is searching from database, LinkedIn, websites and Intenet for Better Result...")
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Request failed with status code {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": "An error occurred while connecting to the API", "details": str(e)}







st.set_page_config(page_title="pitch-59", layout="wide")
st.title("Pitch59")

if 'file_uploaded' not in st.session_state:
    st.session_state.file_uploaded = False
    st.session_state.file_path = None
    st.session_state.response = None
    st.session_state.df = None
    st.session_state.csv_displayed = False 

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None and not st.session_state.file_uploaded:
    try:
        st.session_state.df = pd.read_csv(uploaded_file)
        st.write("Please wait, File is Uploading to Server...")
        
        st.session_state.file_path = upload_file_to_langflow(uploaded_file)
        st.session_state.response = db_flow(st.session_state.file_path)
        
        st.session_state.file_uploaded = True
        st.session_state.csv_displayed = True 

        
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")

if st.session_state.file_uploaded and st.session_state.csv_displayed:
    st.write("Preview of uploaded file:")
    st.dataframe(st.session_state.df)

if st.session_state.file_uploaded:
    profile_selected = st.checkbox("Select a Profile to Compare")

    if profile_selected:
        profile_email = st.selectbox("Select a profile:", st.session_state.df['Email'].dropna().tolist())
        query = st.text_input("Enter your query:", placeholder="Search for specific Requirement for given Email. If not Left Blank")

        if st.button("Match"):
            if profile_email:
                if query:
                    Temp = f"{query} ({profile_email})"
                    print("=======",Temp)
                    response = run_flow(Temp, st.session_state.response["UUID"], prompt_type="COMPARE")
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
                    print("=======",profile_email)
                    response = run_flow(profile_email, st.session_state.response["UUID"], prompt_type="COMPARE")
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
                print("=======",query)
                response = run_flow(query, st.session_state.response["UUID"], prompt_type="keyword")

                st.subheader("Response:")
                if "error" in response:
                    st.error(response["error"])
                    st.write(response["details"])
                else:
                    st.write(response["outputs"][0]["outputs"][0]["results"]["message"]["text"])
            else:
                st.warning("⚠️ Please enter a query before submitting.")

else:
    st.info("Please upload a CSV file to begin.")
