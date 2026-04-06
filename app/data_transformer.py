# app/data_transformer.py

from datetime import datetime

def clean_holidays(raw_response: dict):
    """
    Cleans HRMS holiday API response for LLM consumption
    """

    if not raw_response or "data" not in raw_response:
        return []

    cleaned = []

    for item in raw_response["data"]:
        try:
            # Extract only required fields
            name = item.get("name")

            # Convert ISO date → readable format
            raw_date = item.get("date")
            parsed_date = datetime.fromisoformat(raw_date)

            formatted_date = parsed_date.strftime("%Y-%m-%d")

            cleaned.append({
                "name": name,
                "date": formatted_date
            })

        except Exception:
            continue  # skip bad records

    return cleaned