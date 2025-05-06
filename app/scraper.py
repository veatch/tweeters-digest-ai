from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re

class TwitterScraper:
    def __init__(self):
        self.setup_driver()
        
    def setup_driver(self):
        """Set up the Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def get_tweets(self, username, count=10):
        """
        Scrape tweets from a user's profile.
        
        Args:
            username (str): Twitter username to scrape
            count (int): Number of tweets to fetch
            
        Returns:
            list: List of dictionaries containing tweet data
        """
        try:
            # Navigate to the user's profile
            url = f"https://twitter.com/{username}"
            self.driver.get(url)
            
            # Wait for tweets to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='tweet']"))
            )
            
            # Scroll to load more tweets if needed
            tweets_loaded = 0
            while tweets_loaded < count:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Wait for new tweets to load
                tweets_loaded = len(self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='tweet']"))
                if tweets_loaded >= count:
                    break
            
            # Parse the page content
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            tweets = []
            
            # Find all tweet elements
            tweet_elements = soup.find_all("article", {"data-testid": "tweet"})
            
            for tweet in tweet_elements[:count]:
                try:
                    # Extract tweet text
                    text_element = tweet.find("div", {"data-testid": "tweetText"})
                    text = text_element.get_text() if text_element else ""
                    
                    # Extract timestamp
                    time_element = tweet.find("time")
                    timestamp = time_element.get("datetime") if time_element else None
                    
                    # Extract tweet URL
                    link_element = tweet.find("a", {"href": re.compile(r"/status/\d+")})
                    tweet_id = link_element["href"].split("/status/")[-1] if link_element else None
                    tweet_url = f"https://twitter.com/{username}/status/{tweet_id}" if tweet_id else None
                    
                    tweets.append({
                        "username": username,
                        "text": text,
                        "created_at": timestamp,
                        "url": tweet_url
                    })
                except Exception as e:
                    print(f"Error parsing tweet: {str(e)}")
                    continue
            
            return tweets
            
        except Exception as e:
            print(f"Error scraping tweets for {username}: {str(e)}")
            return []
        
    def close(self):
        """Close the WebDriver."""
        if hasattr(self, 'driver'):
            self.driver.quit() 