"""OBS Not Bildirim Botu - Kayseri Universitesi"""
import os, sys, re, json, time, argparse, base64, requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OBS_USERNAME     = os.getenv("OBS_USERNAME")
OBS_PASSWORD     = os.getenv("OBS_PASSWORD")
OBS_LOGIN_URL    = "https://sis.kayseri.edu.tr/oibs/std/login.aspx"
GRADES_FILE      = Path(__file__).parent / "grades.json"
CAPTCHA_IMG      = str(Path(__file__).parent / "captcha_screenshot.png")
CHECK_INTERVAL   = 120

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def send_telegram(message):
    try:
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=10)
        log("✅ Telegram gonderildi." if r.status_code == 200 else f"❌ {r.text}")
    except Exception as e:
        log(f"❌ Telegram hatasi: {e}")

def load_saved_grades():
    return json.loads(GRADES_FILE.read_text(encoding="utf-8")) if GRADES_FILE.exists() else {}

def save_grades(g):
    GRADES_FILE.write_text(json.dumps(g, ensure_ascii=False, indent=2), encoding="utf-8")

def ocr_captcha(image_path: str) -> str:
    """ddddocr (Yerel AI) ile CAPTCHA coz."""
    try:
        import ddddocr
        ocr = ddddocr.DdddOcr(show_ad=False)
        with open(image_path, "rb") as f:
            img_bytes = f.read()
        res = ocr.classification(img_bytes)
        log(f"🔤 OCR sonucu: {res!r}")
        
        nums = re.findall(r"\d+", res)
        if len(nums) >= 2:
            ans = str(int(nums[0]) + int(nums[1]))
            log(f"🧮 Otomatik: {nums[0]} + {nums[1]} = {ans}")
            return ans
    except Exception as e:
        log(f"⚠️ OCR hatasi: {e}")
    return ""


