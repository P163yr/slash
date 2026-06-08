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
    
    # 1. Image Input (Node 27)
    if "image_base64" in job_input:
        img_data = base64.b64decode(job_input["image_base64"])
        temp_filename = "api_input_pose.png"
        temp_path = os.path.join(INPUT_DIR, temp_filename)
        with open(temp_path, "wb") as f:
            f.write(img_data)
        workflow["27"]["inputs"]["image"] = temp_filename

    # 2. Prompts (Node 3 & 4)
    if "prompt" in job_input:
        workflow["3"]["inputs"]["text"] = job_input["prompt"]
    if "negative_prompt" in job_input:
        workflow["4"]["inputs"]["text"] = job_input["negative_prompt"]
        
    # 3. Resolution (Node 5)
    if "width" in job_input:
        workflow["5"]["inputs"]["width"] = int(job_input["width"])
    if "height" in job_input:
        workflow["5"]["inputs"]["height"] = int(job_input["height"])

    # 4. Sampling Params (Node 7 & 33)
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

    # 5. LoRA (Node 31)
    if "lora_name" in job_input:
        workflow["31"]["inputs"]["lora_name"] = job_input["lora_name"]
    if "lora_strength" in job_input:
        strength = float(job_input["lora_strength"])
        workflow["31"]["inputs"]["strength_model"] = strength
        workflow["31"]["inputs"]["strength_clip"] = strength

    # 6. ControlNet Model & Strength (Node 23 & 22)
    if "controlnet_model" in job_input:
        workflow["23"]["inputs"]["control_net_name"] = job_input["controlnet_model"]
    if "controlnet_strength" in job_input:
        workflow["22"]["inputs"]["strength"] = float(job_input["controlnet_strength"])

    # 7. Preprocessor (Node 24)
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
