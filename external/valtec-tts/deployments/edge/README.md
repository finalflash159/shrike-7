# Valtec Vietnamese TTS - Edge Deployment

🎙️ **Lightweight Vietnamese Text-to-Speech using ONNX Runtime**

Optimized for edge devices, embedded systems, and lightweight deployment.

**✨ Auto-downloads models from HuggingFace Hub** on first run - no manual setup required!

## Features

- ✅ Pure Python ONNX inference (no PyTorch required)
- ✅ Vietnamese Grapheme-to-Phoneme (G2P) conversion
- ✅ CPU and CUDA execution support
- ✅ Five voice options: NF, SF, NM1, SM, NM2 (Northern/Southern, Male/Female)
- ✅ Adjustable speech speed
- ✅ Minimal dependencies
- ✅ Auto-download from HuggingFace Hub

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Inference

Models will be automatically downloaded from [valtecAI-team/valtec-tts-onnx](https://huggingface.co/valtecAI-team/valtec-tts-onnx) on first run.

```bash
# Basic usage (Southern Female voice)
python inference.py --text "Xin chào Việt Nam"

# Northern Male 1 voice
python inference.py --text "Xin chào Việt Nam" --speaker 2

# Southern Male
python inference.py --text "Xin chào" --speaker 3

# Custom output file
python inference.py --text "Xin chào" --output my_audio.wav

# Adjust speed (slower)
python inference.py --text "Xin chào" --speed 1.2

# Use GPU
python inference.py --text "Xin chào" --device cuda
```

### 3. Python API

```python
from inference import VietnameTTSEdge

# Initialize (auto-downloads models)
tts = VietnameTTSEdge(device='cpu')

# Synthesize
audio, sample_rate = tts.synthesize(
    text="Xin chào, tôi là một trợ lý ảo",
    speaker_id=1,      # 0=NF, 1=SF, 2=NM1, 3=SM, 4=NM2
    length_scale=1.0   # speech speed
)

# Save to file
import soundfile as sf
sf.write('output.wav', audio, sample_rate)
```

## Command Line Options

| Argument | Default | Description |
|----------|---------|-------------|
| `--text` | "Hello..." | Vietnamese text to synthesize |
| `--model-dir` | Auto-download | Path to ONNX models (optional, auto-downloads from HF Hub) |
| `--output` | `output.wav` | Output audio file |
| `--speaker` | `1` | Speaker ID: 0=NF, 1=SF, 2=NM1, 3=SM, 4=NM2 |
| `--speed` | `1.0` | Speech speed (>1 slower, <1 faster) |
| `--device` | `cpu` | Execution device (`cpu` or `cuda`) |

## Model Files

### Auto-Download (Recommended)
Models are automatically downloaded from [HuggingFace Hub](https://huggingface.co/valtecAI-team/valtec-tts-onnx) and cached locally:

- **Windows**: `%LOCALAPPDATA%\valtec_tts\onnx_models\`
- **Linux/Mac**: `~/.cache/valtec_tts/onnx_models/`

### Manual Download (Optional)
If you prefer to use local models:

```bash
# Download manually or use existing ../../pretrained/onnx/ folder
python inference.py --model-dir /path/to/onnx/models
```

### Required Files
The following ONNX files are needed:

```
onnx_models/
├── text_encoder.onnx       # Text encoder network
├── duration_predictor.onnx # Duration prediction
├── flow.onnx               # Flow network
├── decoder.onnx            # Audio decoder (HiFi-GAN)
└── tts_config.json         # Model configuration
```

## Performance

| Device | Realtime Factor | Memory Usage |
|--------|-----------------|--------------| 
| CPU (Intel i7) | ~3x realtime | ~500MB |
| GPU (RTX 3060) | ~15x realtime | ~1GB |
| Raspberry Pi 4 | ~0.5x realtime | ~300MB |

*Realtime factor > 1 means faster than realtime*

## Integration Examples

### Flask Web Server

```python
from flask import Flask, request, send_file
from inference import VietnameTTSEdge
import io
import soundfile as sf

app = Flask(__name__)
tts = VietnameTTSEdge()  # Auto-downloads models

@app.route('/tts', methods=['POST'])
def synthesize():
    text = request.json.get('text', '')
    audio, sr = tts.synthesize(text)
    
    buffer = io.BytesIO()
    sf.write(buffer, audio, sr, format='WAV')
    buffer.seek(0)
    
    return send_file(buffer, mimetype='audio/wav')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Batch Processing

```python
from inference import VietnameTTSEdge
import soundfile as sf

tts = VietnameTTSEdge()

texts = [
    "Xin chào tôi là một trợ lý ảo",
    "Xin chào tôi là một trợ lý ảo",
    "Xin chào tôi là một trợ lý ảo",
]

for i, text in enumerate(texts):
    audio, sr = tts.synthesize(text)
    sf.write(f'output_{i:03d}.wav', audio, sr)
    print(f'Generated: output_{i:03d}.wav')
```

## Troubleshooting

### OOM Error on GPU
Try using CPU instead:
```bash
python inference.py --device cpu
```

### Missing ONNX Models
Ensure all 4 ONNX files exist. The auto-download should handle this, but if it fails:
```bash
# Manually download from HuggingFace
huggingface-cli download valtecAI-team/valtec-tts-onnx --local-dir ./models
python inference.py --model-dir ./models
```

### Audio Quality Issues
- Adjust `noise_scale` parameter (lower = more stable, higher = more variation)
- Check input text normalization

## License

This project is part of Valtec TTS. See main repository for license details.

---

**Powered by Valtec AI Team** | ONNX Runtime
