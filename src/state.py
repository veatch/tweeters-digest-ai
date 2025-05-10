import json
import os
from pathlib import Path

# Use absolute path for state file in the top-level directory
STATE_FILE = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "last_tweet_id.json"

def get_last_tweet_id() -> str | None:
    """Get the last processed tweet ID from the state file."""
    if not STATE_FILE.exists():
        return None
    
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            return state.get('last_tweet_id')
    except (json.JSONDecodeError, KeyError):
        return None

def save_last_tweet_id(tweet_id: str) -> None:
    """Save the last processed tweet ID to the state file."""
    state = {'last_tweet_id': tweet_id}
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f) 