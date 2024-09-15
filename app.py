import streamlit as st
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import requests
from mailjet_rest import Client

# Initialize Mailjet client
mailjet = Client(auth=(os.environ.get('MJ_APIKEY_PUBLIC'), os.environ.get('MJ_APIKEY_PRIVATE')), version='v3.1')

# Initialize Groq client
from groq import Groq
client = Groq(api_key=os.environ.get("CHATAPI"))

# Load Google Service Account credentials from environment variable
client_secret = os.environ.get("CLIENT_SECRET")

# Set background theme to black
st.set_page_config(page_title="EmailGenie", layout="wide")
st.markdown("""
    <style>
    body {
        background-color: #000;
        color: #fff;
    }
    </style>
""", unsafe_allow_html=True)

# Page title and image
st.title("EmailGenie: Cold Email Outreach powered by Llama 3.1 and Mailjet")
st.image("email_generator_image.png", width=100)  # Ensure this image is available

# User Profile Setup
st.subheader("Tell us about yourself")
name = st.text_input("Enter your name")
industry = st.selectbox("Select industry", ["Tech", "Finance", "Healthcare", "Marketing", "Other"])
target_audience = st.selectbox("Select target audience", ["Customers", "Investors", "Partners", "Talent", "Other"])
background = st.text_input("Tell about your background")
profile_type = st.radio("Select profile type", ["Personal", "Company"])

# Token input field
st.subheader("Select token amount")
token = st.slider("Token amount", min_value=100, max_value=1000, value=500)

# Connect Email Client and Preview
st.subheader("Connect your email client")
user_email = st.text_input("Enter your email address")

# Email Template Engine
st.subheader("Choose an email template")
template = st.selectbox("Select template", ["Sales Pitch", "Job Application", "Service Offer", "Networking", "Other"])

# Collect form data
form_data = {
    "Name": name,
    "Industry": industry,
    "Target Audience": target_audience,
    "Background": background,
    "Profile Type": profile_type,
    "Email": user_email,
    "Template": template,
    "Token": token,
}

# Google Sheets integration
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
try:
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(client_secret), scope)
    gc = gspread.authorize(credentials)
    spreadsheet_key = "1bxb9OvvEOdPLBcek5gvAy21oIUs2uZaFdIHDCv3kjM8"
    sheet = gc.open_by_key(spreadsheet_key).sheet1
    sheet.append_row(list(form_data.values()))
    google_sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_key}/edit"
except Exception as e:
    st.error(f"Error accessing Google Sheet: {e}")
    google_sheet_url = None

# Generate email using Groq API
prompt = f"Generate an email for {name} in {industry} targeting {target_audience} with background {background} and profile type {profile_type} using {template} template."
try:
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.1-8b-instant",  # Ensure this model name is correct
    )
    email_content = chat_completion.choices[0].message.content
except Exception as e:
    st.error(f"Error generating email: {e}")
    email_content = "Failed to generate email content."

# Display generated email content
st.subheader("Generated Email")
st.text_area("Email Content", value=email_content, height=300)

# Confirm data stored in Google Sheet
st.subheader("Data Stored in Google Sheet")
if google_sheet_url:
    st.markdown(f"Data has been successfully stored in the Google Sheet. You can view it [here]({google_sheet_url}).")
else:
    st.markdown("Data could not be stored in the Google Sheet.")

# Ask user if they want to send the email
st.subheader("Send Email")
send_email = st.radio("Do you want to send the email?", ["Yes", "No"])

if send_email == "Yes":
    recipient_email = st.text_input("Enter recipient's email address")

    if st.button("Send Email"):
        if recipient_email and email_content:
            try:
                data = {
                    'Messages': [
                        {
                            "From": {
                                "Email": user_email,
                                "Name": name
                            },
                            "To": [
                                {
                                    "Email": recipient_email
                                }
                            ],
                            "Subject": "Generated Email from EmailGenie",
                            "HTMLPart": email_content
                        }
                    ]
                }
                result = mailjet.send.create(data=data)
                
                if result.status_code == 200:
                    st.success("Email sent successfully!")
                else:
                    st.error(f"Failed to send email: {result.json()}")
            except Exception as e:
                st.error(f"Failed to send email: {e}")
        else:
            st.error("Recipient email or content is missing.")
