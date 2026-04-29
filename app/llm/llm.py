from llama_cpp import Llama

DEFAULT_CTX = 4096

llm_instance = None
llm_model_path = None
llm_ctx_size = 0


def _build_llm(model_path: str, n_ctx: int):
    print(f"Loading LLM with context window {n_ctx}...")
    instance = Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_threads=6,
        n_batch=128,
        verbose=False
    )
    print("LLM Loaded")
    return instance


def load_llm(model_path: str, n_ctx: int = DEFAULT_CTX):
    global llm_instance, llm_model_path, llm_ctx_size

    llm_model_path = model_path

    if llm_instance is None or n_ctx > llm_ctx_size:
        llm_instance = _build_llm(model_path, n_ctx)
        llm_ctx_size = n_ctx

    return llm_instance


def get_llm(required_ctx: int | None = None):
    if llm_model_path is None:
        raise Exception("LLM model path not configured")
    MIN_CTX = 1024
    MAX_CTX = 4096
    target_ctx = required_ctx or DEFAULT_CTX
    target_ctx = max(MIN_CTX, min(target_ctx, MAX_CTX))

    if llm_instance is None or target_ctx > llm_ctx_size:
        return load_llm(llm_model_path, target_ctx)

    return llm_instance
