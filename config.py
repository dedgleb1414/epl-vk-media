from dotenv import load_dotenv
import os

load_dotenv(override=True)

VK_TOKEN = os.getenv("VK_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")
ADMIN_ID = os.getenv("ADMIN_ID")
FOOTBALL_KEY = os.getenv("FOOTBALL_API_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")
USER_TOKEN = os.getenv("USER_TOKEN")
YOUTUBE_KEY = os.getenv("YOUTUBE_API_KEY")