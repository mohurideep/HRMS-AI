# app/tools/executor.py
import logging
import time
import requests
from app.core.config import BASE_URL

def execute_tool(tool, args, auth_token):

    start_time = time.time()
    url = BASE_URL + tool["path"]

    headers = {
        "Authorization": auth_token,
        "accept": "*/*"
    }

    if tool["method"] == "GET":
        response = requests.get(url, headers=headers, params=args)

    elif tool["method"] == "POST":
        response = requests.post(url, headers=headers, json=args)

    else:
        raise Exception("Unsupported method")

    if response.status_code != 200:
        raise Exception(f"API failed: {response.text}")

    duration = time.time() - start_time
    logging.info(f"🌐 API latency ({tool['name']}): {duration:.3f}s")

    return response.json()