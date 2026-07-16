import os
import json
import urllib.request
from src.application.ports.outputs import NotificationPort

class NotificationManagerAdapter(NotificationPort):
    def __init__(self):
        # We can configure this via environment variables or a config file
        self.telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        
    def send_notification(self, title: str, message: str, status: str = "info") -> bool:
        # Determine emoji based on status
        emoji = "ℹ️"
        if status == "success":
            emoji = "✅"
        elif status == "error":
            emoji = "❌"
        elif status == "warning":
            emoji = "⚠️"
            
        full_message = f"{emoji} *{title}*\n\n{message}"
        print(f"[Notification] {full_message}")
        
        # If Telegram is configured, send it
        if self.telegram_bot_token and self.telegram_chat_id:
            try:
                url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
                data = json.dumps({
                    "chat_id": self.telegram_chat_id,
                    "text": full_message,
                    "parse_mode": "Markdown"
                }).encode("utf-8")
                
                req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    return response.getcode() == 200
            except Exception as e:
                print(f"[Notification] Error enviando a Telegram: {e}")
                return False
                
        return True
