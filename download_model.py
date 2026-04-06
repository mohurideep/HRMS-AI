# download_model.py
from huggingface_hub import list_repo_files

files = list_repo_files("ggml-org/gemma-4-E2B-it-GGUF")

for f in files:
    print(f)

# from huggingface_hub import hf_hub_download

# model_path = hf_hub_download(
#     repo_id="ggml-org/gemma-4-E2B-it-GGUF",
#     filename="gemma-4-e2b-it.Q4_K_M.gguf"
# )

# print("Model downloaded at:", model_path)