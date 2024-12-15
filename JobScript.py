from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from datetime import datetime
import os
from twilio.rest import Client

# Change file permissions for chromedriver (necessary on EC2)
os.chmod('/home/ec2-user/chromedriver', 0o755)

# Set up the ChromeDriver service on AWS EC2 instance
service = Service('/home/ec2-user/chromedriver')

# Set Chrome options for headless browsing (no GUI)
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Set location for Chrome in your EC2 instance
chrome_options.binary_location = "/usr/bin/google-chrome"

# Amazon job URL (make sure this is correct and updated)
job_url = "https://hiring.amazon.com/jobDetail/en-US/Amazon-Sortation-Center-Warehouse-Associate/Woodbury/JOB-US-0000005590"

# Twilio credentials (use environment variables for security)
account_sid = os.environ.get("TWILIO_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
messaging_service_sid = os.environ.get("TWILIO_MSID")
recipient_number = "+1234567891"  # Replace with your phone number

def check_job_status():
    """
    Function to check the status of the job by visiting the Amazon job page.
    """
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(job_url)

        # Wait until the banner with job status appears
        banner = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-test-component="MessageBannerContent"]'))
        )
        status = banner.text.strip()
        return status
    except Exception as e:
        return "Error: Unable to check job status."
    finally:
        driver.quit()

def send_sms_notification(message):
    """
    Function to send an SMS notification using Twilio's API.
    """
    client = Client(account_sid, auth_token)
    try:
        message = client.messages.create(
            to=recipient_number,
            messaging_service_sid=messaging_service_sid,
            body=message
        )
    except Exception as e:
        print(f"Error sending SMS: {e}")  

# Variables to store the last status and whether it's the first run
last_status = None
first_run = True

while True:
    now = datetime.now()

    # Check the current job status
    status = check_job_status()

    # Send an initial message on the first run
    if first_run:
        send_sms_notification(f"Initial status check:\n\n{status}")
        first_run = False

    # Send an SMS if the status has changed or it's the start of a new hour
    elif status != last_status or now.minute == 0:
        message = f"Job status update:\n\n{status}"
        send_sms_notification(message)

    # Update the last status for the next loop
    last_status = status

    sleep(600)  # Sleep for 10 minutes before checking again
