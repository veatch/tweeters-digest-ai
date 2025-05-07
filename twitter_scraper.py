import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import time
import requests
import random

# Try to load from .env file, but don't fail if it doesn't exist
load_dotenv(override=True)

# Common user agents for modern browsers
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]

def send_email(subject, message):
    """
    Send an email using Mailgun API
    """
    domain = os.getenv('MAILGUN_DOMAIN')
    api_key = os.getenv('MAILGUN_API_KEY')
    from_email = os.getenv('FROM_EMAIL')
    to_email = os.getenv('TO_EMAIL')

    # Debug: Print which variables are missing
    missing_vars = []
    if not domain: missing_vars.append('MAILGUN_DOMAIN')
    if not api_key: missing_vars.append('MAILGUN_API_KEY')
    if not from_email: missing_vars.append('FROM_EMAIL')
    if not to_email: missing_vars.append('TO_EMAIL')
    
    if missing_vars:
        print(f"Missing environment variables: {', '.join(missing_vars)}")
        return False

    response = requests.post(
        f"https://api.mailgun.net/v3/{domain}/messages",
        auth=("api", api_key),
        data={
            "from": from_email,
            "to": to_email,
            "subject": subject,
            "text": message
        }
    )

    if response.status_code == 200:
        print("Email sent successfully!")
        return True
    else:
        print(f"Failed to send email. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def login_to_twitter():
    with sync_playwright() as p:
        # Launch browser with more realistic settings
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials'
            ]
        )
        context = browser.new_context()
        page = context.new_page()

        try:
            # Navigate to Twitter login page
            print("Navigating to Twitter login page...")
            page.goto('https://twitter.com/login')
            
            # Wait for the login form to be visible
            print("Waiting for username input field...")
            page.wait_for_selector('input[autocomplete="username"]')
            
            # Enter username/email
            print("Entering username...")
            page.fill('input[autocomplete="username"]', os.getenv('TWITTER_USERNAME'))
            
            # Add a small delay to ensure the field is properly filled
            time.sleep(1)
            
            # Check if the Next button is visible and clickable
            print("Looking for Next button...")
            next_button = page.get_by_role("button", name="Next")
            if next_button.is_visible():
                print("Next button is visible, attempting to click...")
                next_button.click()
            else:
                print("Next button is not visible!")
                # Take a screenshot for debugging
                page.screenshot(path="debug_screenshot.png")
                print("Screenshot saved as debug_screenshot.png")
            
            # Wait for password field and enter password
            print("Waiting for password field...")
            page.wait_for_selector('input[type="password"]')
            page.fill('input[type="password"]', os.getenv('TWITTER_PASSWORD'))
            
            # Click login button
            print("Clicking login button...")
            login_button = page.get_by_role("button", name="Log in")
            if login_button.is_visible():
                login_button.click()
            page.click('div[role="button"]:has-text("Log in")')
            
            # Wait for successful login (wait for home timeline)
            print("Waiting for successful login...")
            page.wait_for_selector('div[data-testid="primaryColumn"]')
            
            print("Successfully logged in to Twitter!")
            
            # Keep the browser open for 30 seconds to verify login
            page.wait_for_timeout(30000)
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            # Take a screenshot on error
            try:
                page.screenshot(path="error_screenshot.png")
                print("Error screenshot saved as error_screenshot.png")
            except:
                print("Could not save error screenshot")
        
        finally:
            browser.close()

if __name__ == "__main__":
    # Check if environment variables are set
    if not os.getenv('TWITTER_USERNAME') or not os.getenv('TWITTER_PASSWORD'):
        print("Please set TWITTER_USERNAME and TWITTER_PASSWORD environment variables")
        exit(1)
    
    # Test email sending
    send_email("Hello from Twitter Digest", "This is a test email from the Twitter Digest application!")
    
    # disable scraping for now, seeing if email works through Github Actions
    #login_to_twitter() 