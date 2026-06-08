FROM runpod/pytorch:2.1.1-py3.10-cuda12.1.1-devel-ubuntu22.04

# Install system dependencies
RUN apt-get update && apt-get install -y wget git ffmpeg libsm6 libxext6 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Clone ComfyUI and install dependencies
RUN git clone https://github.com/comfyanonymous/ComfyUI.git
WORKDIR /workspace/ComfyUI
RUN pip install -r requirements.txt

# Install RunPod and ControlNet Aux (required for your preprocessors)
RUN pip install runpod python-dotenv
RUN cd custom_nodes && \
    git clone https://github.com/Fannovel16/comfyui_controlnet_aux.git && \
    cd ..

# Copy your project files
COPY .env .env
COPY workflow.json /workspace/workflow.json
COPY handler.py /workspace/handler.py
COPY start.sh /workspace/start.sh
RUN chmod +x /workspace/start.sh

EXPOSE 8188
ENTRYPOINT ["/workspace/start.sh"]
