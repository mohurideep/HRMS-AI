import requests

def load_swagger(url: str):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Failed to load Swagger documentation"}