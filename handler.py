import runpod
import json
import urllib.request
import urllib.parse
import time
import base64
import os

WORKFLOW_PATH = "/workspace/workflow.json"
COMFYUI_API_URL = "http://127.0.0.1:8188"
INPUT_DIR = "/workspace/ComfyUI/input/"

os.makedirs(INPUT_DIR, exist_ok=True)

def load_workflow():
    with open(WORKFLOW_PATH, "r") as f:
        data = json.load(f)
    
    # Clean up any accidental trailing spaces in keys (common when copy-pasting)
    cleaned_data = {}
    for k, v in data.items():
        clean_key = str(k).strip()
        if isinstance(v, dict) and "inputs" in v:
            clean_inputs = {}
            for ik, iv in v["inputs"].items():
                clean_inputs[str(ik).strip()] = iv
            v["inputs"] = clean_inputs
        cleaned_data[clean_key] = v
        
    return cleaned_data

def queue_prompt(prompt):
    data = json.dumps({"prompt": prompt}).encode('utf-8')
    req = urllib.request.Request(f"{COMFYUI_API_URL}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"{COMFYUI_API_URL}/view?{url_values}") as response:
        return response.read()

def handler(job):
    job_input = job["input"]
    workflow = load_workflow()
    
    # 1. Handle Base64 Image Input (Node 27: LoadImage)
    if "image_base64" in job_input:
        img_data = base64.b64decode(job_input["image_base64"])
        temp_filename = "api_input_pose.png"
        temp_path = os.path.join(INPUT_DIR, temp_filename)
        
        with open(temp_path, "wb") as f:
            f.write(img_data)
            
        workflow["27"]["inputs"]["image"] = temp_filename

    # 2. Update Positive Prompt (Node 3)
    if "prompt" in job_input:
        workflow["3"]["inputs"]["text"] = job_input["prompt"]
    
    # 3. Update Negative Prompt (Node 4)
    if "negative_prompt" in job_input:
        workflow["4"]["inputs"]["text"] = job_input["negative_prompt"]
        
    # 4. Update Seed (Node 7 for Base, and Node 33 for Upscale)
    if "seed" in job_input:
        seed_val = int(job_input["seed"])
        workflow["7"]["inputs"]["seed"] = seed_val
        workflow["33"]["inputs"]["seed"] = seed_val
        
    # 5. Update LoRA (Node 31)
    if "lora_name" in job_input and job_input["lora_name"] != "None":
        workflow["31"]["inputs"]["lora_name"] = job_input["lora_name"]
        workflow["31"]["inputs"]["strength_model"] = float(job_input.get("lora_strength", 0.8))
        workflow["31"]["inputs"]["strength_clip"] = float(job_input.get("lora_strength", 0.8))
    else:
        workflow["31"]["inputs"]["lora_name"] = "None"

    # 6. Queue the generation
    try:
        prompt_id = queue_prompt(workflow)["prompt_id"]
    except Exception as e:
        return {"error": f"Failed to queue prompt: {str(e)}"}
    
    # 7. Wait for completion
    while True:
        history = json.loads(urllib.request.urlopen(f"{COMFYUI_API_URL}/history/{prompt_id}").read())
        if prompt_id in history:
            break
        time.sleep(1)
        
    # 8. Get the upscaled image (Node 35)
    try:
        output_info = history[prompt_id]["outputs"]["35"]["images"][0]
        image_data = get_image(output_info["filename"], output_info["subfolder"], output_info["type"])
        
        return {
            "image_base64": base64.b64encode(image_data).decode('utf-8'),
            "prompt_id": prompt_id,
            "status": "success"
        }
    except Exception as e:
        return {"error": f"Failed to retrieve image: {str(e)}"}

if __name__ == "__main__":
    print("🚀 Starting RunPod Serverless Handler...")
    runpod.serverless.start({"handler": handler})
