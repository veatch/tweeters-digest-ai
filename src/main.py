import os
from dotenv import load_dotenv
from twitter.scraper import login_to_twitter
from mailer.sender import send_email
from state import get_last_tweet_id, save_last_tweet_id

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
    
    # Get the last processed tweet ID
    last_tweet_id = get_last_tweet_id()
    if last_tweet_id:
        print(f"Resuming from tweet ID: {last_tweet_id}")
    
    # Scrape tweets
    tweets = login_to_twitter(debug_mode=debug_mode, since_id=last_tweet_id)
    
    # Send email with tweets if any were scraped
    if tweets:
        send_email("Latest Tweets from @veatch", tweets)
        # Save the ID of the most recent tweet
        if tweets[0].get('id'):
            save_last_tweet_id(tweets[0]['id'])
    else:
        print("No tweets were scraped!")

if __name__ == "__main__":
    main() 