import streamlit as st
import requests
import pandas as pd
import os
from io import BytesIO
import uuid
import psycopg2


BASE_API_URL = "https://flexapi.aidevlab.com"
FLOW_ID_DB="ca219bed-8041-4649-bf48-dd862064fc19"
FLOW_ID_RUN="f66aa5d8-fe7c-4674-8571-44f9f338ccc7"
ENDPOINT_DB = FLOW_ID_DB
ENDPOINT_RUN = FLOW_ID_RUN
API_KEY = "sk-NIdHHr50vHYaoekjq9c7I-XlOULm4W02BKErIIx0D28"

# Database connection parameters
db_params = {
    'host': 'pitch59-web-dev-api-db.cz3keviqyg78.us-east-1.rds.amazonaws.com',
    'port': '5432',
    'dbname': 'pitch59_db',
    'user': 'user_readonly',
    'password': 'eH!xTTK7Dnf5BusqAYNFLaz2x'
}

def fetch_businesses_data():
    """
    Connects to the database and fetches business data
    """
    try:
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()
        
        print("Fetching the last 500 rows from businesses table...")
        
        columns = [
            "business_id", "business_name", "business_type", "title", 
            "facebook_link", "linkedin_link", "instagram_link", "twitter_link", 
            "pinterest_link", "education_level", "email", "contact_number", 
            "website_link", "address", "state", "user_id", "military_service", 
            "elevator_pitch_script"
        ]
        
        columns_str = ", ".join(f"\"{col}\"" for col in columns)
        query = f"SELECT {columns_str} FROM \"businesses\" ORDER BY business_id DESC LIMIT 500;"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        all_data_string = ""
        emails = []
        
        for row in rows:
            row_data = ""
            for i, col in enumerate(columns):
                value = row[i] if row[i] is not None else ""
                if col == "email" and value:
                    emails.append(value)
                row_data += f"{col}: {value}, "
            
            if row_data.endswith(", "):
                row_data = row_data[:-2]
                
            row_str = row_data + "==end==\n"
            all_data_string += row_str
        
        cursor.close()
        connection.close()
        
        print(f"Successfully fetched {len(rows)} rows from businesses table")
        
        # Create a sample DataFrame for preview - convert to strings to avoid type issues
        preview_data = []
        if rows:
            # Take first 10 rows for preview
            for i in range(min(10, len(rows))):
                row_dict = {}
                for j, col in enumerate(columns):
                    # Convert all values to strings to avoid type conversion issues
                    row_dict[col] = str(rows[i][j]) if rows[i][j] is not None else ""
                preview_data.append(row_dict)
        
        return all_data_string, preview_data, emails
        
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None, None, None


