import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import time
import requests
import random
from datetime import datetime

DEBUG_MODE = False

# Enable Playwright Inspector when in debug mode
# Note that you may need to click the play button in the inspector to start the session
if DEBUG_MODE:
    os.environ['PWDEBUG'] = '1'

# Try to load from .env file, but don't fail if it doesn't exist
load_dotenv(override=True)

# Common user agents for modern browsers
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]

def send_email(subject, tweets):
    """
    Send an email using Mailgun API with formatted tweet content
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

    # Format tweets into a nice email message
    message = "Here are the latest tweets from @veatch:\n\n"
    for tweet in tweets:
        message += f"Tweet from {tweet['date']}:\n"
        message += f"{tweet['text']}\n"
        message += f"Likes: {tweet['likes']} | Retweets: {tweet['retweets']}\n"
        message += "-" * 50 + "\n\n"

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

def scrape_tweets(page, username="veatch", num_tweets=5):
    """
    Scrape tweets from a specific user
    """
    print(f"Navigating to @{username}'s profile...")
    page.goto(f'https://twitter.com/{username}')
    time.sleep(3)  # Wait for page to load

    tweets = []
    tweet_elements = page.query_selector_all('article[data-testid="tweet"]')
    
    for tweet in tweet_elements[:num_tweets]:
        try:
            # Get tweet text
            text_element = tweet.query_selector('div[data-testid="tweetText"]')
            text = text_element.inner_text() if text_element else "No text content"

            # Get engagement metrics
            metrics = tweet.query_selector_all('div[data-testid="reply"] span, div[data-testid="retweet"] span, div[data-testid="like"] span')
            likes = metrics[2].inner_text() if len(metrics) > 2 else "0"
            retweets = metrics[1].inner_text() if len(metrics) > 1 else "0"

            # Get date
            date_element = tweet.query_selector('time')
            date = date_element.get_attribute('datetime') if date_element else datetime.now().isoformat()

            tweets.append({
                'text': text,
                'likes': likes,
                'retweets': retweets,
                'date': date
            })
        except Exception as e:
            print(f"Error scraping tweet: {str(e)}")
            continue

    return tweets

def login_to_twitter():
    with sync_playwright() as p:
        # Launch browser with more realistic settings
        browser = p.chromium.launch(
            headless=not DEBUG_MODE,
            devtools=DEBUG_MODE,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials'
            ]
        )
        
        # Create a more realistic browser context
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=random.choice(USER_AGENTS),
            locale='en-US',
            timezone_id='America/New_York',
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},  # New York City
            permissions=['geolocation'],
            color_scheme='light',
            device_scale_factor=1,
            has_touch=False,
            is_mobile=False,
            java_script_enabled=True,
            accept_downloads=True
        )

        page = context.new_page()

        try:
            # Add random delays between actions to appear more human-like
            def random_delay():
                time.sleep(random.uniform(1, 3))

            # Navigate to Twitter login page
            print("Navigating to Twitter login page...")
            page.goto('https://twitter.com/login')
            random_delay()
            
            # Wait for the login form to be visible
            print("Waiting for username input field...")
            page.wait_for_selector('input[autocomplete="username"]')
            
            # Enter username/email with human-like typing
            print("Entering username...")
            username = os.getenv('TWITTER_USERNAME')
            for char in username:
                page.type('input[autocomplete="username"]', char, delay=random.uniform(50, 150))
            
            random_delay()
            
            # Check if the Next button is visible and clickable
            print("Looking for Next button...")
            next_button = page.get_by_role("button", name="Next")
            if next_button.is_visible():
                print("Next button is visible, attempting to click...")
                next_button.click()
            else:
                print("Next button is not visible!")
                page.screenshot(path="debug_screenshot.png")
                print("Screenshot saved as debug_screenshot.png")
            
            random_delay()
            
            # Wait for password field and enter password with human-like typing
            print("Waiting for password field...")
            page.wait_for_selector('input[type="password"]')
            password = os.getenv('TWITTER_PASSWORD')
            for char in password:
                page.type('input[type="password"]', char, delay=random.uniform(50, 150))
            
            random_delay()
            
            # Click login button
            print("Clicking login button...")
            login_button = page.get_by_role("button", name="Log in")
            if login_button.is_visible():
                login_button.click()

            # This enables Playwright Inspector, which can help with identifying the
            # selectors for elements on the page
            #if DEBUG_MODE:
                #page.pause()
            
            # Wait for successful login (wait for home timeline)
            print("Waiting for successful login...")
            page.get_by_test_id('AppTabBar_Home_Link').wait_for()
            
            print("Successfully logged in to Twitter!")
            
            # Scrape tweets
            tweets = scrape_tweets(page)
            
            # Send email with tweets
            if tweets:
                send_email("Latest Tweets from @veatch", tweets)
            else:
                print("No tweets were scraped!")
            
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