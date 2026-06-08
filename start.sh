#!/bin/bash

echo "🔗 Setting up model symlinks from Network Volume..."
mkdir -p /runpod-volume/ComfyUI/models
ln -sfn /runpod-volume/ComfyUI/models /workspace/ComfyUI/models

echo "Starting ComfyUI in the background..."
python /workspace/ComfyUI/main.py --listen 0.0.0.0 --port 8188 --disable-auto-launch &

echo "Waiting for ComfyUI to be ready..."
while ! curl -s http://127.0.0.1:8188 > /dev/null; do
    sleep 2
done
echo "✅ ComfyUI is ready!"

echo "Starting RunPod Handler..."
python /workspace/handler.py