def db_flow(all_data_string):
    """
    Sends a query to Langflow API using the database data and handles different prompts for each case.
    """
    print("db_flow")
    url = f"{BASE_API_URL}/api/v1/run/{ENDPOINT_DB}?stream=false"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }
    My_uuid=str(uuid.uuid4())
    
   
    
    
    tweaks = {
        "TextInput-8pioA": {"input_value": all_data_string},
        "Chroma-rza2k": {"allow_duplicates": False, "persist_directory": My_uuid},
    }

    payload = {
        "output_type": "chat",
        "input_type": "chat",
        "tweaks": tweaks
    }

    try:
        st.write("Please wait while database data is being processed.")
        response = requests.post(url, json=payload, headers=headers)
        print(response)
        if response.status_code == 200:
            print("Yes True DB")
            st.success("Data has been processed successfully")
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
        prompt = """ 
Role: You are an advanced AI assistant specializing in business referrals and service provider searches based on a user query. Your goal is to identify the top 3 most relevant matches, ensuring precision, clarity, and professionalism in your output.

Instructions:
1. - If no entries are found, do not generate anything yourself. I repeat, **don't generate anything**. Always get the result from the database (Chroma DB) and then process this data.

2. **Process Overview:**
   - **Step 1:** Analyze the provided business data from the Chroma DB. Extract and Rank the top Best 5 most relevant service providers based on the user’s query from the database, considering factors such as business name, expertise, services offered, and available data (e.g., website data, business pitch, Instagram page data).
   - **Step 2:** Narrow down this 5 entries with all the data (from website, Instagram page etc) to the top 3 businesses, ranking them based on their alignment with the email or instruction.

3. **Match Percentage Calculation:**
   The **Match Percentage** reflects how closely a service provider aligns with the user’s query, considering multiple factors:

   - **Keyword Relevance (From 0-15%)**: Evaluate how closely the query's keywords (e.g., “extreme sports,” “mountain biking,” “triathlon”) are reflected in the business's profile. Context matters, so don't just count keywords but assess their relevance in context. If the match is very weak with the keyword, assign a low match score, like 3% or 4%.
   - **Business Expertise (From 0-30%)**: Does the business provide services or products directly related to the query? For example, if the query is about extreme sports, the business’s expertise in outdoor activities or related fields should be weighed heavily.
   - **Personal Trait Relevance (From 0-25%)**: If the business or its leaders mention personal interests or traits that align with the query (e.g., passion for extreme sports), this increases the match score. Subjective queries like "fun" or "loves adventure" should also be reflected here.
   - **Behavioral/Engagement (From 0-10%)**: Does the business or individual share content, engage in activities, or have testimonials relating to the query’s theme (e.g., photos of rock climbing, participation in marathons)? Engagement with the query’s subject matter on social media or in reviews should be considered.
   - **Web/Social Media Data (From 0-10%)**: Check if the business or its leadership showcases relevant interests or activities related to the query on their website, blog, or social media. This may include posts, articles, or other forms of engagement that demonstrate alignment.
   - **Query Ambiguity Adjustment (From 0-10%)**: For subjective queries (e.g., “someone who loves extreme sports” or “someone who is fun”), apply a **penalty adjustment** to prevent overestimation. These types of queries should not score as highly as more objective ones, as they are inherently harder to measure.

   Note: The total match percentage should vary and depend on the actual data retrieved from the database. The percentage will not always be 80, 85, or 90, but should be more variable and based on the match data retrieved.

4. **Result Presentation:**
   For each of the top 3 businesses, include the following details:
   - **Person Name:** Name of the business owner or leader.
   - **Business Name:** Full name of the business or service provider, including key details about its offerings.
   - **Website Link:** Link to the business website (if available), or "No Link" with a list of services provided in keywords and bullet points.
   - **Services:** Specific Best all services (e.g., - service 1, - service 2, - service 3... and so on).
   - **Instagram Link:** Link to the Instagram profile (if available)
      - Brief Biography in one Line
      - Followers and Following
   - **Location:** Physical location of the business (city, state, country).
   - **Match Percentage:** A score (0-100%) calculated from each match category indicating the relevance of the business to the user’s query, ranked from highest to lowest.
   - **Business Overview:** A brief summary of the business, its services, and its areas of expertise.
   - **Justification:** A concise explanation of why the business is a good match and what makes it stand out, including details about its services, expertise, or personal traits that align with the query.

   Add line after each entry   

   ---

5. **Subjective Queries:** 
   - For subjective queries like "someone who loves extreme sports" or "someone who is fun," apply a more nuanced approach. These queries will have a lower maximum match percentage due to their inherent subjectivity. The match percentage should reflect both business expertise and personal traits but will be capped to avoid overestimating the match.

6. **Evaluation & Feedback:**
   - After presenting the top results, allow the user to provide feedback on the accuracy of the matches. This feedback should be used to continuously refine the matching criteria and improve the accuracy of the system.

Note: Use Chroma db tool to answer the query.

"""

    else:
        print("==(match)==hihihi")
        prompt = """ 

# Role & Objective:
You are an advanced AI assistant specializing in business referrals and service provider searches based on user queries. Your goal is to identify the **top 3 most relevant business matches** based on a given email address or query while ensuring **precision, clarity, and professionalism** in your output.

---

## 📌 Handling Email Queries:

### 🔹 **Case 1: Email Address Only**
- When a user provides **only an email address** (e.g., `xxxxxx@xxxx.com`), extract **business details** associated with that email using database information.
- Identify **5 external business matches** that provide **similar services or industry focus** but **are not part of the same company, parent brand, franchise, or business network**. External must.
- Businesses should be ranked based on **industry alignment, service offerings, and overall business approach**.

### 🔹 **Case 2: Email with Additional Instructions**
- When a user provides an **email address along with specific criteria** (e.g., "Find a company in the USA for `xxxxxx@xxxx.com`"), extract **business details** associated with the email.
- Identify 5 external businesses that **match the industry or business of provided email's** while also aligning with the specific **instruction (e.g., location, service type, expertise, etc.)**.
- Ensure the recommended businesses **are not part of the same company, brand, franchise, or network**.

---

## 🛠 **Step-by-Step Process for Business Matching:**

### **Step 1: Extract and Rank Relevant Business Data**
- **Use Chroma DB** to find the **top 5 most relevant businesses** based on the provided email's business detail and query details.
- **For Case 1:** Prioritize businesses based on **industry, service type, and business approach**.
- **For Case 2:** Consider the above **plus any specific user-provided criteria** (e.g., location, specialization, or any specific request).

### **Step 2: Finalize and Rank the Top 3 Businesses**
- Based on the collected information from Chroma DB and other available sources, **narrow down** the **top 5 businesses to the top 3**.
- Rank them **in descending order** based on how well they align with the email query or specified instructions.

---

## 🔍 **Dealing with Missing Business Information**
If **no detailed business information is available** for a given email:
1. **Check the company’s official website** and **public web/social media sources**.
2. Extract business details from these sources.
3. If **no business is found for this specific email**, **clearly mention this** in the response and instruct the user to provide a different email and do not generate anything further.
4. Do **not generate any additional assumptions or unrelated information**.

---

## 📊 **Match Percentage Calculation Criteria**

The **Match Percentage** reflects how closely a business aligns with the user’s query. It is calculated based on the following categories:
   - **Keyword Relevance (From 0-15%)**: Evaluate how closely the query's keywords (e.g., “extreme sports,” “mountain biking,” “triathlon”) are reflected in the business's profile. Context matters, so don't just count keywords but assess their relevance in context. If the match is very weak with the keyword, assign a low match score, like 3% or 4%.
   - **Business Expertise (From 0-30%)**: Does the business provide services or products directly related to the query? For example, if the query is about extreme sports, the business’s expertise in outdoor activities or related fields should be weighed heavily.
   - **Personal Trait Relevance (From 0-25%)**: If the business or its leaders mention personal interests or traits that align with the query (e.g., passion for extreme sports), this increases the match score. Subjective queries like "fun" or "loves adventure" should also be reflected here.
   - **Behavioral/Engagement (From 0-10%)**: Does the business or individual share content, engage in activities, or have testimonials relating to the query’s theme (e.g., photos of rock climbing, participation in marathons)? Engagement with the query’s subject matter on social media or in reviews should be considered.
   - **Web/Social Media Data (From 0-10%)**: Check if the business or its leadership showcases relevant interests or activities related to the query on their website, blog, or social media. This may include posts, articles, or other forms of engagement that demonstrate alignment.
   - **Query Ambiguity Adjustment (From 0-10%)**: For subjective queries (e.g., “someone who loves extreme sports” or “someone who is fun”), apply a **penalty adjustment** to prevent overestimation. These types of queries should not score as highly as more objective ones, as they are inherently harder to measure.
   
   Note: The total match percentage should vary and depend on the actual data retrieved from the database. The percentage will not always be 80, 85, or 90, but should be more variable and based on the match data retrieved.

---

## 🚫 **Important Exclusions & Guidelines**
- **❌ Avoid Recommending Businesses from the Same Parent Company or Franchise:**  
  If the provided email belongs to a business that is part of a **larger franchise or corporate group (e.g., EXIT Realty, Keller Williams, etc.)**, do **not include businesses from the same network**.
  
- **🔍 Prioritize Relevant Business Matches:**  
  Focus on **businesses with similar industries, complementary services, and comparable business models** (e.g., real estate firms, mortgage brokers, home staging services).

- **✅ Provide Only External Business Referrals:**  
  Ensure that **all suggested businesses are independent companies** and **not affiliated** with the business from the given email.

---

## 📑 **Final Results Format**
For each **top 3 business match**, provide:

### Result Presentation:
   For each of the top 3 businesses, include the following details:
   - **Person Name:** Name of the business owner or leader.
   - **Business Name:** Full name of the business or service provider, including key details about its offerings.
   - **Website Link:** Link to the business website (if available), or "No Link" with a list of services provided in keywords and bullet points.
   - **Services:** Specific Best all services (e.g., - service 1, - service 2, - service 3... and so on).
   - **Instagram Link:** Link to the Instagram profile (if available)
      - Brief Biography in one Line
      - Followers and Following
   - **Location:** Physical location of the business (city, state, country).
   - **Match Percentage:** A score (0-100%) calculated from each match category indicating the relevance of the business to the user’s query, ranked from highest to lowest.
   - **Business Overview:** A brief summary of the business, its services, and its areas of expertise.
   - **Justification:** A concise explanation of why the business is a good match and what makes it stand out, including details about its services, expertise, or personal traits that align with the query.

---

## ⚠️ **Key Takeaways**
✅ **If business details are missing, check the company’s website and social media** before concluding.  
✅ **Ensure businesses are independent and do not belong to the same corporate group.**  
✅ **Clearly mention if no business data is found and suggest an alternative email query.**  
✅ **Match businesses based on industry, complementary services, and business approach.**  

---

### 🎯 **Goal:**
Your mission is to deliver **highly relevant, professional, and independent business referrals** that align **precisely** with the user’s query.


"""

    tweaks = {
        "ChatInput-6ZCEt": {
            "input_value": query
        },
        # "ChatOutput-XkGc1": {"session_id": str(My_uuid)},
        "Chroma-qMdCm": {"allow_duplicates": False, "persist_directory": My_uuid},
        "Agent-PorIY": {"system_prompt": prompt,"session_id":My_uuid} 
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

if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.response = None
    st.session_state.preview_data = None
    st.session_state.all_data_string = None
    st.session_state.emails = None

if st.button("Load Database Data") and not st.session_state.data_loaded:
    try:
        with st.spinner("Connecting to database and retrieving data..."):
            st.session_state.all_data_string, st.session_state.preview_data, st.session_state.emails = fetch_businesses_data()
            
            if st.session_state.all_data_string is not None:
                st.session_state.response = db_flow(st.session_state.all_data_string)
                st.session_state.data_loaded = True
                st.success("Database data loaded successfully!")
            else:
                st.error("Failed to retrieve data from database.")
    except Exception as e:
        st.error(f"Error: {e}")

if st.session_state.data_loaded and st.session_state.preview_data:
    st.write("Preview of database data:")
    try:
        # Convert to DataFrame and ensure all columns are string type
        preview_df = pd.DataFrame(st.session_state.preview_data)
        # Convert all columns to string type
        for col in preview_df.columns:
            preview_df[col] = preview_df[col].astype(str)
        st.dataframe(preview_df)
    except Exception as e:
        st.error(f"Error displaying preview: {e}")
        # Fallback to displaying raw data
        st.json(st.session_state.preview_data[:3])

if st.session_state.data_loaded:
    profile_selected = st.checkbox("Select a Profile to Compare")

    if profile_selected:
        profile_email = st.selectbox("Select a profile:", st.session_state.emails if hasattr(st.session_state, 'emails') and st.session_state.emails else ["No emails available"])
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
    st.info("Please click on Load database button.")
