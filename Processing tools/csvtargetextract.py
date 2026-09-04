import csv
import json
import re
import unicodedata
from datetime import datetime, timedelta


def normalize_text(text):
    return (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
    )


def make_company_name(company):
    company = normalize_text(company).lower()
    company = re.sub(r"[^a-z0-9]+", "_", company)
    return company.strip("_")


def make_hashtag(company):
    company = normalize_text(company).lower()
    return re.sub(r"[^a-z0-9]", "", company)


def parse_date(value):
    value = value.strip().replace("Z", "+00:00")
    return datetime.fromisoformat(value).date()


def split_date_range(start_date, end_date):
    """Split a date range into non-overlapping periods of up to 30 days."""
    periods = []
    current_start = start_date

    while current_start <= end_date:
        current_end = min(
            current_start + timedelta(days=29),
            end_date
        )

        periods.append((current_start, current_end))
        current_start = current_end + timedelta(days=1)

    return periods


def csv_to_json(input_csv, output_json):
    targets = []

    with open(input_csv, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row_number, row in enumerate(reader, start=2):
            company = row["Company"].strip()
            initial_value = row["Date of Initial Transgression"].strip()
            response_value = row["Date of Response"].strip()

            if not company or not initial_value or not response_value:
                print(f"Skipping row {row_number}: missing information")
                continue

            initial_date = parse_date(initial_value)
            response_date = parse_date(response_value)

            if response_date < initial_date:
                print(
                    f"Skipping {company}: response date is before "
                    "the initial transgression"
                )
                continue

            # Keep the same date when both events occurred on the same day.
            if response_date == initial_date:
                final_end_date = initial_date
            else:
                final_end_date = response_date - timedelta(days=1)

            periods = split_date_range(
                start_date=initial_date,
                end_date=final_end_date
            )

            for start_date, end_date in periods:
                targets.append({
                    "company": make_company_name(company),
                    "hashtag_name": make_hashtag(company),
                    "min_comment_count": 100,
                    "start_date": start_date.strftime("%Y%m%d"),
                    "end_date": end_date.strftime("%Y%m%d"),
                    "Before_or_after_Transgression": "before"
                })
            after_start_date = final_end_date + timedelta(days=1)
            after_end_date = after_start_date + timedelta(days=14)

            after_periods = split_date_range(
                start_date=after_start_date,
                end_date=after_end_date
            )

            for start_date, end_date in after_periods:
                targets.append({
                    "company": make_company_name(company),
                    "hashtag_name": make_hashtag(company),
                    "min_comment_count": 100,
                    "start_date": start_date.strftime("%Y%m%d"),
                    "end_date": end_date.strftime("%Y%m%d"),
                    "Before_or_after_Transgression": "after"
                })

    with open(output_json, "w", encoding="utf-8") as file:
        json.dump(targets, file, indent=2, ensure_ascii=False)

    print(f"Saved {len(targets)} search periods to {output_json}")
    return targets


csv_to_json(
    input_csv="target_companies.csv",
    output_json="targets.json"
)