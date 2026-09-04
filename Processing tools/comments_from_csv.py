import argparse
import csv
import json
import re
import zipfile
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

from comments import get_comments_for_video
from tiktok_api import get_access_token


POSSIBLE_ID_COLUMNS = [
    "id",
    "video_id",
    "Video ID",
    "video id",
    "tiktok_id",
]

POSSIBLE_COMPANY_COLUMNS = [
    "company",
    "Company",
    "company_name",
]


VIDEO_FIELDS_TO_KEEP_FIRST = [
    "id",
    "tiktok_url",
    "tiktok_link",
    "v3_flag",
    "v3_score",
    "v2_flag",
    "controversy_key",
    "controversy_text",
    "company",
    "Before_or_after_Transgression",
    "username",
    "video_description",
    "description_without_hashtags",
    "hashtags_used_for_check",
    "region_code",
    "create_time",
    "like_count",
    "comment_count",
    "share_count",
    "view_count",
    "hashtag_names",
    "favorites_count",
    "video_duration",
    "voice_to_text",
]


COMMENT_FIELDS_TO_KEEP = [
    "id",
    "video_id",
    "text",
    "like_count",
    "reply_count",
    "parent_comment_id",
    "create_time",
    "display_name",
]


def safe_str(value):
    if value is None:
        return ""
    return str(value)


