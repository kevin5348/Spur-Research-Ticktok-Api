
import json
from tiktok_api import get_access_token
from utils import safe_str, unix_to_iso
from videos import get_video_ids_and_metadata


def format_video(video):
    return {
        "id": safe_str(video.get("id")),
        "video_description": video.get("video_description"),
        "username": video.get("username"),
        "region_code": video.get("region_code"),
        "create_time": unix_to_iso(video.get("create_time")),
        "like_count": video.get("like_count"),
        "comment_count": video.get("comment_count"),
        "share_count": video.get("share_count"),
        "view_count": video.get("view_count"),
        "hashtag_names": video.get("hashtag_names"),
        "favorites_count": video.get("favorites_count"),
        "video_duration": video.get("video_duration"),
        "video_label": video.get("video_label"),
        "voice_to_text": video.get("voice_to_text")
    }


def build_dataset(input_file, output_file):
    access_token = get_access_token()

    with open(input_file, "r", encoding="utf-8") as file:
        targets = json.load(file)

    final_data = []

    for target in targets:
        company = target.get("company")
        hashtag_name = target.get("hashtag_name")
        keyword = target.get("keyword")
        min_comment_count = target.get("min_comment_count")
        start_date = target.get("start_date")
        end_date = target.get("end_date")
        Before_or_after_Transgression = target.get("Before_or_after_Transgression")
        print(f"\nSearching videos for {company}")
        print(
            f"hashtag={hashtag_name}, keyword={keyword}, "
            f"min_comment_count={min_comment_count}"
        )

        videos = get_video_ids_and_metadata(
            access_token=access_token,
            hashtag_name=hashtag_name,
            keyword=keyword,
            min_comment_count=min_comment_count,
            start_date=start_date,
            end_date=end_date
        )

        formatted_videos = [
            format_video(video)
            for video in videos
            if video.get("id")
        ]

        target_result = {
            "company": company,
            "Before_or_after_Transgression" : Before_or_after_Transgression, 
            "search": {
                "hashtag_name": hashtag_name,
                "keyword": keyword,
                "min_comment_count": min_comment_count,
                "start_date": start_date,
                "end_date": end_date
            },
            "video_count": len(formatted_videos),
            "videos": formatted_videos
        }

        # Must be inside the target loop.
        final_data.append(target_result)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(final_data, file, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(final_data)} searches to {output_file}")
    return final_data


    """    



#def format_comment(comment, replies=None):
    text = comment.get("text")
    return {
        "id": safe_str(comment.get("id")),
        "video_id": safe_str(comment.get("video_id")),
        "text": comment.get("text"),
        "text_length": text_length(text),
        "like_count": comment.get("like_count"),
        "reply_count": comment.get("reply_count"),
        "is_reply": False,
        "parent_comment_id": safe_str(comment.get("parent_comment_id")),
        "create_time": unix_to_iso(comment.get("create_time")),
        "display_name": comment.get("display_name"),
        "replies": replies or []
    }





def build_dataset(input_file, output_file):
    access_token = get_access_token()

    with open(input_file, "r", encoding="utf-8") as file:
        targets = json.load(file)

    final_data = []

    for target in targets:
        company = target.get("company")
        hashtag_name = target.get("hashtag_name")
        keyword = target.get("keyword")
        min_comment_count = target.get("min_comment_count")
        start_date = target.get("start_date")
        end_date = target.get("end_date")
        

        print(f"\nSearching videos for {company}")
        print(f"hashtag={hashtag_name}, keyword={keyword}, min_comment_count={min_comment_count}")

        videos = get_video_ids_and_metadata(
            access_token=access_token,
            hashtag_name=hashtag_name,
            keyword=keyword,
            min_comment_count=min_comment_count,
            start_date=start_date,
            end_date=end_date,
        )

        target_result = {
            "company": company,
            "search": {
                "hashtag_name": hashtag_name,
                "keyword": keyword,
                "min_comment_count": min_comment_count,
                "start_date": start_date,
                "end_date": end_date
            },
            "video_count": len(videos),
            "videos": []
        }

    for video in videos:
            video_id = safe_str(video.get("id"))
            if not video_id:
                continue

            print(f"\nCollecting comments for video {video_id}")
            comments = get_comments_for_video(access_token, video_id)

            formatted_comments = []

            for comment in comments:
                comment_id = safe_str(comment.get("id"))
                replies = []

                if comment_id and comment.get("reply_count", 0) > 0:
                    raw_replies = get_replies_for_comment(access_token, comment_id)
                    replies = [
                        format_reply(reply, parent_comment_id=comment_id)
                        for reply in raw_replies
                    ]

                formatted_comments.append(
                    format_comment(comment, replies=replies)
                )

            target_result["videos"].append({
                "video": format_video(video),
                "comments_count_collected": len(formatted_comments),
                "comments": formatted_comments
            })

    final_data.append(target_result)
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(final_data, file, indent=2, ensure_ascii=False)

    print(f"\nSaved dataset to {output_file}")
    return final_data
"""