import os
import time
import random
import json
from datetime import datetime
from typing import List, Dict
from playwright.sync_api import Page, sync_playwright
from pathlib import Path

# Common user agents for modern browsers
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]

COOKIES_FILE = Path("twitter_cookies.json")

def debug_log(message: str, debug_mode: bool = False) -> None:
    """Helper function to print debug messages only when in debug mode"""
    if debug_mode:
        print(f"[DEBUG] {message}")

def scrape_tweets(page: Page, username: str = "veatch", num_tweets: int = 5, since_id: str | None = None, debug_mode: bool = False) -> List[Dict[str, str]]:
    """
    Scrape tweets from a specific user
    
    Args:
        page: Playwright page object
        username: Twitter username to scrape
        num_tweets: Number of tweets to scrape
        since_id: Only scrape tweets newer than this ID
        debug_mode: Whether to run in debug mode with additional logging
        
    Returns:
        List of tweet dictionaries containing text, likes, retweets, date, and id
    """
    debug_log(f"Starting tweet scraping for @{username}", debug_mode)
    print(f"Navigating to @{username}'s profile...")
    page.goto(f'https://twitter.com/{username}')
    time.sleep(3)  # Wait for page to load

    tweets = []
    tweet_elements = page.query_selector_all('article[data-testid="tweet"]')
    debug_log(f"Found {len(tweet_elements)} tweet elements", debug_mode)
    
    for i, tweet in enumerate(tweet_elements[:num_tweets], 1):
        try:
            debug_log(f"Processing tweet {i}/{num_tweets}", debug_mode)
            
            # Get tweet ID from the article element
            tweet_id = tweet.get_attribute('data-tweet-id')
            if not tweet_id:
                # Try to get ID from the tweet link
                tweet_link = tweet.query_selector('a[href*="/status/"]')
                if tweet_link:
                    href = tweet_link.get_attribute('href')
                    tweet_id = href.split('/status/')[-1].split('?')[0]
            
            # Skip tweets older than since_id if provided
            if since_id and tweet_id and tweet_id <= since_id:
                debug_log(f"Skipping tweet {tweet_id} as it's older than {since_id}", debug_mode)
                continue
            
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
                'id': tweet_id,
                'text': text,
                'likes': likes,
                'retweets': retweets,
                'date': date
            })
            debug_log(f"Successfully processed tweet {i}", debug_mode)
        except Exception as e:
            print(f"Error scraping tweet: {str(e)}")
            debug_log(f"Failed to process tweet {i}: {str(e)}", debug_mode)
            continue

    debug_log(f"Successfully scraped {len(tweets)} tweets", debug_mode)
    return tweets

def login_to_twitter(debug_mode: bool = False, since_id: str | None = None) -> List[Dict[str, str]]:
    """
    Login to Twitter and scrape tweets
    
    Args:
        debug_mode: Whether to run in debug mode with browser visible and additional logging
        since_id: Only scrape tweets newer than this ID
        
    Returns:
        List of scraped tweets
    """
    debug_log("Initializing Playwright", debug_mode)
    with sync_playwright() as p:
        # Launch browser with more realistic settings
        debug_log("Launching browser", debug_mode)
        browser = p.chromium.launch(
            headless=not debug_mode,
            devtools=debug_mode,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials'
            ]
        )
        
        # Create a more realistic browser context
        debug_log("Creating browser context", debug_mode)
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
            # Try to load cookies if they exist
            if COOKIES_FILE.exists():
                debug_log("Loading saved cookies", debug_mode)
                with open(COOKIES_FILE, 'r') as f:
                    cookies = json.load(f)
                context.add_cookies(cookies)
                
                # Try to access Twitter with saved cookies
                print("Attempting to access Twitter with saved cookies...")
                page.goto('https://twitter.com/home')
                time.sleep(3)
                
                # Check if we're actually logged in
                if page.get_by_test_id('AppTabBar_Home_Link').is_visible():
                    print("Successfully logged in using saved cookies!")
                    return scrape_tweets(page, debug_mode=debug_mode, since_id=since_id)
                else:
                    print("Saved cookies are invalid, proceeding with password login...")
            
            # If we get here, we need to do a password login
            def random_delay():
                delay = random.uniform(1, 3)
                debug_log(f"Random delay: {delay:.2f}s", debug_mode)
                time.sleep(delay)

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
            
            # Wait for successful login (wait for home timeline)
            print("Waiting for successful login...")
            page.get_by_test_id('AppTabBar_Home_Link').wait_for()
            
            print("Successfully logged in to Twitter!")
            
            # Save cookies after successful login
            debug_log("Saving cookies for future use", debug_mode)
            cookies = context.cookies()
            with open(COOKIES_FILE, 'w') as f:
                json.dump(cookies, f)
            
            # Scrape tweets
            return scrape_tweets(page, debug_mode=debug_mode, since_id=since_id)
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            debug_log(f"Error during Twitter login: {str(e)}", debug_mode)
            # Take a screenshot on error
            try:
                page.screenshot(path="error_screenshot.png")
                print("Error screenshot saved as error_screenshot.png")
            except:
                print("Could not save error screenshot")
            return []
        
        finally:
            debug_log("Closing browser", debug_mode)
            browser.close() 