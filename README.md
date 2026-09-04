# TikTok Research API Pipeline

A Python pipeline developed during a Maynooth University SPUR research internship to collect and prepare public TikTok video and comment data for research into company controversies and responses.

## What it does

- Converts company and event dates into valid 30-day TikTok API search windows.
- Collects video metadata with pagination and duplicate removal.
- Collects comments while saving progress for long-running requests.
- Exports data to CSV and removes videos marked irrelevant during review.

## Project structure

```text
pipeline/   API authentication, video search, comment collection and dataset creation
tools/      CSV/Excel conversion, filtering and cleanup utilities

```



