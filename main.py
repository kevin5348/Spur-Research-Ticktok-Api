from dataset import build_dataset
from csvMaker import csvmake



from comments import add_comments_to_videos


if __name__ == "__main__":
    add_comments_to_videos(
        input_file="videos_by_company.json",
        output_file="video_ids_by_company_with_comments.json"
    )
"""
if __name__ == "__main__":
    build_dataset(
        input_file="target_queries.json",
        output_file="tiktok_dataset.json"
    )

csvmake("tiktok_dataset.json")
"""