#!/bin/bash

echo "🔗 Setting up model symlinks from Network Volume..."

# Safety check: Where did RunPod mount the Network Volume?
if [ -d "/runpod-volume/ComfyUI/models/loras" ]; then
    echo "✅ Found models in /runpod-volume. Creating symlink..."
    rm -rf /workspace/ComfyUI/models
    ln -sfn /runpod-volume/ComfyUI/models /workspace/ComfyUI/models
elif [ -d "/workspace/ComfyUI/models/loras" ]; then
    echo "✅ Models are already in /workspace. No symlink needed."
else
    echo "⚠️ WARNING: Could not find models! Check your Network Volume."
    ls -la /runpod-volume
    ls -la /workspace
fi

echo "Starting ComfyUI in the background..."
python /workspace/ComfyUI/main.py --listen 0.0.0.0 --port 8188 --disable-auto-launch &

echo "Waiting for ComfyUI to be ready..."
while ! curl -s http://127.0.0.1:8188 > /dev/null; do
    sleep 2
done
echo "✅ ComfyUI is ready!"

echo "Starting RunPod Handler..."
python /workspace/handler.py
