# app/hrms_client.py
import requests

BASE_URL = "https://hrmsapi.pureagrigroup.com"

def get_holidays(auth_token: str):
    url = f"{BASE_URL}/api/v1/attendance/getHolidays"
    headers = {"Authorization": auth_token,
               "accept": "*/*"}
    response = requests.get(url, headers=headers)
    print("==== DEBUG REQUEST ====")
    print("URL:", url)
    print("HEADERS:", headers)
    print("STATUS:", response.status_code)
    print("RESPONSE:", response.text)
    
    if response.status_code != 200:
        return {"error": "API_FAILED", "status_code": response.status_code, "message": response.text}
    try:
        return response.json()
    except ValueError:
        return {"error": "INVALID_JSON", "raw_response": response.text}