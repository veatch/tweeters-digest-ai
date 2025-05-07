import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

def login_to_twitter():
    with sync_playwright() as p:
        # Launch browser (using Chromium as it's the most stable)
        browser = p.chromium.launch(
            headless=True,
            # Replace above with lines below to debug locally
            #headless=False,
            #devtools=True  # Enable DevTools
        )
        # Also, you can uncomment line below to enable Playwright Inspector,
        # which can help with identifying the selectors for elements on the page
        # page.pause()
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
    
    login_to_twitter() 