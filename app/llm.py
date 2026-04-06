from llama_cpp import Llama
import json

MODEL_PATH = r"models\gemma\gemma-4-e2b-it-Q8_0.gguf"

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    n_threads=4
)

#Intent Function
def get_intent(query: str):
    messages = [
        {
            "role": "system",
            "content": """You are an HRMS intent classifier.

Available intents:
- get_holidays

Rules:
- Return valid JSON only
- Do not include explanations or markdown
- Use this exact schema: {"intent": "<intent_name_or_unknown>"}
- If the user is asking about holidays, leave, festival holidays, company holidays, public holidays, or holiday calendar, return {"intent": "get_holidays"}
- If the request does not match an available intent, return {"intent": "unknown"}"""
        },
        {
            "role": "user",
            "content": query.strip()
        }
    ]

    output = llm.create_chat_completion(
        messages=messages,
        max_tokens=64,
        temperature=0.0
    )
    text = output.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

    try:
        parsed = json.loads(text)
        if parsed.get("intent") in {"get_holidays", "unknown"}:
            return json.dumps(parsed)
    except json.JSONDecodeError:
        pass

    normalized_query = query.lower()
    if any(keyword in normalized_query for keyword in ["holiday", "holidays", "festival", "public holiday", "holiday calendar"]):
        return json.dumps({"intent": "get_holidays"})

    return json.dumps({"intent": "unknown"})

def generate_answer(query: str, data: dict):
    context = "\n".join([
        f"{item['date']}: {item['name']}"
        for item in data
    ])

    messages = [
        {
            "role": "system",
            "content": """You are an HR assistant.

            Rules:
            - Answer using provided data only
            - Format response in a clear, user-friendly way
            - Group by year if multiple years exist
            - Use bullet points
            - Do NOT return JSON
            - Do NOT include extra explanations
            """
        },
        {
            "role": "user",
            "content": f"""
            Query: {query}
            Holidays data:
            {context}
            Generate a clean, readable response.
            """
        }
    ]

    output = llm.create_chat_completion(
        messages=messages,
        max_tokens=get_max_tokens(messages),
        temperature=0.0
    )
    text = output.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    return text

# Helper function to set dynamic token allocation
def get_max_tokens(message):
    approx_input_token = sum(len(part["content"]) for part in message) // 4  # Approximate input tokens
    return min(512, 2048 - approx_input_token)
