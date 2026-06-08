FROM runpod/pytorch:2.1.1-py3.10-cuda12.1.1-devel-ubuntu22.04

# 1. Install system dependencies
RUN apt-get update && apt-get install -y wget git ffmpeg libsm6 libxext6 aria2 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# 2. Clone ComfyUI and install core dependencies
RUN git clone https://github.com/comfyanonymous/ComfyUI.git
WORKDIR /workspace/ComfyUI
RUN pip install -r requirements.txt

# 3. Install RunPod serverless, dotenv, and ControlNet Aux preprocessors
RUN pip install runpod python-dotenv
RUN cd /workspace/ComfyUI/custom_nodes && \
    git clone https://github.com/Fannovel16/comfyui_controlnet_aux.git && \
    cd /workspace/ComfyUI/custom_nodes/comfyui_controlnet_aux && \
    pip install -r requirements.txt

# 4. Copy ONLY the application code (No model downloading!)
COPY .env /workspace/.env
COPY workflow.json /workspace/workflow.json
COPY handler.py /workspace/handler.py
COPY start.sh /workspace/start.sh
RUN chmod +x /workspace/start.sh

# 5. Set entrypoint
WORKDIR /workspace
EXPOSE 8188
ENTRYPOINT ["/workspace/start.sh"]
