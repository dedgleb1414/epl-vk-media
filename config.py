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

# Беседа "Футбол Глебовка": peer_id различается в зависимости от того, чьим токеном смотреть.
# CHAT_PEER_ID — со стороны сообщества (VK_TOKEN): именно это присылает Callback API в peer_id
# входящих событий, и именно это нужно messages.send для отправки в беседу.
CHAT_PEER_ID = int(os.getenv("CHAT_PEER_ID", "2000000001"))
# CHAT_PEER_ID_HISTORY — та же беседа со стороны личного аккаунта (USER_TOKEN): нужен для
# messages.getHistory/polls.getById, так как групповой токен эти методы не поддерживает.
CHAT_PEER_ID_HISTORY = int(os.getenv("CHAT_PEER_ID_HISTORY", "2000000216"))