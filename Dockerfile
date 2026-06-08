# 1. Use the stable 2.1.1 base (We know this exists)
FROM runpod/pytorch:2.1.1-py3.10-cuda12.1.1-devel-ubuntu22.04

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

# 5. CRITICAL FIX: Upgrade PyTorch to support 'custom_op'
# We use the specific CUDA 12.1 index to match the base image perfectly.
RUN pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 6. Fix NumPy compatibility
RUN pip install "numpy<2.0.0"

# 7. Copy your application files
COPY .env /workspace/.env
COPY workflow.json /workspace/workflow.json
COPY handler.py /workspace/handler.py
COPY start.sh /workspace/start.sh
RUN chmod +x /workspace/start.sh

# 8. Set entrypoint
WORKDIR /workspace
EXPOSE 8188

# Pre-download the 3 tiny ControlNet preprocessor models (~200MB total)
# This prevents them from downloading on every single API request
RUN mkdir -p /workspace/ComfyUI/custom_nodes/comfyui_controlnet_aux/ckpts/lllyasviel/Annotators/ && \
    cd /workspace/ComfyUI/custom_nodes/comfyui_controlnet_aux/ckpts/lllyasviel/Annotators/ && \
    aria2c -x 16 -s 16 -k 1M -q "https://huggingface.co/lllyasviel/Annotators/resolve/main/body_pose_model.pth" && \
    aria2c -x 16 -s 16 -k 1M -q "https://huggingface.co/lllyasviel/Annotators/resolve/main/hand_pose_model.pth" && \
    aria2c -x 16 -s 16 -k 1M -q "https://huggingface.co/lllyasviel/Annotators/resolve/main/facenet.pth"

EXPOSE 8188
ENTRYPOINT ["/workspace/start.sh"]
ENTRYPOINT ["/workspace/start.sh"]
