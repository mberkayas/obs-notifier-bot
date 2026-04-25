# OBS Notifier Bot 🎓

Kayseri Üniversitesi Öğrenci Bilgi Sistemi (OBS) için tasarlanmış otomatik not kontrol ve bildirim botu. 

Sistem arka planda (görünmez olarak) çalışarak belirli aralıklarla notlarınızı kontrol eder. Yeni bir sınav sonucu açıklandığında veya mevcut bir notunuz güncellendiğinde, **Telegram üzerinden size anında mesaj atar.** İçerisinde bulunan yerel yapay zeka modeli (`ddddocr`) sayesinde OBS sisteminin girişindeki CAPTCHA (doğrulama) güvenlik duvarını kimseye ihtiyaç duymadan otomatik olarak aşar.

## Kurulum Rehberi (Nasıl Kullanılır?)

Bu botu kendi bilgisayarınızda çalıştırmak için aşağıdaki adımları sırasıyla uygulayın:

### 1. Projeyi İndirin ve Gereksinimleri Kurun
Öncelikle bilgisayarınızda [Python](https://www.python.org/downloads/) yüklü olmalıdır.

Projeyi indirin (Yukarıdaki yeşil **Code** butonuna basıp **Download ZIP** diyerek indirebilirsiniz). Klasörü zip'ten çıkartın. Klasörün içine girin ve boş bir yere sağ tıklayarak terminali (Komut İstemcisi / PowerShell) açın.

Şu komutu yazarak gerekli eklentileri tek seferde kurun:
```bash
pip install -r requirements.txt
```

Botun arka planda internet sitelerine girebilmesi için gerekli tarayıcı motorunu kurun:
```bash
playwright install
```

### 2. Kendi Bilgilerinizi Girin (`.env` Dosyası)
Kodun sizin adınıza sisteme girebilmesi ve size mesaj atabilmesi için şifrelerinizi girmelisiniz. Şifrelerinizin güvende olması için bu projede `.env` sistemi kullanılmıştır. 

Proje klasörünün içine yeni bir dosya oluşturun ve adını tam olarak **`.env`** koyun. (Başında nokta olmalı). İçerisine kendi bilgilerinizi şu formatta yapıştırın ve kaydedin:

```env
TELEGRAM_TOKEN=bot_fatherdan_aldiginiz_token_buraya
TELEGRAM_CHAT_ID=kendi_telegram_chat_id_numaraniz
OBS_USERNAME=ogrenci_numaraniz
OBS_PASSWORD=obs_sifreniz
```

### 3. Çalıştırma
Her şey hazır! Terminale aşağıdaki komutu yazarak botu çalışmaya bırakabilirsiniz:

```bash
python bot.py --loop
```
Bot artık her 2 dakikada bir arka planda kontrol yapacak ve değişiklik olursa telefonunuza bildirim gönderecektir.
