import csv
import json
import re

def csvmake(INPUT_FILE):
    EXCLUDED_FIELDS = {
      
    }

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    for company_data in dataset:
        company = company_data.get("company", "unknown_company")
        search = company_data.get("search", {})
        rows = []

        for video in company_data.get("videos", []):
            row = {
                "company": company,
                "Before_or_after_Transgression": company_data.get("Before_or_after_Transgression"),
                "search_hashtag": search.get("hashtag_name"),
                "search_keyword": search.get("keyword"),
                "search_min_comment_count": search.get("min_comment_count"),
                "search_start_date": search.get("start_date"),
                "search_end_date": search.get("end_date"),
            }

            for field, value in video.items():
                if field not in EXCLUDED_FIELDS:
                    row[field] = value

            rows.append(row)

        # Sort this company's videos by comment count
        rows.sort(
            key=lambda row: row.get("comment_count", 0) or 0,
            reverse=True,
        )

        if rows:
            output_file = f"videos.csv"

            with open(output_file, "a", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=rows[0].keys())
                writer.writerows(rows)

            print(f"Saved {len(rows)} videos to {output_file}")
        else:
            print(f"No videos found for {company}")