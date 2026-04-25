@echo off
echo Sanal ortam aktif ediliyor...
call venv\Scripts\activate.bat

echo ----------------------------------------------------
echo Eski ve bozuk kutuphaneler siliniyor...
echo ----------------------------------------------------
pip uninstall -y ddddocr onnxruntime opencv-python opencv-python-headless

echo ----------------------------------------------------
echo Yeni sorunsuz kutuphaneler kuruluyor...
echo ----------------------------------------------------
pip install ddddocr opencv-python-headless

echo ----------------------------------------------------
echo Kurulum bitti, test basliyor:
echo ----------------------------------------------------
python test_ocr.py

echo.
pause
