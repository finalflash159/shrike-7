# Valtec Vietnamese TTS - Android Demo

🎙️ **Vietnamese Text-to-Speech Android App using ONNX Runtime**

On-device Vietnamese TTS application running directly on Android devices.

## Demo

### 📱 Android App Demo

![Android TTS Demo](../../examples/ValtecTTS%20-%20Android.mp4)

*Demonstrating 5-voice Vietnamese TTS on Xiaomi 12S Pro with real-time synthesis*

## Features

- ✅ **On-device Inference**: Runs entirely on device, no internet required
- ✅ **ONNX Runtime Mobile**: Fast and battery-efficient inference
- ✅ **Vietnamese G2P**: Text-to-phoneme conversion
- ✅ **5 Voice Options**: NF, SF, NM1, SM, NM2 (Northern/Southern, Male/Female)
- ✅ **Modern UI**: Material Design interface
- ✅ **Models from HF Hub**: Download from valtecAI-team/valtec-tts-onnx

## Requirements

- Android Studio Arctic Fox (2020.3.1) or later
- Android SDK 26+ (Android 8.0 Oreo)
- ~300MB RAM for inference

## Build Instructions

### 1. Download ONNX Models

**Download from HuggingFace Hub:**
```bash
# From project root (valtec-tts/)
huggingface-cli download valtecAI-team/valtec-tts-onnx --local-dir pretrained/onnx
```

**Or export from pretrained model:**
```bash
python export_full_onnx.py
```

### 2. Copy Models to Android Assets

```bash
# Copy ONNX files to Android assets
cp ../../pretrained/onnx/*.onnx app/src/main/assets/
cp ../../pretrained/onnx/tts_config.json app/src/main/assets/
```

### 3. Open in Android Studio

```bash
# Open the android folder in Android Studio
# File -> Open -> Select deployments/android/ folder
```

### 4. Build APK

**Via Android Studio:**
- Build > Build Bundle(s) / APK(s) > Build APK(s)

**Via Command Line:**
```bash
./gradlew assembleDebug

# APK will be at: app/build/outputs/apk/debug/app-debug.apk
```

### 5. Install on Device

```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

## Project Structure

```
android/
├── app/
│   ├── src/main/
│   │   ├── java/com/valtec/tts/
│   │   │   ├── MainActivity.kt         # Main activity
│   │   │   ├── ValtecTTSEngine.kt      # ONNX inference engine
│   │   │   └── VietnameseG2P.kt        # Vietnamese G2P converter
│   │   ├── assets/                      # ONNX models (copy here)
│   │   │   ├── text_encoder.onnx
│   │   │   ├── duration_predictor.onnx
│   │   │   ├── flow.onnx
│   │   │   ├── decoder.onnx
│   │   │   └── tts_config.json
│   │   └── res/                         # UI resources
│   └── build.gradle
└── build.gradle
```

## Dependencies

Key dependencies (defined in `app/build.gradle`):

```gradle
implementation 'com.microsoft.onnxruntime:onnxruntime-android:1.16.0'
implementation 'androidx.core:core-ktx:1.12.0'
implementation 'androidx.appcompat:appcompat:1.6.1'
implementation 'com.google.android.material:material:1.11.0'
```

## Usage

1. Launch the app on your Android device
2. Enter Vietnamese text in the input field (e.g., "Xin chào Việt Nam")
3. Select a voice from the dropdown (NF, SF, NM1, SM, NM2)
4. Tap "Tạo giọng nói" (Generate Speech)
5. Listen to the generated audio

## Performance

### Real Device Testing

| Device | Chip | Inference Time | Memory | Status |
|--------|------|----------------|--------|--------|
| **Xiaomi 12S Pro** | Snapdragon 8+ Gen 1 | ~200-300ms | ~280MB | ✅ Tested |
| Flagship (SD 8 Gen 2) | Snapdragon 8 Gen 2 | ~250ms | ~280MB | Estimated |
| Mid-range (SD 778G) | Snapdragon 778G | ~800ms | ~300MB | Estimated |
| Budget (SD 662) | Snapdragon 662 | ~2000ms | ~350MB | Estimated |

*Inference time measured for ~3s audio output*

## Troubleshooting

### App Crashes on Launch
- Check that all ONNX models are in `app/src/main/assets/`
- Verify models are not corrupted
- Ensure device has sufficient RAM

### Audio Quality Issues
- Check if device supports 24kHz audio playback
- Verify ONNX models are the correct versions

### Build Errors
- Clean and rebuild: `./gradlew clean build`
- Sync Gradle files in Android Studio
- Check Android SDK version is 26+

## Model Bundle Size

Total APK size with models: **~185 MB**

Breakdown:
- App code & resources: ~20 MB
- ONNX models: ~165 MB

## Alternative: Download Models at Runtime

For smaller APK size, consider downloading models on first app launch instead of bundling in assets. This requires:

1. Adding network permissions
2. Implementing download progress UI
3. Caching models in app storage

## License

This project is part of Valtec TTS. See main repository for license details.

---

**Powered by Valtec AI Team** | ONNX Runtime Mobile
