import imaplib
import email
import os
import requests
import time
from dotenv import load_dotenv
from email.utils import parsedate_to_datetime

load_dotenv()

EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
IMAP_SERVER = "imap.gmail.com"
API_ENDPOINT = "https://email-parser-clean.onrender.com/parse-email"

def fetch_and_process_unread():
    print("Connecting to inbox...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    mail.select("inbox")

    status, messages = mail.search(None, '(UNSEEN)')
    print("IMAP search status:", status)
    print("Messages found:", messages)

    email_ids = messages[0].split()

    if not email_ids:
        print("No unread emails found.")
        mail.logout()
        return

    for eid in email_ids:
        _, data = mail.fetch(eid, "(RFC822)")
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        email_date_raw = msg.get("Date")
        email_datetime = parsedate_to_datetime(email_date_raw)
        formatted_timestamp = email_datetime.strftime("%Y-%m-%d %H:%M:%S")

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")

        print("Sending to parser...\n---\n", body[:300], "\n---\n")
        response = requests.post(API_ENDPOINT, json={
            "email_text": body,
            "timestamp": formatted_timestamp
        })
        print("Sent email to parser:", response.status_code, response.text)

    mail.logout()

if __name__ == "__main__":
    while True:
        fetch_and_process_unread()
        print("Sleeping for 1 minutes...\n")
        time.sleep(60)
