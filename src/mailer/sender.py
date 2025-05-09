import os
import requests
from typing import List, Dict

def send_email(subject: str, tweets: List[Dict[str, str]]) -> bool:
    """
    Send an email using Mailgun API with formatted tweet content
    
    Args:
        subject: Email subject line
        tweets: List of tweet dictionaries containing text, likes, retweets, and date
        
    Returns:
        bool: True if email was sent successfully, False otherwise
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