import os
import urllib.request
import json
import subprocess
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("CIVITAI_API_KEY", "")

BASE_API_URL = "https://civitai.red/api/download/models"
LORA_FOLDER = "/workspace/ComfyUI/models/loras/"
CHECKPOINT_FOLDER = "/workspace/ComfyUI/models/checkpoints/"
CONTROLNET_FOLDER = "/workspace/ComfyUI/models/controlnet/"

os.makedirs(LORA_FOLDER, exist_ok=True)
os.makedirs(CHECKPOINT_FOLDER, exist_ok=True)
os.makedirs(CONTROLNET_FOLDER, exist_ok=True)

LORA_MODELS = [
    "1602909", "996220", "1837939", "2006381", "1659625", "1729904", 
    "1646900", "1256683", "1477075", "1385116", "553648", "779355"
]
CHECKPOINT_MODELS = ["2047770", "1359028"]

def get_version_id(model_id):
    try:
        metadata_url = f"https://civitai.com/api/v1/models/{model_id}?token={API_KEY}"
        req = urllib.request.Request(metadata_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            model_data = json.loads(response.read().decode('utf-8'))
        if not model_data.get('modelVersions'):
            return None
        return str(model_data['modelVersions'][0]['id'])
    except Exception as e:
        print(f"Error fetching ID for {model_id}: {e}")
        return None

def download_model(version_id, destination_path):
    try:
        download_url = f"{BASE_API_URL}/{version_id}?token={API_KEY}"
        req = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            content_disp = response.info().get('Content-Disposition')
            filename = content_disp.split("filename=")[1].strip('"\'') if content_disp and "filename=" in content_disp else f"model_{version_id}.safetensors"
            
            final_path = os.path.join(destination_path, filename)
            print(f"Downloading {filename}...")
            
            with open(final_path, 'wb') as f:
                while True:
                    buffer = response.read(10 * 1024 * 1024) # 10MB chunks
                    if not buffer: break
                    f.write(buffer)
            print(f"✅ Saved to {final_path}")
    except Exception as e:
        print(f"❌ Error downloading: {e}")

print("--- Downloading LoRAs ---")
for model_id in LORA_MODELS:
    vid = get_version_id(model_id)
    if vid: download_model(vid, LORA_FOLDER)

print("--- Downloading Checkpoints ---")
for model_id in CHECKPOINT_MODELS:
    vid = get_version_id(model_id)
    if vid: download_model(vid, CHECKPOINT_FOLDER)

print("--- Downloading ControlNets ---")
print("Downloading Depth ControlNet...")
subprocess.run(["wget", "-c", "https://huggingface.co/xinsir/controlnet-depth-sdxl-1.0/resolve/main/diffusion_pytorch_model.safetensors", "-O", os.path.join(CONTROLNET_FOLDER, "controlnet-depth-sdxl-1.0.safetensors")])

print("Downloading OpenPose ControlNet...")
subprocess.run(["wget", "-c", "https://huggingface.co/windsingai/Illustrious-XL-openpose-test/resolve/main/openpose_s6000.safetensors", "-O", os.path.join(CONTROLNET_FOLDER, "controlnet-openpose-illustrious-xl.safetensors")])

print("🎉 All models downloaded successfully!")