def run_check(saved_grades: dict):
    """Bir kontrol dongusu. (yeni_grades, basarili) donduruluyor."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("dialog", lambda d: d.accept())

        try:
            # ── 1. Giris ──────────────────────────────────────────────────────
            log("🔑 Giris yapiliyor...")
            logged_in = False

            for attempt in range(1, 21):
                page.goto(OBS_LOGIN_URL, timeout=30000)
                page.wait_for_timeout(2000)

                # Zaten icerdeyse (oturum hala aciksa)
                if "login" not in page.url.lower():
                    log(f"✅ Zaten icerde: {page.url}")
                    logged_in = True
                    break

                # Form doldur (JavaScript ile - her zaman calisir)
                page.evaluate(f"""() => {{
                    const u = document.getElementById('txtParamT01');
                    const pw = document.getElementById('txtParamT02');
                    if(u) u.value = '{OBS_USERNAME}';
                    if(pw) {{ pw.removeAttribute('readonly'); pw.value = '{OBS_PASSWORD}'; }}
                }}""")

                # CAPTCHA al ve coz (Dun calisan sorunsuz metot)
                try:
                    page.wait_for_timeout(2000)
                    page.locator("#imgCaptchaImg").screenshot(path=CAPTCHA_IMG, timeout=10000)
                    ans = ocr_captcha(CAPTCHA_IMG)

                except Exception as e:
                    log(f"  [{attempt}/20] CAPTCHA alinamadi: {e}")
                    continue

                if not ans:
                    log(f"  [{attempt}/20] OCR basarisiz, yeniden deneniyor...")
                    continue

                # CAPTCHA gir ve login
                page.evaluate(f"""() => {{
                    const c = document.getElementById('txtSecCode');
                    if(c) c.value = '{ans}';
                }}""")
                page.click("#btnLogin")
                page.wait_for_timeout(2500)

                if "login" not in page.url.lower():
                    log(f"✅ Giris basarili! (Deneme {attempt})")
                    logged_in = True
                    break
                log(f"  [{attempt}/20] Giris basarisiz.")

            if not logged_in:
                log("❌ 20 denemede de giris yapilamadi. 1 dakika sonra tekrar denenecek.")
                return saved_grades, False

            # ── 2. Notlara Git ────────────────────────────────────────────────
            log("📋 Menude Not Listesi aranıyor...")
            page.wait_for_timeout(2000)

            for frame in page.frames:
                try:
                    el = frame.get_by_text("Ders ve D", exact=False).first
                    if el.is_visible(timeout=2000):
                        el.click(); page.wait_for_timeout(1500); break
                except: pass

            for frame in page.frames:
                try:
                    el = frame.get_by_text("Not Listesi", exact=False).first
                    if el.is_visible(timeout=2000):
                        el.click(); page.wait_for_timeout(4000)
                        log("📋 Not Listesi acildi."); break
                except: pass

            # ── 3. Notlari Oku ────────────────────────────────────────────────
            grades = {}
            page.wait_for_timeout(1000)
            for frame in page.frames:
                try:
                    for table in frame.query_selector_all("table"):
                        rows = table.query_selector_all("tr")
                        if len(rows) < 2: continue
                        headers = [th.inner_text().strip() for th in rows[0].query_selector_all("th,td")]
                        if not any(k in " ".join(headers).lower() for k in ["ders","not","vize","final"]):
                            continue
                        log(f"✅ Tablo bulundu: {headers[:4]}")
                        for row in rows[1:]:
                            cells = row.query_selector_all("td")
                            if not cells: continue
                            texts = [c.inner_text().strip() for c in cells]
                            row_data = {headers[i]: texts[i] for i in range(min(len(headers), len(texts)))}
                            name = next((row_data[k] for k in row_data if "ders" in k.lower() and "ad" in k.lower()), "")
                            if not name and len(texts) >= 3: name = texts[2]
                            if len(name) >= 3: grades[name] = row_data
                except: pass

            if not grades:
                log("⚠️ Not tablosu bos/bulunamadi.")
                return saved_grades, False

            log(f"✅ {len(grades)} ders notu okundu.")

            # ── 4. Karsilastir ────────────────────────────────────────────────
            changed = []
            for course, data in grades.items():
                if course not in saved_grades:
                    changed.append(("🆕 YENİ", course, data))
                elif saved_grades[course] != data:
                    changed.append(("🔔 GUNCELLENDI", course, data))

            if changed:
                msg = ["<b>🎓 OBS Not Bildirimi</b>\n"]
                for evt, crs, dat in changed:
                    msg.append(f"{evt}: <b>{crs}</b>")
                    for k, v in dat.items():
                        if v and v != crs: msg.append(f"  • {k}: {v}")
                    msg.append("")
                send_telegram("\n".join(msg))
            else:
                log("✅ Not degisikligi yok.")

            save_grades(grades)
            return grades, True

        finally:
            browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--github", action="store_true", help="GitHub Actions modu (5 dk içinde 2 kez kontrol)")
    args = parser.parse_args()

    if not all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, OBS_USERNAME, OBS_PASSWORD]):
        print("❌ .env veya çevre değişkenlerinde eksik bilgiler var!"); exit(1)

    saved = load_saved_grades()
    try:
        if args.github:
            log("🚀 GitHub Actions modu: 5 dakikalık görev içinde 2 kez kontrol yapılacak.")
            log("=" * 50)
            saved, success = run_check(saved)
            
            log("⏳ 2.5 dakika (150 saniye) bekleniyor (2. kontrol için)...")
            time.sleep(150)
            
            log("=" * 50)
            saved, success = run_check(saved)
            log("🏁 GitHub Actions görevi tamamlandı.")
            
        elif args.loop:
            log(f"🔄 Dongu modu: Her {CHECK_INTERVAL//60} dakikada bir kontrol.")
            while True:
                log("=" * 50)
                saved, success = run_check(saved)
                wait = CHECK_INTERVAL if success else 60
                log(f"⏳ {wait//60} dk {wait%60} sn bekleniyor...")
                time.sleep(wait)
        else:
            run_check(saved)
    except KeyboardInterrupt:
        log("👋 Durduruldu.")
