from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import jinja2
from .scraper import TwitterScraper

# Load environment variables
load_dotenv()

app = FastAPI(title="Tweeters Digest API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SendGrid setup
sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))

# Models
class TwitterUser(BaseModel):
    username: str
    last_checked: Optional[datetime] = None

class EmailConfig(BaseModel):
    recipient_email: str
    frequency: str  # daily, weekly
    last_sent: Optional[datetime] = None

# In-memory storage (replace with database in production)
users = []
email_config = None
scraper = None

@app.on_event("startup")
async def startup_event():
    global scraper
    scraper = TwitterScraper()

@app.on_event("shutdown")
async def shutdown_event():
    if scraper:
        scraper.close()

@app.get("/")
async def read_root():
    return {"message": "Welcome to Tweeters Digest API"}

@app.post("/users")
async def add_user(user: TwitterUser):
    try:
        # Verify user exists by attempting to scrape their profile
        tweets = scraper.get_tweets(user.username, count=1)
        if not tweets:
            raise HTTPException(status_code=400, detail="User not found or no tweets available")
        users.append(user)
        return {"message": f"Added user {user.username}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users")
async def get_users():
    return users

@app.delete("/users/{username}")
async def delete_user(username: str):
    global users
    users = [u for u in users if u.username != username]
    return {"message": f"Deleted user {username}"}

@app.post("/email-config")
async def set_email_config(config: EmailConfig):
    global email_config
    email_config = config
    return {"message": "Email configuration updated"}

@app.get("/tweets")
async def get_tweets():
    all_tweets = []
    for user in users:
        try:
            tweets = scraper.get_tweets(user.username, count=10)
            all_tweets.extend(tweets)
        except Exception as e:
            print(f"Error fetching tweets for {user.username}: {str(e)}")
    
    return sorted(all_tweets, key=lambda x: x["created_at"] if x["created_at"] else "", reverse=True)

@app.post("/send-digest")
async def send_digest():
    if not email_config:
        raise HTTPException(status_code=400, detail="Email configuration not set")
    
    tweets = await get_tweets()
    
    # Create email content using Jinja2 template
    template_loader = jinja2.FileSystemLoader(searchpath="./app/templates")
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template("email_template.html")
    
    email_content = template.render(tweets=tweets)
    
    message = Mail(
        from_email=Email("your-verified-sender@example.com"),
        to_emails=To(email_config.recipient_email),
        subject="Your Twitter Digest",
        html_content=Content("text/html", email_content)
    )
    
    try:
        response = sg.send(message)
        return {"message": "Digest sent successfully", "status_code": response.status_code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 