import time
import json
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from pyvirtualdisplay import Display

# --- ตั้งค่า Configuration ---
LOG_FILE = "angpao_log.json"
display = None # ตัวแปรสำหรับจอจำลอง

def start_virtual_display():
    """เปิดจอจำลองเฉพาะเมื่อรันบน Linux VPS เพื่อหลอกว่าเป็นคอมพิวเตอร์ปกติ"""
    global display
    if sys.platform.startswith('linux'):
        print("🖥️ กำลังเริ่มระบบจอจำลอง (Xvfb)...")
        # สร้างจอขนาด 1920x1080 (Color depth 24)
        display = Display(visible=0, size=(1920, 1080))
        display.start()

def stop_virtual_display():
    """ปิดจอจำลองเมื่อเลิกใช้"""
    global display
    if display:
        display.stop()

def setup_driver():
    print("🚀 กำลังเปิด Browser...")
    options = webdriver.ChromeOptions()
    
    # --- Option ที่จำเป็นสำหรับ VPS/Linux ---
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-notifications")
    options.add_argument("--window-size=1920,1080")
    
    # สำคัญ: ไม่ใช้ --headless เพื่อหลีกเลี่ยงการโดนจับได้จาก Cloudflare
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def save_to_json(data):
    """บันทึกข้อมูลลงไฟล์ JSON"""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    else:
        logs = []

    logs.append(data)

    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)
    print(f"💾 บันทึกข้อมูลเรียบร้อย")

def get_text_safe(driver, element_id):
    """ดึงข้อความโดยไม่ให้ Error (ถ้าไม่มีให้คืนค่า -)"""
    try:
        return driver.find_element(By.ID, element_id).text.strip()
    except:
        return "-"

def scrape_result_data(driver, link, status_note=""):
    """ฟังก์ชันดึงข้อมูลผลลัพธ์ (ใช้ได้ทั้งหน้ารับเงินและหน้าประวัติ)"""
    try:
        # รอให้ข้อมูลโหลด (สังเกตจากเลขอ้างอิงด้านล่างสุด)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "reference-id")))

        # ดึงข้อมูล
        receiver_name = get_text_safe(driver, "detail-receiver-name-0")
        receiver_amount = get_text_safe(driver, "detail-receiver-amount-0")
        receiver_phone = get_text_safe(driver, "detail-receiver-mobile-no-0")
        timestamp = get_text_safe(driver, "detail-receiver-datetime-0")
        message = get_text_safe(driver, "message")
        ref_id = get_text_safe(driver, "reference-id").replace("เลขอ้างอิงซอง:", "").strip()

        result_data = {
            "status": status_note,
            "receiver_name": receiver_name,
            "amount": receiver_amount,
            "receiver_phone": receiver_phone,
            "message": message,
            "timestamp": timestamp,
            "reference_id": ref_id,
            "link": link
        }

        # --- แสดงผลหน้า Console ---
        print("\n" + "="*40)
        print(f"💰 สรุปข้อมูล ({status_note})")
        print(f"========================================")
        print(f"ชื่อผู้รับ       : {result_data['receiver_name']}")
        print(f"จำนวนเงิน      : {result_data['amount']}")
        print(f"เบอร์โทร       : {result_data['receiver_phone']}")
        print(f"ข้อความ        : {result_data['message']}")
        print(f"เวลา          : {result_data['timestamp']}")
        print(f"Ref ID        : {result_data['reference_id']}")
        print("="*40 + "\n")

        save_to_json(result_data)

    except Exception as e:
        print(f"⚠️ ดึงข้อมูลไม่สำเร็จ (หน้าเว็บอาจโหลดไม่ครบ): {e}")

def redeem_angpao_selenium(driver, phone_number, link):
    try:
        print(f"\n🔗 กำลังไปที่: {link}")
        driver.get(link)
        wait = WebDriverWait(driver, 10)
        
        # --- เช็ค URL ว่าโดนเด้งไปหน้า Detail เลยไหม? ---
        time.sleep(2) # รอ Redirect
        current_url = driver.current_url
        
        if "voucher_detail" in current_url:
            print("⚠️ ลิงก์นี้ถูกรับไปแล้ว หรือหมดอายุ (เข้าสู่โหมดดูประวัติ)")
            scrape_result_data(driver, link, status_note="History/Full")
            return

        # ==========================================
        # ถ้ายังอยู่หน้าปกติ ให้ทำตามขั้นตอนเดิม
        # ==========================================
        
        # 1. ใส่เบอร์โทร
        print("⏳ 1. กำลังใส่เบอร์...")
        try:
            phone_input = wait.until(EC.presence_of_element_located((By.ID, "mobile-text-field")))
            phone_input.click()
            phone_input.clear()
            phone_input.send_keys(phone_number)
        except:
            print("❌ ไม่เจอช่องใส่เบอร์ (อาจจะโหลดหน้าเว็บไม่สมบูรณ์)")
            return

        # 2. กดปุ่มยืนยัน
        print("⏳ 2. กำลังกดปุ่มยืนยัน...")
        try:
            submit_btn = wait.until(EC.element_to_be_clickable((By.ID, "footer_button_text")))
            submit_btn.click()
        except:
            phone_input.send_keys(Keys.ENTER)

        # 3. รอกดฉีกซอง
        print("⏳ 3. รอกดฉีกซอง...")
        try:
            envelope = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@data-testid='envelope-image']")))
            time.sleep(1)
            envelope.click()
            print("✅ กดฉีกซองแล้ว!")
        except:
            pass # ซองอาจจะเปิดอัตโนมัติหรือข้ามหน้านี้

        # 4. ดึงข้อมูล (Success Case)
        print("⏳ 4. กำลังดึงข้อมูล...")
        scrape_result_data(driver, link, status_note="Success Redeem")

    except Exception as e:
        print(f"❌ Error ระบบ: {e}")

# --- ส่วนทำงานหลัก ---
if __name__ == "__main__":
    print("--- TrueMoney Auto Redeem (VPS/Linux Full Version) ---")
    
    # 1. เริ่มจอจำลอง
    start_virtual_display()
    
    driver = None
    try:
        my_phone = input("กรุณาใส่เบอร์ Wallet ของคุณ: ").strip()
        
        # 2. เริ่ม Browser
        driver = setup_driver()
        
        print("\n✅ พร้อมใช้งาน! วางลิงก์แล้วกด Enter (พิมพ์ 'exit' เพื่อออก)")
        while True:
            link = input("\n>> วางลิงก์ซองที่นี่: ").strip()
            
            if link.lower() == 'exit':
                break
            
            if "gift.truemoney.com" in link:
                redeem_angpao_selenium(driver, my_phone, link)
            else:
                print("❌ ลิงก์ไม่ถูกต้อง")

    except KeyboardInterrupt:
        print("\nจบการทำงาน")
    except Exception as e:
        print(f"Critical Error: {e}")
    finally:
        # Cleanup
        if driver:
            driver.quit()
        stop_virtual_display()
        print("👋 ปิดโปรแกรมเรียบร้อย")