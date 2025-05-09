import os
from dotenv import load_dotenv
from twitter.scraper import login_to_twitter
from mailer.sender import send_email

# Try to load from .env file, but don't fail if it doesn't exist
load_dotenv(override=True)

def main():
    # Check if environment variables are set
    if not os.getenv('TWITTER_USERNAME') or not os.getenv('TWITTER_PASSWORD'):
        print("Please set TWITTER_USERNAME and TWITTER_PASSWORD environment variables")
        exit(1)
    
    # Check for debug mode
    debug_mode = os.getenv('DEBUG_MODE', '').lower() in ('true', '1', 'yes')
    if debug_mode:
        print("Running in debug mode - browser will be visible and devtools enabled")
        os.environ['PWDEBUG'] = '1'  # Enable Playwright Inspector
    
    # Scrape tweets
    tweets = login_to_twitter(debug_mode=debug_mode)
    
    # Send email with tweets if any were scraped
    if tweets:
        send_email("Latest Tweets from @veatch", tweets)
    else:
        print("No tweets were scraped!")

if __name__ == "__main__":
    main() 