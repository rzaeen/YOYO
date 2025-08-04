# YOYO  
 Description in English
🔐 YOYO – Full USB Forensics & Backup Tool
YOYO is a professional cybersecurity tool built with Python, designed for automatic backup, data recovery, and forensic analysis of removable devices like USB flash drives and external hard disks.

When a USB device is connected, YOYO automatically:

🔍 Detects the device instantly
📁 Copies all files (old, new, hidden, large)
💾 Creates a full backup on the Desktop
🧠 Analyzes sensitive files (passwords, tokens, configs)
📄 Generates a detailed forensic report
🛠️ Handles errors gracefully without crashing
✅ Key Features
Supports Linux & Windows
Handles very large files (100GB+)
Copies hidden, system, and locked files (if accessible)
Silent mode – no developer name displayed
Professional CLI interface with colors and smooth navigation
Ideal for digital forensics, security audits, and data recovery
🎯 Who Uses YOYO?
Cybersecurity analysts
Digital forensic investigators
IT administrators
Privacy-conscious users
# 1. استنساخ المشروع
git clone https://github.com/yourusername/yoyo.git
cd yoyo

# 2. إنشاء بيئة افتراضية
python3 -m venv yoyo-env
source yoyo-env/bin/activate  # Linux/Mac
# أو على ويندوز: yoyo-env\Scripts\activate

# 3. تثبيت المكتبات
pip install scapy  # اختياري لدعم ميزات مستقبلية

# 4. تشغيل الأداة (على لينكس: باستخدام sudo)
sudo python3 yoyo.py
