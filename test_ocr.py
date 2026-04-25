import sys
print("ddddocr yükleniyor...")
try:
    import ddddocr
    print("Başarıyla yüklendi!")
except Exception as e:
    print("Hata:", e)
