# UPGRADED to PyTorch 2.2.2 to support torch.library.custom_op
FROM runpod/pytorch:2.2.2-py3.10-cuda12.1.1-devel-ubuntu22.04

# 1. Install system dependencies
RUN apt-get update && apt-get install -y wget git ffmpeg libsm6 libxext6 aria2 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# 2. Clone ComfyUI and install core dependencies
RUN git clone https://github.com/comfyanonymous/ComfyUI.git
WORKDIR /workspace/ComfyUI
RUN pip install -r requirements.txt

# 3. FIX NUMPY 2.x COMPATIBILITY: Force downgrade to NumPy 1.x
RUN pip install "numpy<2.0.0"

# 4. Install RunPod serverless, dotenv, and ControlNet Aux preprocessors
RUN pip install runpod python-dotenv
RUN cd /workspace/ComfyUI/custom_nodes && \
    git clone https://github.com/Fannovel16/comfyui_controlnet_aux.git && \
    cd /workspace/ComfyUI/custom_nodes/comfyui_controlnet_aux && \
    pip install -r requirements.txt && \
    pip install "numpy<2.0.0"

# 5. Copy ONLY the application code (No model downloading!)
COPY .env /workspace/.env
COPY workflow.json /workspace/workflow.json
COPY handler.py /workspace/handler.py
COPY start.sh /workspace/start.sh
RUN chmod +x /workspace/start.sh

# 6. Set entrypoint
WORKDIR /workspace
EXPOSE 127.0.0.1:8188
ENTRYPOINT ["/workspace/start.sh"]
