import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class Config:
    SUPABASE_URL: str = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY: str = os.getenv('SUPABASE_KEY', '')
    MAILJET_API_KEY: str = os.getenv('MAILJET_API_KEY', '')
    MAILJET_API_SECRET: str = os.getenv('MAILJET_API_SECRET', '')

config = Config()