def unix_to_iso(value):
    """Convert TikTok unix create_time to ISO text. Leaves existing text alone."""
    if value in (None, ""):
        return ""

    try:
        value_int = int(value)
        # TikTok timestamps are in seconds, not milliseconds.
        if value_int > 10_000_000_000:
            value_int = value_int // 1000
        return datetime.fromtimestamp(value_int, tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return safe_str(value)


def clean_video_id(value):
    """Clean video IDs read from CSV or Excel.

    Excel can sometimes turn long numeric IDs into strings like 72123...0.0,
    so this keeps only the digits before any .0 suffix. If a full TikTok URL is
    in the ID column, it extracts the /video/<id> part.
    """
    value = safe_str(value).strip()

    if not value:
        return ""

    match = re.search(r"/video/(\d+)", value)
    if match:
        return match.group(1)

    if re.fullmatch(r"\d+\.0", value):
        value = value[:-2]

    value = value.replace(",", "").replace(" ", "")
    return value if value.isdigit() else ""


def read_csv_rows(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def _xlsx_col_to_index(cell_reference):
    letters = "".join(ch for ch in cell_reference if ch.isalpha())
    index = 0
    for ch in letters:
        index = index * 26 + (ord(ch.upper()) - ord("A") + 1)
    return index - 1


def _read_xlsx_shared_strings(zip_file):
    try:
        xml_bytes = zip_file.read("xl/sharedStrings.xml")
    except KeyError:
        return []

    root = ET.fromstring(xml_bytes)
    namespace = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    strings = []

    for item in root.findall("main:si", namespace):
        text_parts = []
        for text_node in item.findall(".//main:t", namespace):
            text_parts.append(text_node.text or "")
        strings.append("".join(text_parts))

    return strings


def _first_sheet_path(zip_file):
    workbook = ET.fromstring(zip_file.read("xl/workbook.xml"))
    rels = ET.fromstring(zip_file.read("xl/_rels/workbook.xml.rels"))

    workbook_ns = {
        "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }
    rels_ns = {"rel": "http://schemas.openxmlformats.org/package/2006/relationships"}

    first_sheet = workbook.find("main:sheets/main:sheet", workbook_ns)
    if first_sheet is None:
        raise ValueError("No sheets found in Excel file.")

    relationship_id = first_sheet.attrib[
        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    ]

    for rel in rels.findall("rel:Relationship", rels_ns):
        if rel.attrib.get("Id") == relationship_id:
            target = rel.attrib["Target"]
            if not target.startswith("xl/"):
                target = "xl/" + target.lstrip("/")
            return target

    raise ValueError("Could not find the first sheet XML file.")


def read_xlsx_rows(path):
    """Read the first worksheet from an .xlsx file without pandas/openpyxl."""
    with zipfile.ZipFile(path) as zip_file:
        shared_strings = _read_xlsx_shared_strings(zip_file)
        sheet_path = _first_sheet_path(zip_file)
        sheet = ET.fromstring(zip_file.read(sheet_path))

    namespace = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    raw_rows = []

    for row in sheet.findall(".//main:sheetData/main:row", namespace):
        values = []

        for cell in row.findall("main:c", namespace):
            cell_reference = cell.attrib.get("r", "A1")
            column_index = _xlsx_col_to_index(cell_reference)

            while len(values) <= column_index:
                values.append("")

            cell_type = cell.attrib.get("t")
            value_node = cell.find("main:v", namespace)
            inline_node = cell.find("main:is/main:t", namespace)

            if cell_type == "s" and value_node is not None:
                shared_index = int(value_node.text)
                values[column_index] = shared_strings[shared_index]
            elif cell_type == "inlineStr" and inline_node is not None:
                values[column_index] = inline_node.text or ""
            elif value_node is not None:
                values[column_index] = value_node.text or ""
            else:
                values[column_index] = ""

        raw_rows.append(values)

    if not raw_rows:
        return []

    headers = [safe_str(header).strip() for header in raw_rows[0]]
    rows = []

    for raw_row in raw_rows[1:]:
        row_dict = {}
        for index, header in enumerate(headers):
            if header:
                row_dict[header] = raw_row[index] if index < len(raw_row) else ""
        rows.append(row_dict)

    return rows


def read_video_rows(path):
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return read_csv_rows(path)

    if suffix == ".xlsx":
        return read_xlsx_rows(path)

    raise ValueError("Input file must be a .csv or .xlsx file.")


def find_column(rows, requested_column, possible_columns, label):
    if not rows:
        raise ValueError("The video file is empty.")

    headers = list(rows[0].keys())

    if requested_column and requested_column in headers:
        return requested_column

    for column in possible_columns:
        if column in headers:
            return column

    raise ValueError(
        f"Could not find a {label} column. I looked for {possible_columns}. "
        f"Your columns are: {headers}"
    )


def order_video_fields(video_row, video_id):
    """Keep all video columns, but place the important ones first."""
    output = OrderedDict()
    output["id"] = safe_str(video_id)

    for field in VIDEO_FIELDS_TO_KEEP_FIRST:
        if field == "id":
            continue
        if field in video_row:
            output[field] = video_row.get(field)

    for field, value in video_row.items():
        if field not in output and field != "id":
            output[field] = value

    return output


def format_comment(comment, video_id):
    """Format one top-level comment only. No replies are requested or nested."""
    return {
        "id": safe_str(comment.get("id")),
        "video_id": safe_str(comment.get("video_id") or video_id),
        "text": safe_str(comment.get("text")),
        "like_count": comment.get("like_count", ""),
        "reply_count": comment.get("reply_count", ""),
        "parent_comment_id": safe_str(comment.get("parent_comment_id")),
        "create_time": unix_to_iso(comment.get("create_time")),
        "display_name": safe_str(comment.get("display_name")),
    }


def collect_comments_from_video_file(
    video_file,
    output_file="comments_dataset.json",
    id_column="id",
    company_column="company",
    max_videos=None,
):
    """Read video IDs from a CSV/XLSX and save nested JSON.

    Output structure:
    [
      {
        "company": "company_name",
        "video_count": 2,
        "comments_count_collected": 123,
        "videos": [
          {
            "id": "...",
            "video_description": "...",
            "comments_count_collected": 50,
            "comments": [{...}, {...}]
          }
        ]
      }
    ]
    """
    rows = read_video_rows(video_file)
    id_column = find_column(rows, id_column, POSSIBLE_ID_COLUMNS, "video ID")
    company_column = find_column(rows, company_column, POSSIBLE_COMPANY_COLUMNS, "company")
    access_token = get_access_token()

    seen_video_ids = set()
    grouped = OrderedDict()

    for row in rows:
        video_id = clean_video_id(row.get(id_column))
        if not video_id or video_id in seen_video_ids:
            continue

        seen_video_ids.add(video_id)
        company = safe_str(row.get(company_column)).strip() or "unknown_company"

        if company not in grouped:
            grouped[company] = []

        grouped[company].append((video_id, row))

    all_video_rows = [item for videos in grouped.values() for item in videos]
    if max_videos is not None:
        allowed_ids = {video_id for video_id, _ in all_video_rows[:max_videos]}
        for company in list(grouped.keys()):
            grouped[company] = [item for item in grouped[company] if item[0] in allowed_ids]
            if not grouped[company]:
                del grouped[company]

    total_unique_videos = sum(len(videos) for videos in grouped.values())
    print(f"Found {total_unique_videos} unique video IDs in {video_file}")

    output_data = []
    global_index = 0

    for company, video_rows in grouped.items():
        company_result = {
            "company": company,
            "video_count": len(video_rows),
            "comments_count_collected": 0,
            "videos": [],
        }

        for video_id, video_row in video_rows:
            global_index += 1
            print(f"\n[{global_index}/{total_unique_videos}] Collecting comments for video {video_id}")

            try:
                raw_comments = get_comments_for_video(access_token, video_id)
            except Exception as error:
                print(f"Failed to collect comments for video {video_id}: {error}")
                raw_comments = []

            formatted_comments = [format_comment(comment, video_id) for comment in raw_comments]

            video_output = order_video_fields(video_row, video_id)
            video_output["comments_count_collected"] = len(formatted_comments)
            video_output["comments"] = formatted_comments

            company_result["comments_count_collected"] += len(formatted_comments)
            company_result["videos"].append(video_output)

            # Save progress after every video, so you keep data if the API stops mid-run.
            with open(output_file, "w", encoding="utf-8") as file:
                json.dump(output_data + [company_result], file, indent=2, ensure_ascii=False)

            print(f"Saved {len(formatted_comments)} comments for video {video_id}")

        output_data.append(company_result)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(output_data, file, indent=2, ensure_ascii=False)

    total_comments = sum(company["comments_count_collected"] for company in output_data)
    print(f"\nDone. Saved {total_comments} comments from {total_unique_videos} videos to {output_file}")
    return output_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Read TikTok video IDs from a video CSV/XLSX and collect top-level comments into nested JSON."
    )
    parser.add_argument(
        "video_file",
        nargs="?",
        default="videos_checked_v3.xlsx",
        help="Path to the video CSV/XLSX file. Default: videos_checked_v3.xlsx",
    )
    parser.add_argument(
        "--output",
        default="comments_dataset.json",
        help="Output JSON file. Default: comments_dataset.json",
    )
    parser.add_argument(
        "--id-column",
        default="id",
        help="Name of the video ID column. Default: id",
    )
    parser.add_argument(
        "--company-column",
        default="company",
        help="Name of the company column. Default: company",
    )
    parser.add_argument(
        "--max-videos",
        type=int,
        default=None,
        help="Optional limit for testing, e.g. --max-videos 3",
    )

    args = parser.parse_args()

    collect_comments_from_video_file(
        video_file=args.video_file,
        output_file=args.output,
        id_column=args.id_column,
        company_column=args.company_column,
        max_videos=args.max_videos,
    )
