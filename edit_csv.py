

import csv


def remove_company_from_csv(input_csv, output_csv, company_to_remove):
    company_to_remove = company_to_remove.lower().strip()

    with open(input_csv, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        fieldnames = reader.fieldnames

    filtered_rows = [
        row for row in rows
        if row.get("company", "").lower().strip() != company_to_remove
    ]

    with open(output_csv, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered_rows)

    print(f"Original rows: {len(rows)}")
    print(f"Rows after removing {company_to_remove}: {len(filtered_rows)}")


remove_company_from_csv(
    input_csv="videos_no_duplicates.csv",
    output_csv="videos_filtered1.csv",
    company_to_remove="new_balance"
)