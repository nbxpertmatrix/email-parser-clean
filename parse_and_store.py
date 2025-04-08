import openai
import os
import re
import json
import requests
import random
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def parse_email_with_gpt(email_text):
    prompt = f"""
You are an expert information extractor. Read the email below and extract:

- parent_company_name (main company mentioned)
- parent_company_website (best guess if not stated)
- subsidiaries (a list of known business units, brands, or subsidiaries of the parent - include both name and website)
- expert_type (the kind of expert the sender is looking for: formers, customers, employees, etc.)

If there are no known subsidiaries, return an empty list for subsidiaries.

Respond in this exact JSON format:
{{
  "parent_company_name": "...",
  "parent_company_website": "...",
  "subsidiaries": [
    {{"name": "...", "website": "..."}}
  ],
  "expert_type": "..."
}}

Email:
\"\"\"{email_text}\"\"\"
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    content = response['choices'][0]['message']['content']
    json_match = re.search(r"\{.*\}", content, re.DOTALL)
    if not json_match:
        raise ValueError("No JSON found in GPT response.")

    return json.loads(json_match.group())

def write_to_airtable(data, timestamp=None):
    airtable_url = f"https://api.airtable.com/v0/{os.getenv('AIRTABLE_BASE_ID')}/{os.getenv('AIRTABLE_TABLE_NAME').replace(' ', '%20')}"
    headers = {
        "Authorization": f"Bearer {os.getenv('AIRTABLE_API_KEY')}",
        "Content-Type": "application/json"
    }

    assigned_agent = random.choice(["Yared", "Nati"])
    request_date = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    records = [{
        "fields": {
            "Company Name": data.get("parent_company_name"),
            "Website": data.get("parent_company_website"),
            "Expert Type": data.get("expert_type"),
            "Assigned To": assigned_agent,
            "Request Date": request_date,
            "Is Subsidiary": False
        }
    }]

    for sub in data.get("subsidiaries", []):
        records.append({
            "fields": {
                "Company Name": sub.get("name"),
                "Website": sub.get("website"),
                "Expert Type": data.get("expert_type"),
                "Assigned To": assigned_agent,
                "Request Date": request_date,
                "Is Subsidiary": True
            }
        })

    body = {"records": records}
    response = requests.post(airtable_url, headers=headers, json=body)
    if response.status_code != 200:
        raise Exception(f"Airtable error: {response.status_code} - {response.text}")
