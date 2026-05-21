@echo off
echo ============================================
echo Valtec TTS - Windows EXE Builder
echo ============================================
echo.

echo [1/3] Cai dat cac thu vien ho tro...
pip install pyinstaller sounddevice customtkinter soundfile numpy

echo.
echo [2/3] Dong goi phan mem thanh file EXE...
echo (Qua trinh nay co the mat vai phut)
echo.

:: Use gui_app_modern.py (v2.0) instead of old gui_app.py
pyinstaller --name "ValtecTTS" ^
    --windowed ^
    --onefile ^
    --collect-all customtkinter ^
    --collect-all numpy ^
    --hidden-import=src ^
    --hidden-import=src.models ^
    --hidden-import=src.models.synthesizer ^
    --hidden-import=src.text ^
    --hidden-import=src.text.symbols ^
    --hidden-import=src.vietnamese ^
    --hidden-import=src.nn ^
    --hidden-import=src.utils ^
    --hidden-import=valtec_tts ^
    --add-data "src;src" ^
    --add-data "valtec_tts;valtec_tts" ^
    gui_app_modern.py ^
    --clean

echo.
echo [3/3] Hoan tat!
echo ============================================
echo File EXE da duoc tao trong thu muc 'dist'
echo Ten file: dist\ValtecTTS.exe
echo ============================================
echo.
echo LUU Y: Khi chay lan dau, app se tai model tu HuggingFace.
echo Hay dam bao co ket noi Internet!
echo.
pause
