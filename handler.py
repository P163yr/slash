import runpod
import json
import urllib.request
import urllib.parse
import time
import base64
import os
from PIL import Image

WORKFLOW_PATH = "/workspace/workflow.json"
COMFYUI_API_URL = "http://127.0.0.1:8188"
INPUT_DIR = "/workspace/ComfyUI/input/"

os.makedirs(INPUT_DIR, exist_ok=True)

# Create a fallback image once, so the workflow never breaks if no image is provided
FALLBACK_IMAGE = os.path.join(INPUT_DIR, "fallback_pose.png")
if not os.path.exists(FALLBACK_IMAGE):
    fallback_img = Image.new('RGB', (512, 512), color=(128, 128, 128))
    fallback_img.save(FALLBACK_IMAGE)

def load_workflow():
    with open(WORKFLOW_PATH, "r") as f:
        data = json.load(f)
    
    # Clean keys (removes trailing spaces that cause KeyError)
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
    
    # 1. Smart Image Handling (Node 27)
    if "image_base64" in job_input and job_input["image_base64"]:
        # User provided an image: Decode and save it
        img_data = base64.b64decode(job_input["image_base64"])
        temp_filename = "api_input_pose.png"
        temp_path = os.path.join(INPUT_DIR, temp_filename)
        with open(temp_path, "wb") as f:
            f.write(img_data)
        workflow["27"]["inputs"]["image"] = temp_filename
        
        # Default ControlNet strength to 0.8 if not specified
        if "controlnet_strength" not in job_input:
            workflow["22"]["inputs"]["strength"] = 0.8
    else:
        # No image provided: Use fallback and DISABLE ControlNet for pure Text-to-Image
        workflow["27"]["inputs"]["image"] = "fallback_pose.png"
        workflow["22"]["inputs"]["strength"] = 0.0

    # 2. Checkpoint (Node 6)
    if "checkpoint_name" in job_input:
        workflow["6"]["inputs"]["ckpt_name"] = job_input["checkpoint_name"]

    # 3. Prompts (Node 3 & 4)
    if "prompt" in job_input:
        workflow["3"]["inputs"]["text"] = job_input["_prompt"] if "_prompt" in job_input else job_input["prompt"] # Fallback safety
    if "prompt" in job_input:
        workflow["3"]["inputs"]["text"] = job_input["prompt"]
    if "negative_prompt" in job_input:
        workflow["4"]["inputs"]["text"] = job_input["negative_prompt"]
        
    # 4. Resolution (Node 5)
    if "width" in job_input:
        workflow["5"]["inputs"]["width"] = int(job_input["width"])
    if "height" in job_input:
        workflow["5"]["inputs"]["height"] = int(job_input["height"])

    # 5. Sampling Params (Node 7 & 33)
    if "seed" in job_input:
        seed_val = int(job_input["seed"])
        workflow["7"]["inputs"]["seed"] = seed_val
        workflow["33"]["inputs"]["seed"] = seed_val
    if "steps" in job_input:
        workflow["7"]["inputs"]["steps"] = int(job_input["steps"])
        workflow["33"]["inputs"]["steps"] = int(job_input["steps"])
    if "cfg" in job_input:
        workflow["7"]["inputs"]["cfg"] = float(job_input["cfg"])
        workflow["33"]["inputs"]["cfg"] = float(job_input["cfg"])
    if "denoise" in job_input:
        workflow["33"]["inputs"]["denoise"] = float(job_input["denoise"])

    # 6. LoRA (Node 31)
    if "lora_name" in job_input:
        workflow["31"]["inputs"]["lora_name"] = job_input["lora_name"]
    if "lora_strength" in job_input:
        strength = float(job_input["lora_strength"])
        workflow["31"]["inputs"]["strength_model"] = strength
        workflow["31"]["inputs"]["strength_clip"] = strength

    # 7. ControlNet Model & Preprocessor (Node 23 & 24)
    if "controlnet_model" in job_input:
        workflow["23"]["inputs"]["control_net_name"] = job_input["controlnet_model"]
    if "controlnet_strength" in job_input and "image_base64" in job_input:
        workflow["22"]["inputs"]["strength"] = float(job_input["controlnet_strength"])
    if "preprocessor" in job_input:
        workflow["24"]["inputs"]["preprocessor"] = job_input["preprocessor"]
    if "preprocessor_resolution" in job_input:
        workflow["24"]["inputs"]["resolution"] = int(job_input["preprocessor_resolution"])

    # 8. Queue and wait
    try:
        prompt_id = queue_prompt(workflow)["prompt_id"]
    except Exception as e:
        return {"error": f"Failed to queue prompt: {str(e)}"}
    
    while True:
        history = json.loads(urllib.request.urlopen(f"{COMFYUI_API_URL}/history/{prompt_id}").read())
        if prompt_id in history:
            break
        time.sleep(1)
        
    # 9. Get the upscaled image (Node 35)
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
