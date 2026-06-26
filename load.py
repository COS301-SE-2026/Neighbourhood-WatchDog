from huggingface_hub import hf_hub_download

path = hf_hub_download(
    repo_id="Subh775/Threat-Detection-YOLOv8n",
    filename="weights/best.pt",
    local_dir="ai/pipeline/models/weights/"

)

print(f"Downloaded to: {path}")