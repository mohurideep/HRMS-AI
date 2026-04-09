import logging
import threading
import time

from app.llm.llm import get_llm

_llm_lock = threading.Lock()

LLM_PROFILES = {
    "tool_call": {
        "min_ctx": 2048,
        "max_ctx": 4096,
        "min_output_tokens": 32,
        "max_output_tokens": 128,
        "reserved_tokens": 256,
    },
    "response_generation": {
        "min_ctx": 4096,
        "max_ctx": 8192,
        "min_output_tokens": 256,
        "max_output_tokens": 2048,
        "reserved_tokens": 768,
    },
}


def _estimate_tokens(messages) -> int:
    total_chars = 0
    for message in messages:
        total_chars += len(str(message.get("role", "")))
        total_chars += len(str(message.get("content", "")))
    return max(1, total_chars // 4)


def _round_ctx_size(required_ctx: int, profile: dict) -> int:
    for candidate in (2048, 4096, 8192, 16384):
        if candidate >= required_ctx:
            return min(candidate, profile["max_ctx"])
    return profile["max_ctx"]


def resolve_generation_config(messages, profile_name: str, max_tokens: int | None = None) -> dict:
    profile = LLM_PROFILES.get(profile_name, LLM_PROFILES["response_generation"])
    input_tokens = _estimate_tokens(messages)

    if max_tokens is None:
        available_output = profile["max_ctx"] - input_tokens - profile["reserved_tokens"]
        max_tokens = max(profile["min_output_tokens"], available_output)

    max_tokens = min(max_tokens, profile["max_output_tokens"])
    required_ctx = input_tokens + max_tokens + profile["reserved_tokens"]
    ctx_size = _round_ctx_size(max(required_ctx, profile["min_ctx"]), profile)

    if input_tokens + max_tokens >= ctx_size:
        adjusted_max_tokens = ctx_size - input_tokens - max(128, profile["reserved_tokens"] // 2)
        max_tokens = max(profile["min_output_tokens"], adjusted_max_tokens)

    return {
        "input_tokens": input_tokens,
        "max_tokens": max_tokens,
        "ctx_size": ctx_size,
        "profile": profile_name,
    }


def generate(
    messages,
    max_tokens: int | None = None,
    temperature: float = 0.2,
    profile_name: str = "response_generation"
):
    """
    Central LLM call (thread-safe) with dynamic context and token sizing.
    """

    config = resolve_generation_config(messages, profile_name, max_tokens=max_tokens)
    llm = get_llm(required_ctx=config["ctx_size"])
    start_time = time.time()

    try:
        with _llm_lock:
            logging.info(
                "LLM call started | profile=%s input_tokens=%s max_tokens=%s ctx=%s",
                config["profile"],
                config["input_tokens"],
                config["max_tokens"],
                config["ctx_size"],
            )

            response = llm.create_chat_completion(
                messages=messages,
                max_tokens=config["max_tokens"],
                temperature=temperature
            )

            content = response["choices"][0]["message"]["content"]
            duration = time.time() - start_time
            logging.info("LLM call completed | latency=%.3fs", duration)

            return content

    except Exception as e:
        logging.exception("LLM call failed")
        raise Exception(f"LLM Error: {str(e)}")
