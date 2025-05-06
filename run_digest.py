import asyncio
import os
from dotenv import load_dotenv
from app.main import app
from app.scraper import TwitterScraper
from app.models import EmailConfig

async def run_digest():
    # Load environment variables
    load_dotenv()
    
    # Initialize scraper
    scraper = TwitterScraper()
    try:
        # Get tweets
        tweets = await app.get_tweets()
        
        # Send email
        config = EmailConfig(
            recipient_email=os.getenv('RECIPIENT_EMAIL'),
            frequency='daily'
        )
        await app.send_digest()
    finally:
        scraper.close()

if __name__ == "__main__":
    asyncio.run(run_digest()) 