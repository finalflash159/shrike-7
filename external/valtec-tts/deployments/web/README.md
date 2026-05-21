# Valtec Vietnamese TTS - Web Demo

🎙️ **Vietnamese Text-to-Speech running entirely in the browser**

Full browser-based TTS using ONNX Runtime Web, no backend server required.

## Demo

### 🌐 Live Web Demo

![Web TTS Demo](../../examples/ValtecTTS%20-%20WEB.mp4)

*Real-time Vietnamese TTS running entirely in browser using ONNX Runtime Web*

## Features

- ✅ **Full Browser Inference**: Runs entirely in browser, no backend needed
- ✅ **Vietnamese G2P**: Accurate text-to-phoneme conversion using viphoneme
- ✅ **5 Voice Options**: NF, SF, NM1, SM, NM2 (Northern/Southern, Male/Female)
- ✅ **ONNX Runtime Web**: WebAssembly-powered inference
- ✅ **Modern UI**: Beautiful glassmorphism design
- ✅ **Models from HF Hub**: Download from valtecAI-team/valtec-tts-onnx

## Quick Start

### 1. Download ONNX Models

**Option A: Download from HuggingFace Hub (Recommended)**
```bash
# From project root
huggingface-cli download valtecAI-team/valtec-tts-onnx --local-dir pretrained/onnx
```

**Option B: Export from pretrained model**
```bash
python export_full_onnx.py  # From project root
```

### 2. Start HTTP Server

```bash
# From project root
npx -y http-server . -p 8080 -c-1

# Or use Python
python -m http.server 8080
```

### 3. Open Browser

Navigate to: **http://localhost:8080/deployments/web/**

### 4. Usage

1. Enter Vietnamese text in the text box
2. Select voice (NF/SF/NM1/SM/NM2)
3. Click **"Tạo giọng nói"**
4. Wait for processing and listen to audio

## Project Structure

```
web/
├── index.html           # Web interface + ONNX inference logic
├── vietnamese_g2p.js    # Vietnamese G2P converter (ported from viphoneme)
└── README.md            # This file

../../pretrained/onnx/   # Model files (download from HF Hub)
├── text_encoder.onnx
├── duration_predictor.onnx
├── flow.onnx
├── decoder.onnx
└── tts_config.json
```

## Model Files

Models downloaded from [valtecAI-team/valtec-tts-onnx](https://huggingface.co/valtecAI-team/valtec-tts-onnx):

| File | Size | Description |
|------|------|-------------|
| `text_encoder.onnx` | ~28 MB | Text encoder network |
| `duration_predictor.onnx` | ~27 MB | Duration prediction |
| `flow.onnx` | ~83 MB | Flow network |
| `decoder.onnx` | ~27 MB | HiFi-GAN decoder |
| `tts_config.json` | ~10 KB | Config & symbol mapping |

**Total: ~165 MB** (first load)

## Vietnamese G2P

The `vietnamese_g2p.js` file is a JavaScript port of the Python `viphoneme` library:

- Converts text → IPA phonemes
- Handles special cases correctly (gi, qu, ngh...)
- Accurate tone mapping
- Achieves **99.96% accuracy** compared to Python viphoneme

## Browser Support

| Browser | Support |
|---------|---------|
| Chrome 90+ | ✅ Full |
| Firefox 90+ | ✅ Full |
| Edge 90+ | ✅ Full |
| Safari 15+ | ⚠️ Limited |

## Troubleshooting

### Model Loading Error
- Ensure serving via HTTP server (not file://)
- Check path `../../pretrained/onnx/` exists

### Audio Not Playing
- Check browser allows autoplay
- Try clicking page before generating

### Slow First Load
- Models need to load ~165MB on first run
- Subsequent loads will be cached by browser

---

**Powered by Valtec AI Team** | ONNX Runtime Web
