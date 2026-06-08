# 1. Use the 2.2.0 base image (We know this tag exists and builds successfully)
FROM runpod/pytorch:2.2.0-py3.10-cuda12.1.1-devel-ubuntu22.04

# 2. Install system dependencies
RUN apt-get update && apt-get install -y wget git ffmpeg libsm6 libxext6 aria2 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# 3. Clone ComfyUI and install core dependencies
RUN git clone https://github.com/comfyanonymous/ComfyUI.git
WORKDIR /workspace/ComfyUI
RUN pip install -r requirements.txt

# 4. Install RunPod, dotenv, and ControlNet Aux
RUN pip install runpod python-dotenv
RUN cd /workspace/ComfyUI/custom_nodes && \
    git clone https://github.com/Fannovel16/comfyui_controlnet_aux.git && \
    cd /workspace/ComfyUI/custom_nodes/comfyui_controlnet_aux && \
    pip install -r requirements.txt

# 5. CRITICAL FIX: Force upgrade PyTorch
# The custom nodes above silently downgraded PyTorch to 2.1.x, causing the custom_op error.
# We force upgrade it here to the latest 2.x version to restore the custom_op feature.
RUN pip install --upgrade torch torchvision torchaudio

# 6. Fix NumPy compatibility
RUN pip install "numpy<2.0.0"

# 7. Copy ONLY the application code
COPY .env /workspace/.env
COPY workflow.json /workspace/workflow.json
COPY handler.py /workspace/handler.py
COPY start.sh /workspace/start.sh
RUN chmod +x /workspace/start.sh

# 8. Set entrypoint
WORKDIR /workspace
EXPOSE 8188
ENTRYPOINT ["/workspace/start.sh"]
