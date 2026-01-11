# 1. ติดตั้ง Python venv และตัวจำลองหน้าจอ (Xvfb)
```sudo apt-get update
sudo apt-get install -y python3-venv xvfb unzip wget```

# 2. ติดตั้ง Google Chrome (ถ้ายังไม่ได้ลง)
```wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb```

# 3. สร้างและเปิดใช้งาน .venv
```python3 -m venv .venv
source .venv/bin/activate```

# 4. ติดตั้ง lib
```pip install selenium webdriver-manager pyvirtualdisplay requests```

# 5.
```xvfb-run -a python main.py```
