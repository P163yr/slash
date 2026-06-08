#!/bin/bash

echo "🔗 Setting up model symlinks from Network Volume..."

# 1. CRITICAL: Remove the existing empty 'models' directory created during Docker build.
# If we don't delete it, 'ln' will fail or create a broken nested link.
rm -rf /workspace/ComfyUI/models

# 2. Intelligently find where the models are located in the Network Volume
if [ -d "/runpod-volume/loras" ]; then
    echo "✅ Found models at the root of the Network Volume."
    ln -s /runpod-volume /workspace/ComfyUI/models
elif [ -d "/runpod-volume/ComfyUI/models/loras" ]; then
    echo "✅ Found models inside a ComfyUI/models folder in the Network Volume."
    ln -s /runpod-volume/ComfyUI/models /workspace/ComfyUI/models
else
    echo "⚠️ WARNING: Could not automatically find the models in /runpod-volume!"
    echo "Listing contents of /runpod-volume to help debug:"
    ls -la /runpod-volume
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
