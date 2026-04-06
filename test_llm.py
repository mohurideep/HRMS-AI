from app.llm import llm

messages = [
    {
        "role": "system",
        "content": """You are an HR assistant.

Rules:
- Answer ONLY using provided data
- Do NOT add extra commentary
- Do NOT ask follow-up questions
- Keep response concise
- Format as bullet points
"""
    },
    {
        "role": "user",
        "content": """What are the holidays?

2025-01-01 - New Year
2025-03-14 - Holi
2025-08-15 - Independence Day
"""
    }
]

output = llm.create_chat_completion(
    messages=messages,
    max_tokens=200,
    temperature=0.1
)

print(output)
print(output["choices"][0]["message"]["content"])