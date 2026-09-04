from config import VIDEO_FIELDS, VIDEO_QUERY_URL
from tiktok_api import post

def split_search_values(value):
    if value is None:
        return []

    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]

    return [v.strip() for v in str(value).split(",") if v.strip()]



def build_video_query(hashtag_name=None, keyword=None, min_comment_count=None):
    conditions = []

    hashtag_values = split_search_values(hashtag_name)
    keyword_values = split_search_values(keyword)

    if hashtag_values:
        conditions.append({
            "operation": "IN",
            "field_name": "hashtag_name",
            "field_values": hashtag_values
        })

    if keyword_values:
        conditions.append({
            "operation": "IN",
            "field_name": "keyword",
            "field_values": keyword_values
        })

    if min_comment_count is not None:
        conditions.append({
            "operation": "GTE",
            "field_name": "comment_count",
            "field_values": [str(min_comment_count)]
        })

    return {
            "and": conditions
        }
    


def get_video_ids_and_metadata(
    access_token,
    hashtag_name=None,
    keyword=None,
    min_comment_count=None,
    start_date=None,
    end_date=None,
    max_pages=None
):
    """
    Gets all videos matching hashtag + keyword + minimum comment count.
    Returns full metadata, so the video IDs can be reused for comment collection.
    """
    params = {
        "fields": VIDEO_FIELDS
    }

    cursor = 0
    has_more = True
    search_id = None
    page_number = 0
    all_videos = []
    seen_video_ids = set()

    while has_more:
        body = {
            "query": build_video_query(
                hashtag_name=hashtag_name,
                keyword=keyword,
                min_comment_count=min_comment_count
            ),
            "max_count": 100,
            "cursor": cursor,
            "is_random": False,
            "start_date": start_date,
            "end_date": end_date
        }
        if search_id is not None:
            body["search_id"] = search_id

        data = post(
            VIDEO_QUERY_URL,
            access_token=access_token,
            params=params,
            body=body
        )
        if data is None:
            print("Skipping this request because TikTok returned an error.")
            break
        api_data = data.get("data", {})
        videos = api_data.get("videos", [])

        if search_id is None:
            search_id = api_data.get("search_id")

        for video in videos:
            video_id = str(video.get("id"))
            if video_id and video_id not in seen_video_ids:
                seen_video_ids.add(video_id)
                all_videos.append(video)

        page_number += 1
        print(f"Video search page {page_number}: got {len(videos)} videos, total unique {len(all_videos)}")

        has_more = api_data.get("has_more", False)
        cursor = api_data.get("cursor", cursor + len(videos))

        if max_pages is not None and page_number >= max_pages:
            break

    return all_videos

