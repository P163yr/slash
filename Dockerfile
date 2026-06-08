FROM runpod/pytorch:2.1.1-py3.10-cuda12.1.1-devel-ubuntu22.04

# 1. Install system dependencies (ADDED aria2 for parallel downloads)
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

# =========================================================
# 4. DOWNLOAD MODELS FIRST (This layer will now be CACHED!)
# =========================================================
COPY .env /workspace/.env
COPY download_models.py /workspace/download_models.py

WORKDIR /workspace
# This will now run 5x-10x faster and finish well under 30 minutes
RUN python download_models.py

# =========================================================
# 5. COPY APPLICATION CODE (Changes here won't trigger re-downloads)
# =========================================================
COPY workflow.json /workspace/workflow.json
COPY handler.py /workspace/handler.py
COPY start.sh /workspace/start.sh
RUN chmod +x /workspace/start.sh

# 6. Set entrypoint
WORKDIR /workspace
EXPOSE 8188
ENTRYPOINT ["/workspace/start.sh"]
