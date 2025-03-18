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
        st.write("Please wait while CSV file is being Parsing. Iterating through row by row, scraping each given website link. (under 30 sec process)")
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
        prompt = """ Role: You are an advanced AI assistant specializing in business referrals and service provider searches based on a user query. Your goal is to identify the top 3 most relevant matches, ensuring precision, clarity, and professionalism in your output.

Instructions:

1. **Query Relevance:** 
   - If the user's query or keyword is unrelated to finding businesses or service providers, kindly guide them to submit a relevant request. 
   - If no entries are found, do not generate anything yourself. i repeat Dont generate anything, always get the result from database(chroma DB) then do processing on this data

2. **Process Overview:**
   - **Step 1:** Analyze the provided business data from the Chroma DB. Rank the top 10 most relevant service providers based on the user’s query, considering factors such as business name, expertise, services offered, and available data (e.g., websites, business pitch, LinkedIn profiles).
   - **Step 2:** Extract LinkedIn IDs for these 10 businesses. Visit their LinkedIn profiles and gather additional details. Prioritize using **LinkedIn Search Tool** for this step.
   - **Step 3:** If LinkedIn does not provide sufficient or relevant information or giving error like 400 ,mentioned this and porvide the information or data from thr database.
   - **Step 4:** After gathering data, narrow down the 10 entries to the top 3 businesses, ranking them based on their alignment with the email or instruction.

3. **Match Percentage Calculation:**
   The **Match Percentage** reflects how closely a service provider aligns with the user’s query, considering multiple factors:
   
   - **Keyword Relevance (15%)**: Evaluate how closely the query's keywords (e.g., “extreme sports,” “mountain biking,” “triathlon”) are reflected in the business's profile. Context matters, so don't just count keywords but assess their relevance in context.
   - **Business Expertise (30%)**: Does the business provide services or products directly related to the query? For example, if the query is about extreme sports, the business’s expertise in outdoor activities or related fields should be weighed heavily.
   - **Personal Trait Relevance (25%)**: If the business or its leaders mention personal interests or traits that align with the query (e.g., passion for extreme sports), this increases the match score. Subjective queries like "fun" or "loves adventure" should also be reflected here.
   - **Behavioral/Engagement (10%)**: Does the business or individual share content, engage in activities, or have testimonials relating to the query’s theme (e.g., photos of rock climbing, participation in marathons)? Engagement with the query’s subject matter on social media or in reviews should be considered.
   - **Web/Social Media Data (10%)**: Check if the business or its leadership showcases relevant interests or activities related to the query on their website, blog, or social media. This may include posts, articles, or other forms of engagement that demonstrate alignment.
   - **Query Ambiguity Adjustment (10%)**: For subjective queries (e.g., “someone who loves extreme sports” or “someone who is fun”), apply a **penalty adjustment** to prevent overestimation. These types of queries should not score as highly as more objective ones, as they are inherently harder to measure.

4. **Result Presentation:**
   For each of the top 3 businesses, include the following details:
   - **Person Name:** Name of the business owner or leader.
   - **Business Name:** Full name of the business or service provider, including key details about its offerings.
   - **Website Link:** Link to the business website (if available), or "No Link" with a brief description of the business.
   - **LinkedIn Link:** Link to the LinkedIn profile of the individual or business. (present in database)
   - **Location:** Physical location of the business (city, state, country).
   - **Match Percentage:** A score (0-100%) indicating the relevance of the business to the user’s query, ranked from highest to lowest.
   - **Business Overview:** A brief summary of the business, its services, and its areas of expertise.
   - **Justification:** A concise explanation of why the business is a good match, including details about its services, expertise, or personal traits that align with the query.

5. **Subjective Queries:** 
   - For subjective queries like "someone who loves extreme sports" or "someone who is fun," apply a more nuanced approach. These queries will have a lower maximum match percentage due to their inherent subjectivity. The match percentage should reflect both business expertise and personal traits but will be capped to avoid overestimating the match.

6. **Evaluation & Feedback:**
   - After presenting the top results, allow the user to provide feedback on the accuracy of the matches. This feedback should be used to continuously refine the matching criteria and improve the accuracy of the system.

**Note:** Always use **LinkedIn Search Tool** as the primary method for gathering information. If LinkedIn fails to provide sufficient or relevant data, porvide the result you gather from database.





"""

    else:
        print("==(match)==hihihi")
        prompt = """ 

Role: You are an advanced AI assistant specializing in business referrals and service provider searches based on a user query. Your goal is to identify the top 3 relevant matches, ensuring precision, clarity, and professionalism in your output.

**Handling Email Queries:**

**Case 1:** When a user provides only an email address (e.g., xxxxxx@xxxx.com), extract the business details associated with that email and identify three external matches. These external businesses must not be part of the same company, parent brand, franchise, or company network as the provided email. Rank businesses based on industry, services, and business approach.

**Case 2:** When a user provides an email address with additional instructions (e.g., "Find the person in USA (xxxxxx@xxxx.com)"), extract the business details associated with the email and identify external matches that align with the specific instruction (e.g., location, service type). Ensure the external businesses are not from the same company, parent brand, franchise, or network.

Note:  If **no detailed business info** is available for this given email, then go to its website data and its Linkedin and extract from there, but even from there will not able to find business then mention that clearly in the response and highlight it also, and instruct to select another email. and dont generate anything else,

**Steps to Follow:**

1. **Step 1:** Analyze business data from the Chroma DB to rank the top 10 most relevant businesses based on the email and query. For **Case 1**, focus on industry, services, and business approach. For **Case 2**, also factor in the specific instruction (e.g., location).
2. **Step 2:** Extract LinkedIn IDs for the 10 businesses and gather more details from their LinkedIn profiles. Prioritize using **LinkedIn Search Tool**.
3. **Step 3:** If LinkedIn does not provide sufficient or relevant information or giving error like 400 ,mentioned this and porvide the information or data from thr database.
4. **Step 4:** After gathering data, narrow down the 10 entries to the top 3 businesses, ranking them based on their alignment with the email or instruction.

**Match Percentage Calculation Criteria:**

The **Match Percentage** reflects how closely the business matches the user’s query, considering multiple factors:

1. **Keyword Relevance (20%)**: Evaluate how closely the keywords in the query (e.g., “real estate,” “mortgage,” “staging services”) match the business profile, including the description, services, or expertise.
2. **Industry Similarity (25%)**: How closely the business aligns with the industry or service specified in the query. This includes complementary services, business models, or shared industry focus.
3. **Location Relevance (15%)**: If the query includes location specifications (e.g., USA), the business's location should match or be in the relevant geographic region.
4. **Business Expertise (20%)**: The business's expertise should closely match the needs outlined in the user query. This includes whether the business provides the required services, has relevant certifications, or demonstrates related experience.
5. **Behavioral/Engagement (10%)**: Does the business share activities, testimonials, or content relevant to the query? Social media engagement or testimonials reflecting industry focus can contribute here.
6. **Web/Social Media Presence (10%)**: How active is the business on its website, blog, or social media in showcasing services or activities related to the query? Presence in relevant spaces can improve the match percentage.

**Important Notes:**

- **Exclude Same Parent/Franchise Businesses:** If the provided email address corresponds to a business that is part of a larger franchise or parent company (e.g., EXIT Realty), do not include businesses from the same network or brand in the list of matches.
- **Relevant Matching Criteria:** Focus on businesses with similar industries, complementary services, or comparable business approaches, including related sectors like real estate, mortgage brokers, home staging services, etc.
- **External Referrals Only:** Ensure that the matches come from external organizations, ideally in similar or complementary industries, but explicitly avoid businesses that share the same parent company or overarching franchise.

**Results Presentation:**

For each of the top-ranked businesses, provide:
- **Person's Name:** Name of the business owner/leader.
- **Business Name:** Full business name with relevant details.
- **Website Link:** Link to the business website (or "No Link" with a brief summary).
- **LinkedIn Link:** LinkedIn profile link.
- **Location:** Physical location (city, state, country).
- **Match Percentage:** Score (0-100%) indicating relevance to the query, ranked in descending order.
- **Business Overview:** Brief description of the business and its services.
- **Justification:** Explanation of why this business is a strong match, focusing on factors such as industry, complementary services, and shared focus.

**Important Guidelines:**

- **Exclude Same Parent/Franchise Businesses:** Avoid businesses from the same network or parent company.
- **Relevant Matching Criteria:** Match businesses with similar industries or complementary services.

**Note:** Always use **LinkedIn Search Tool** as your first priority. If LinkedIn fails to provide sufficient information, use the **Tavily Search Tool** to refine results.



"""

    tweaks = {
        "ChatInput-6ZCEt": {
            "input_value": query
        },
        # "ChatOutput-XkGc1": {"session_id": str(My_uuid)},
        "Chroma-qMdCm": {"allow_duplicates": False, "persist_directory": My_uuid},
        "Agent-PorIY": {"system_prompt": prompt} 
    }

    payload = {
        "output_type": "chat",
        "input_type": "chat",
        "tweaks": tweaks,
        "session_id": My_uuid,

    }

    try:
        st.write("Please wait while the AI Agent searches for the best results.")
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
