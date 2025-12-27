from instagrapi import Client
from instagrapi.exceptions import *
import random
import time
import logging
import requests
from bs4 import BeautifulSoup

from config import *
from database import get_setting, update_setting, get_item, add_item, is_processed, mark_processed
from utils.link_processor import process_telegram_link, generate_unique_pk

logger = logging.getLogger(__name__)

class StableInstagramBot:
    def __init__(self):
        self.cl = Client()
        self.cl.delay_range = [4, 12]  # تأخیر کلی بین درخواست‌ها

        # گرفتن آخرین نسخه اینستاگرام اتوماتیک
        latest_version = self.get_latest_instagram_version()
        logger.info(f"استفاده از app_version: {latest_version}")

        self.cl.set_device({
            'app_version': latest_version,           # همیشه آخرین نسخه واقعی
            'android_version': 15,
            'android_release': '15.0.0',
            'dpi': '480dpi',
            'resolution': '1220x2712',
            'manufacturer': 'Xiaomi',
            'device': 'zircon',
            'model': 'Redmi Note 14 Pro 5G',
            'cpu': 'arm64-v8a'
        })

        self.logged_in = self._login()
        self.delay_range_dm = [int(get_setting('min_delay_dm', '10')), int(get_setting('max_delay_dm', '25'))]

    def get_latest_instagram_version(self):
        """آخرین نسخه اینستاگرام اندروید رو اتوماتیک از Uptodown بگیره"""
        fallback_version = '410.1.0.63.71'  # نسخه فعلی تا دسامبر ۲۰۲۵

        try:
            url = "https://instagram.en.uptodown.com/android"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                logger.warning(f"صفحه Uptodown باز نشد (کد: {response.status_code})")
                return fallback_version

            soup = BeautifulSoup(response.text, 'html.parser')
            
            version_tag = soup.find('div', class_='version')
            if version_tag:
                version = version_tag.text.strip()
                # مطمئن شدن که فرمت درست باشه (مثل 410.1.0.63.71)
                import re
                if re.match(r'\d+\.\d+\.\d+\.\d+\.\d+', version):
                    logger.info(f"آخرین نسخه اینستاگرام پیدا شد: {version}")
                    return version
                else:
                    logger.warning(f"نسخه پیدا شده نامعتبر: {version}")
                    return fallback_version

            logger.warning("تگ div.version پیدا نشد")
            return fallback_version
        except Exception as e:
            logger.error(f"خطا در گرفتن آخرین نسخه: {e}")
            return fallback_version

    def _login(self, retry_count=0):
        max_retries = 2

        if SESSION_FILE.exists():
            try:
                self.cl.load_settings(SESSION_FILE)
                self.cl.get_timeline_feed()
                logger.info("Session loaded successfully")
                return True
            except Exception as e:
                logger.warning(f"Session load failed: {e}")
                if retry_count < max_retries:
                    logger.info(f"Session قدیمی نامعتبر. پاک کردن و تلاش مجدد ({retry_count + 1}/{max_retries})...")
                    SESSION_FILE.unlink(missing_ok=True)
                    time.sleep(random.uniform(30, 90))
                    return self._login(retry_count=retry_count + 1)

        try:
            logger.info("تلاش fresh login...")
            self.cl.login(USERNAME, PASSWORD)
            self.cl.dump_settings(SESSION_FILE)
            logger.info("Login موفق → session جدید ذخیره شد")
            time.sleep(random.uniform(90, 150))
            return True
        except ChallengeRequired:
            logger.error("Challenge Required! باید دستی حل کنی.")
            return False
        except Exception as e:
            logger.error(f"Login error: {type(e).__name__} - {e}")
            if retry_count < max_retries:
                logger.info(f"تلاش مجدد ({retry_count + 1}/{max_retries})...")
                time.sleep(random.uniform(60, 120))
                return self._login(retry_count=retry_count + 1)
            else:
                logger.critical("حداکثر تلاش‌ها تمام شد.")
                return False

    def send_dm(self, user_id, message):
        try:
            logger.info(f"شروع ارسال DM به کاربر {user_id}: {message[:50]}...")
            self.cl.direct_send(message, [int(user_id)])
            time.sleep(random.uniform(*self.delay_range_dm))
            logger.info(f"DM به {user_id} با موفقیت ارسال شد")
        except Exception as e:
            logger.error(f"خطا در ارسال DM به {user_id}: {type(e).__name__} - {e}")

    def reply_to_comment(self, media_id, comment_id, text):
        try:
            logger.info(f"شروع ارسال reply زیر کامنت {comment_id}: {text}")
            self.cl.media_comment(media_id, text, replied_to_comment_id=comment_id)
            time.sleep(random.uniform(40, 90))
            logger.info(f"Reply به کامنت {comment_id} ارسال شد")
        except Exception as e:
            logger.error(f"خطا در ارسال reply به کامنت {comment_id}: {type(e).__name__} - {e}")

    def show_admin_panel(self, user_id):
        panel = (
            "💎 پنل مدیریت ربات (نسخه نهایی - ۱۴۰۴)\n\n"
            "تنظیمات فعلی سیستم:\n"
            f"۱. فاصله چک کامنت‌ها: {get_setting('check_interval', '420')} ثانیه\n"
            f"۲. حداقل تأخیر ارسال دایرکت: {get_setting('min_delay_dm', '10')} ثانیه\n"
            f"۳. حداکثر تأخیر ارسال دایرکت: {get_setting('max_delay_dm', '25')} ثانیه\n"
            f"۴. تعداد پست تحت نظارت: {get_setting('posts_count', '5')} پست آخر\n\n"
            "دستورات مجاز (دقیق بنویسید):\n\n"
            "• پنل → نمایش این پنل\n\n"
            "• تنظیم [شماره] [مقدار]\n"
            "  مثال: تنظیم 1 600   (تغییر فاصله چک کامنت به ۱۰ دقیقه)\n\n"
            "• ثبت start=... - نام فیلم\n"
            "  مثال: ثبت start=movie_abc123 - جوکر ۲\n\n"
            "  توضیح مهم: لینک کامل نفرستید! فقط قسمت start رو بدهید.\n"
            "  ربات خودش لینک کامل رو می‌سازه و در دیتابیس ذخیره می‌کنه.\n"
            "  دلیل: اینستاگرام گاهی پیام‌های حاوی لینک کامل رو بلاک می‌کنه.\n"
            "  بعد از ثبت، کد ۴ رقمی به شما داده می‌شه که کاربران باید کامنت کنند.\n\n"
            "موفق باشید! 🚀"
        )
        self.send_dm(user_id, panel)

    def process_comments(self):
        """چک کامنت‌ها فقط با API خصوصی (v1) - بدون GraphQL عمومی"""
        try:
            posts_count = int(get_setting('posts_count', '5'))
            logger.info(f"شروع چک {posts_count} پست اخیر فقط با API خصوصی...")

            try:
                medias = self.cl.user_medias_v1(self.cl.user_id, amount=posts_count)
            except Exception as e:
                logger.warning(f"user_medias_v1 ارور داد: {e} → fallback به user_medias")
                medias = self.cl.user_medias(self.cl.user_id, amount=posts_count)

            if not medias or len(medias) == 0:
                logger.warning("هیچ پستی پیدا نشد! بررسی کن: پست داری؟ posts_count درست باشه؟")
                return

            logger.info(f"{len(medias)} پست گرفته شد")

            for media in medias:
                logger.info(f"پردازش پست: PK={media.pk} (نوع: {media.media_type})")

                try:
                    comments = self.cl.media_comments(media.pk, amount=40)
                    logger.info(f"{len(comments)} کامنت گرفته شد")
                except Exception as e:
                    logger.error(f"خطا در کامنت‌های پست {media.pk}: {e}")
                    continue

                for comment in comments:
                    c_id = f"c_{comment.pk}"
                    if is_processed(c_id):
                        logger.debug(f"کامنت {c_id} قبلاً پردازش شده")
                        continue

                    text = (comment.text or "").strip()
                    logger.info(f"کامنت {comment.pk}: {text}")

                    if not text.isdigit() or not (1000 <= int(text) <= 9999):
                        continue

                    pk = int(text)
                    item = get_item(pk)
                    if not item:
                        logger.warning(f"کد {pk} در دیتابیس نیست")
                        continue

                    category, name, link = item
                    reply_text = random.choice(REPLY_TEMPLATES)
                    logger.info(f"ارسال reply به کامنت {comment.pk}: {reply_text}")
                    self.reply_to_comment(media.pk, comment.pk, reply_text)

                    dm_msg = random.choice(DM_TEMPLATES).format(category=category, name=name, link=link)
                    logger.info(f"ارسال DM به {comment.user.pk}: {dm_msg[:50]}...")
                    self.send_dm(comment.user.pk, dm_msg)

                    mark_processed(c_id)
                    logger.info(f"کامنت {comment.pk} با کد {pk} کامل پردازش شد")

        except Exception as e:
            logger.error(f"خطای کلی در چک کامنت‌ها: {type(e).__name__} - {e}")

    def process_dms(self):
        try:
            threads = self.cl.direct_threads(amount=8)  # تعداد کم کافیه چون همون دیلی شدیدی نداره
            for t in threads:
                user_count = len(t.users)
                title = getattr(t, 'thread_title', '').strip()

                # توی ترد ها وقتی کاربر تعداش 0 باشه یعنی اکانت خودتونه
                if user_count == 0:
                    logger.info(f"✅ Saved Messages is detected! Thread ID: {t.id} | Title: '{title}' | Users: 0")
                    msgs = self.cl.direct_messages(t.id, amount=5)  # آخرین ۵ پیام
                    if not msgs:
                        logger.warning(f"There's no message at Saved Message!")
                        continue

                    msg = msgs[0]
                    text = (msg.text or "").strip()
                    if not text:
                        continue

                    logger.info(f"New message at Saved Messages: {text[:80]}...")
                    self.process_admin_command(self.cl.user_id, text)
                    self.cl.direct_send_seen(t.id)  # seen کردن

                else:
                    logger.debug(f"اسکیپ thread {t.id} - غیر Saved (کاربران: {user_count}, عنوان: '{title}')")

                time.sleep(random.uniform(8, 15))

        except Exception as e:
            logger.error(f"خطا در پردازش دایرکت‌ها: {type(e).__name__} - {e}")

    def process_admin_command(self, user_id, text):
        if user_id != ADMIN_ID:
            return

        text = text.strip()
        text_lower = text.lower()
        logger.info(f"Processing admin command from {user_id}: {text}")

        if text_lower == "پنل":
            self.show_admin_panel(user_id)
            return

        if text_lower.startswith("تنظیم ") and len(text.split()) == 3:
            try:
                parts = text.split()
                n = int(parts[1])
                v = int(parts[2])

                if n == 1:
                    update_setting('check_interval', str(v))
                    msg = f"✅ فاصله چک کامنت‌ها به {v} ثانیه تغییر کرد"
                elif n == 2:
                    update_setting('min_delay_dm', str(v))
                    self.delay_range_dm[0] = v
                    msg = f"✅ حداقل تأخیر دایرکت به {v} ثانیه تنظیم شد"
                elif n == 3:
                    update_setting('max_delay_dm', str(v))
                    self.delay_range_dm[1] = v
                    msg = f"✅ حداکثر تأخیر دایرکت به {v} ثانیه تنظیم شد"
                elif n == 4:
                    update_setting('posts_count', str(v))
                    msg = f"✅ تعداد پست تحت نظارت به {v} تغییر یافت"
                else:
                    msg = "❌ شماره تنظیم معتبر نیست (۱ تا ۴)"

                self.send_dm(user_id, msg)
            except ValueError:
                self.send_dm(user_id, "❌ فرمت اشتباه! مثال: تنظیم ۱ ۶۰۰")
            return

        if text_lower.startswith("ثبت "):
            try:
                content = text.split("ثبت", 1)[1].strip() if "ثبت" in text else ""
                logger.info(f"محتوای ثبت دریافتی: {content}")

                if "-" not in content:
                    self.send_dm(user_id, "❌ فرمت اشتباه!\nمثال درست:\nثبت start=movie_abc123 - جوکر ۲\nیا ثبت ?start=animation_10,11,12 - انیمیشن تست")
                    return

                start_part, name = [x.strip() for x in content.rsplit("-", 1)]

                start_value = None
                for prefix in ["start=", "?start="]:
                    if prefix in start_part:
                        start_value = start_part.split(prefix)[-1].strip()
                        break
                    elif start_part.startswith(prefix):
                        start_value = start_part[len(prefix):].strip()

                if not start_value:
                    self.send_dm(user_id, "❌ مقدار start پیدا نشد!\nلطفاً به این شکل بنویسید:\nثبت start=abc123 - نام فیلم\nیا ثبت ?start=abc123 - نام فیلم")
                    return

                full_link = f"https://t.me/{TELEGRAM_BOT_USERNAME}?start={start_value}"
                logger.info(f"لینک ساخته‌شده: {full_link}")

                cat, _ = process_telegram_link(full_link)
                if not cat:
                    self.send_dm(user_id, "❌ مقدار start معتبر نیست (category شناسایی نشد)")
                    return

                pk = generate_unique_pk()
                add_item(pk, cat, name, full_link)

                success = (
                    "🎬 **ثبت موفق!** محتوا با موفقیت اضافه شد\n\n"
                    f"عنوان: {name}\n"
                    f"نوع محتوا: {cat}\n"
                    f"کد اختصاصی: {pk}\n"
                    f"لینک: {full_link}\n\n"
                    "متن داخل پست:\n"
                    f"فقط عدد بالا ({pk}) را زیر پست کامنت کنید\n"
                    "لینک دانلود به صورت خودکار به دایرکت شما ارسال می‌شود!\n"
                    "\n"
                    "تنها با کلیک روی متن میتونید اون رو کپی کنید! 🌟"
                )
                self.send_dm(user_id, success)

            except ValueError as ve:
                logger.warning(f"ValueError in ثبت: {ve}")
                self.send_dm(user_id, "❌ فرمت اشتباه! مثال درست:\nثبت start=movie_abc123 - جوکر ۲")
            except Exception as e:
                logger.error(f"خطا در ثبت: {e}")
                self.send_dm(user_id, f"❌ مشکلی پیش اومد!\nجزئیات: {str(e)}\nلطفاً دوباره امتحان کن.")
            return