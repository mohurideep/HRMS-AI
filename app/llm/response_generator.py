from app.llm.llm_service import generate

def generate_response(llm, query: str, data: list):

    context = "\n".join([
        f"{item['date']}: {item['name']}"
        for item in data
    ])

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
{context}
"""
        }
    ]

    response = generate(
        messages=messages,
        temperature=0.2,
        max_tokens=300
    )

    return response["choices"][0]["message"]["content"]