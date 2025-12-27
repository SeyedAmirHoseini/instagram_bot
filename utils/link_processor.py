import base64
import random
import re

def process_telegram_link(url):
    try:
        if "start=" not in url:
            return None, None
        encoded = url.split("start=")[1].split("&")[0]
        encoded += '=' * ((4 - len(encoded) % 4) % 4)
        decoded = base64.b64decode(encoded).decode("utf-8")
        
        m = re.match(r"(movie|serie|animation)", decoded, re.I)
        if not m:
            return None, None
            
        cat_raw = m.group(1).lower()
        mapping = {"movie": "فیلم", "serie": "سریال", "animation": "انیمیشن"}
        return mapping.get(cat_raw), url
    except:
        return None, None

def generate_unique_pk():
    from database import get_connection
    with get_connection() as conn:
        c = conn.cursor()
        while True:
            pk = random.randint(1000, 9999)
            c.execute("SELECT 1 FROM items WHERE pk=?", (pk,))
            if not c.fetchone():
                return pk