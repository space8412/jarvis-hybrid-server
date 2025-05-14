import requests
import os

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# 대표님이 지금 붙여넣은 ID로 테스트
database_id = "1f2b0006df05803b9390dbfa131c378c"
url = f"https://api.notion.com/v1/databases/{database_id}"

response = requests.get(url, headers=headers)

print(response.status_code)
print(response.text)
