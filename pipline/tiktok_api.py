import requests
import json
from config import CLIENT_KEY, CLIENT_SECRET, TOKEN_URL
import time

def get_access_token():
    if not CLIENT_KEY or not CLIENT_SECRET:
        raise ValueError("Missing TIKTOK_CLIENT_KEY or TIKTOK_CLIENT_SECRET")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }

    response = requests.post(
        TOKEN_URL,
        headers=headers,
        data=data,
        timeout=30
    )

    response.raise_for_status()
    token_data = response.json()
    return token_data["access_token"]




def post(url, access_token, params=None, body=None):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        url,
        headers=headers,
        params=params,
        json=body,
        timeout=30
    )

    if response.status_code == 429:
        print("\nRate limit hit: too many requests")
        print("Status code:", response.status_code)
        print("URL:", response.url)
        return None

    if response.status_code >= 500:
        print("\nTikTok API server error")
        print("Status code:", response.status_code)
        print("URL:", response.url)
        print("Request body:")
        print(json.dumps(body, indent=2))

        print("Response body:")
        try:
            print(json.dumps(response.json(), indent=2))
        except Exception:
            print(response.text)

        return None

    if response.status_code >= 400:
        print("\nTikTok API client error")
        print("Status code:", response.status_code)
        print("URL:", response.url)
        print("Request body:")
        print(json.dumps(body, indent=2))

        print("Response body:")
        try:
            print(json.dumps(response.json(), indent=2))
        except Exception:
            print(response.text)

            return None

    return response.json()