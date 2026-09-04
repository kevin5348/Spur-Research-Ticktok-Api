import json
import os
import shutil
import time
RATE_LIMIT_HIT = False
from config import COMMENT_FIELDS, COMMENT_LIST_URL
from tiktok_api import get_access_token, post


def get_comments_for_video(access_token, video_id):
    global RATE_LIMIT_HIT

    params = {
        "fields": COMMENT_FIELDS
    }

    all_comments = []
    cursor = 0
    has_more = True

    while has_more:
        body = {
            "video_id": int(video_id),
            "max_count": 100,
            "cursor": cursor
        }

        data = post(
            COMMENT_LIST_URL,
            access_token=access_token,
            params=params,
            body=body
        )

        if data is None:
            RATE_LIMIT_HIT = True
            print(f"Stopping at video {video_id}. Saved {len(all_comments)} comments collected for this video.")
            return all_comments

        api_data = data.get("data", {})
        comments = api_data.get("comments", [])
        all_comments.extend(comments)

        has_more = api_data.get("has_more", False)
        cursor = api_data.get("cursor", cursor + len(comments))

        print(f"Video {video_id}: collected {len(all_comments)} comments")

    return all_comments


def add_comments_to_videos(input_file, output_file):
    access_token = get_access_token()

    # IMPORTANT:
    # If output file already exists, resume from it instead of starting again
    resume_file = output_file if os.path.exists(output_file) else input_file

    print(f"Loading data from: {resume_file}")

    with open(resume_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, dict):
        companies = data.get("companies", [])
    elif isinstance(data, list):
        companies = data
    else:
        raise ValueError("JSON must be a list or a dict with a companies key")

    for company in companies:
        for video in company.get("videos", []):
            video_id = video.get("video_id") or video.get("id")

            if not video_id:
                video["comments"] = []
                continue

            # Skip videos already completed
            if "comments" in video:
                print(f"Skipping video {video_id}, already has comments")
                continue

            video["comments"] = get_comments_for_video(access_token, video_id)

            # Backup previous output before overwriting
            if os.path.exists(output_file):
                shutil.copy(output_file, output_file + ".bak")

            with open(output_file, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2, ensure_ascii=False)

            print(f"Saved progress after video {video_id}")

            if RATE_LIMIT_HIT:
                print(f"Rate limit/API stop hit. Progress saved to {output_file}")
                return

            time.sleep(3)

    # Final save
    if os.path.exists(output_file):
        shutil.copy(output_file, output_file + ".bak")

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    print(f"Saved nested comments JSON to {output_file}")