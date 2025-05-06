import os
from tweet_digest import setup_driver, get_tweets, send_email

def test_tweet_scraping():
    """Test the tweet scraping functionality."""
    driver = setup_driver()
    try:
        # Test with a known Twitter account
        test_username = "elonmusk"  # Using a popular account for testing
        print(f"Testing tweet scraping for @{test_username}...")
        tweets = get_tweets(driver, test_username, hours_ago=48)  # Get tweets from last 48 hours for testing
        
        print(f"\nFound {len(tweets)} tweets:")
        for tweet in tweets:
            print(f"\nTimestamp: {tweet['timestamp']}")
            print(f"Text: {tweet['text']}")
            
    finally:
        driver.quit()

def test_email_sending():
    """Test the email sending functionality."""
    # Create test data
    test_tweets = {
        "test_user1": [
            {
                "text": "This is a test tweet 1",
                "timestamp": "2024-01-01 12:00:00"
            },
            {
                "text": "This is a test tweet 2",
                "timestamp": "2024-01-01 13:00:00"
            }
        ],
        "test_user2": [
            {
                "text": "Another test tweet",
                "timestamp": "2024-01-01 14:00:00"
            }
        ]
    }
    
    print("Testing email sending...")
    send_email(test_tweets)

if __name__ == "__main__":
    # Check if environment variables are set
    required_vars = ['EMAIL_SENDER', 'EMAIL_PASSWORD', 'EMAIL_RECIPIENT']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Please set the following environment variables: {', '.join(missing_vars)}")
    else:
        print("Running tweet scraping test...")
        test_tweet_scraping()
        
        print("\nRunning email sending test...")
        test_email_sending() 