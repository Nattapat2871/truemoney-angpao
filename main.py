
#  https://github.com/Nattapat2871/truemoney-angpao

import asyncio
import re
from curl_cffi.requests import AsyncSession

# ==========================================
# ส่วนตั้งค่า
# ==========================================
MY_PHONE_NUMBER = "08xxxxxxxx"  # เบอร์ TrueMoney Wallet ของคุณ
TARGET_LINK = "https://gift.truemoney.com/campaign/?v=xxxxxxxx" # ลิงก์ซองที่ต้องการเติม

async def test_redeem():
    print(f"🔍 Testing redemption for link: {TARGET_LINK}")
    print(f"📱 Phone Number: {MY_PHONE_NUMBER}")
    
    # 1. แกะรหัส Voucher Code จากลิงก์
    match = re.search(r"v=([a-zA-Z0-9]+)", TARGET_LINK)
    if not match:
        print("❌ Invalid Link Format (หา code ไม่เจอ)")
        return
    
    voucher_code = match.group(1)
    print(f"🔹 Extracted Voucher Code: {voucher_code}")

    # 2. เตรียมข้อมูลสำหรับยิง API
    url = f"https://gift.truemoney.com/campaign/vouchers/{voucher_code}/redeem"
    
    # Header ไม่ต้องเยอะ curl_cffi จัดการให้
    headers = {
        "Content-Type": "application/json",
        "Referer": TARGET_LINK
    }
    
    payload = {
        "mobile": MY_PHONE_NUMBER,
        "voucher_hash": voucher_code
    }

    # 3. ยิง Request (ใช้ impersonate="chrome")
    print("🚀 Sending request to TrueMoney API (Impersonating Chrome)...")
    
    try:
        # ใช้ AsyncSession ของ curl_cffi และสั่งปลอมตัวเป็น chrome
        async with AsyncSession(impersonate="chrome") as client:
            response = await client.post(url, json=payload, headers=headers)
            
            print(f"📡 HTTP Status: {response.status_code}")
            
            # ถ้าผ่าน Cloudflare มาได้ จะต้องอ่าน JSON ได้
            try:
                data = response.json()
                print(f"📄 Raw Response: {data}")
                
                status_code = data.get("status", {}).get("code")
                
                if status_code == "SUCCESS":
                    amount = data.get("data", {}).get("my_ticket", {}).get("amount_baht")
                    owner = data.get("data", {}).get("owner_profile", {}).get("full_name")
                    print("-" * 30)
                    print(f"✅ SUCCESS! รับเงินสำเร็จ")
                    print(f"💰 ยอดเงิน: {amount} บาท")
                    print(f"👤 จาก: {owner}")
                    print("-" * 30)
                else:
                    message = data.get("status", {}).get("message")
                    print("-" * 30)
                    print(f"❌ FAILED: ไม่สำเร็จ (แต่ทะลุ Cloudflare แล้ว)")
                    print(f"⚠️ Reason: {message}")
                    print("-" * 30)
                    
            except Exception as e:
                # ถ้ายังพัง แสดงว่า Cloudflare ยังบล็อกอยู่ หรือ JSON ผิดพลาด
                print(f"❌ Could not parse JSON (อาจยังโดนบล็อก): {response.text[:500]}")

    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_redeem())
