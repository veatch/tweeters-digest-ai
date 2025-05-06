import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
TWITTER_USERS = os.getenv('TWITTER_USERS', '').split(',')
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_RECIPIENT = os.getenv('EMAIL_RECIPIENT')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))

def setup_driver():
    """Set up and return a configured Chrome WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def get_tweets(driver, username, hours_ago=24):
    """Scrape tweets from a specific user within the last 24 hours."""
    url = f'https://twitter.com/{username}'
    driver.get(url)
    
    # Wait for tweets to load
    time.sleep(5)
    
    tweets = []
    tweet_elements = driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
    
    for tweet in tweet_elements[:10]:  # Get last 10 tweets
        try:
            tweet_text = tweet.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]').text
            timestamp = tweet.find_element(By.TAG_NAME, 'time').get_attribute('datetime')
            tweet_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            if datetime.now(tweet_time.tzinfo) - tweet_time <= timedelta(hours=hours_ago):
                tweets.append({
                    'text': tweet_text,
                    'timestamp': tweet_time.strftime('%Y-%m-%d %H:%M:%S')
                })
        except Exception as e:
            print(f"Error processing tweet: {e}")
            continue
    
    return tweets

def send_email(tweets_by_user):
    """Send an email with the collected tweets."""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECIPIENT
    msg['Subject'] = f"Twitter Digest - {datetime.now().strftime('%Y-%m-%d')}"
    
    body = "Here's your Twitter digest:\n\n"
    
    for username, tweets in tweets_by_user.items():
        if tweets:
            body += f"\n=== Tweets from @{username} ===\n\n"
            for tweet in tweets:
                body += f"[{tweet['timestamp']}]\n{tweet['text']}\n\n"
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

def main():
    """Main function to scrape tweets and send email."""
    if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT]):
        print("Please set all required environment variables")
        return
    
    driver = setup_driver()
    tweets_by_user = {}
    
    try:
        for username in TWITTER_USERS:
            username = username.strip()
            if username:
                print(f"Scraping tweets from @{username}...")
                tweets = get_tweets(driver, username)
                tweets_by_user[username] = tweets
        
        send_email(tweets_by_user)
    finally:
        driver.quit()

if __name__ == "__main__":
    main() 