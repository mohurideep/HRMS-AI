from app.llm.llm import get_llm
import threading
import logging

# global lock to prevent concurrent access
_llm_lock = threading.Lock()

def generate(messages, max_tokens=200, temperature=0.2):
    """
    Central LLM call (thread-safe)
    """

    llm = get_llm()

    try:
        with _llm_lock:
            logging.info("🧠 LLM call started")

            response = llm.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            content = response["choices"][0]["message"]["content"]

            logging.info("✅ LLM call completed")

            return content

    except Exception as e:
        logging.exception("❌ LLM call failed")
        raise Exception(f"LLM Error: {str(e)}")