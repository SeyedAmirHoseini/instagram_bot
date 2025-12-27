import time
import random
import logging
from database import init_db, get_setting
from utils.bot import StableInstagramBot

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')

def main():
    init_db()
    bot = StableInstagramBot()
    if not bot.logged_in:
        print("Login failed - exiting")
        return

    print("Bot started - Careful mode")
    last_check = time.time()

    while True:
        try:
            bot.process_dms()

            now = time.time()
            if now - last_check > int(get_setting('check_interval', '420')):
                print("Checking comments...")
                bot.process_comments()
                last_check = now

            time.sleep(random.uniform(20, 45))
        except KeyboardInterrupt:
            print("Stopped")
            break
        except Exception as e:
            logging.error(f"Main loop error: {e}")
            time.sleep(120)

if __name__ == "__main__":
    main()