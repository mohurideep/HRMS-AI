from app.llm.llm_service import generate

def generate_response(query: str, data: list):

    # context = "\n".join([
    #     f"{item['date']}: {item['name']}"
    #     for item in data
    # ])

    messages = [
        {
            "role": "system",
            "content": """You are an HR assistant.

Rules:
- Answer using ONLY provided data
- Format response clearly
- Group by year if needed
- No hallucination
"""
        },
        {
            "role": "user",
            "content": f"""
Query: {query}

Data:
{data}
"""
        }
    ]

    response = generate(
        messages=messages,
        temperature=0.2,
        max_tokens=get_max_tokens(messages)
    )

    return response.strip()


# Helper function to set dynamic token allocation
def get_max_tokens(message):
     approx_input_token = sum(len(part["content"]) for part in message) // 4  # Approximate input tokens
     return max(512, 2048 - approx_input_token)