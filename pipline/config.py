import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")

TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
VIDEO_QUERY_URL = "https://open.tiktokapis.com/v2/research/video/query/"
COMMENT_LIST_URL = "https://open.tiktokapis.com/v2/research/video/comment/list/"

VIDEO_FIELDS = (
    "id,video_description,create_time,username,region_code,"
    "like_count,comment_count,share_count,view_count,"
    "music_id,favorites_count,video_duration,voice_to_text"
    
)

COMMENT_FIELDS = (
    "id,video_id,text,like_count,reply_count,"
    "parent_comment_id,create_time,display_name"
)
