from app.llm.llm_service import generate


def generate_response(query: str, data: list):
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
        temperature=0.1,
        profile_name="response_generation"
    )

    return response.strip()
