#!/usr/bin/env python3
"""Telegram alert when iPhone Duo 256GB Night Sky is available for in-store pickup.

Polls Apple's own pickup-availability endpoint (the same data InStock Radar
reads) for the Apple Stores nearest one or more US ZIP codes, and sends a
Telegram message when the part goes from unavailable to available at a store.

Configuration (environment variables):
  TELEGRAM_BOT_TOKEN  token from @BotFather
  TELEGRAM_CHAT_ID    your chat id (see README)
  ZIP_CODES           comma-separated US ZIPs, e.g. "10001,07030"
  PART                Apple part number (default MK1F4LL/A = 256GB Night Sky)
  INTERVAL            seconds between checks (default 60)

Usage:
  python3 iphone_duo_bot.py           # run forever
  python3 iphone_duo_bot.py --once    # single check, print results
  python3 iphone_duo_bot.py --test    # send a test Telegram message
"""

import json
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

PART = os.environ.get("PART", "MK1F4LL/A")
ZIP_CODES = [z.strip() for z in os.environ.get("ZIP_CODES", "").split(",") if z.strip()]
INTERVAL = int(os.environ.get("INTERVAL", "60"))
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

PICKUP_URL = "https://www.apple.com/us/shop/retail/pickup-message"
BUY_URL = "https://www.apple.com/us/shop/buy-iphone/iphone-duo"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/18.0 Safari/605.1.15")


def log(msg):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), msg, flush=True)


def check_zip(zip_code):
    """Return [(store_number, store_name, city, distance, available, quote)]."""
    qs = urllib.parse.urlencode({"pl": "true", "parts.0": PART, "location": zip_code})
    req = urllib.request.Request(
        f"{PICKUP_URL}?{qs}",
        headers={"User-Agent": UA, "Accept": "application/json",
                 "Referer": "https://www.apple.com/us/shop/buy-iphone"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    results = []
    for s in data.get("body", {}).get("stores", []):
        pa = s.get("partsAvailability", {}).get(PART, {})
        quote = pa.get("messageTypes", {}).get("regular", {}).get("storePickupQuote", "")
        results.append((
            s.get("storeNumber"), s.get("storeName"), s.get("city"),
            s.get("storeDistanceWithUnit", ""),
            pa.get("pickupDisplay") == "available", quote,
        ))
    return results


def send_telegram(text):
    if not (BOT_TOKEN and CHAT_ID):
        log("Telegram not configured; would have sent: " + text)
        return
    body = urllib.parse.urlencode({
        "chat_id": CHAT_ID, "text": text, "disable_web_page_preview": "true",
    }).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data=body)
    with urllib.request.urlopen(req, timeout=20) as r:
        if not json.load(r).get("ok"):
            raise RuntimeError("Telegram sendMessage failed")


def check_all():
    """Merge results from all ZIPs, keyed by store number."""
    stores = {}
    for z in ZIP_CODES:
        for row in check_zip(z):
            stores[row[0]] = row
    return stores


def main():
    args = sys.argv[1:]
    if "--test" in args:
        send_telegram(f"✅ iPhone Duo bot is set up. Watching {PART} near {', '.join(ZIP_CODES) or '(no ZIP set)'}.")
        if BOT_TOKEN and CHAT_ID:
            log("Test message sent.")
        return
    if not ZIP_CODES:
        sys.exit("Set ZIP_CODES, e.g. ZIP_CODES=10001")

    if "--once" in args:
        for num, name, city, dist, avail, quote in check_all().values():
            log(f"{'AVAILABLE' if avail else 'sold out '}  {name} ({city}, {dist})  {quote}")
        return

    log(f"Watching {PART} near {', '.join(ZIP_CODES)} every ~{INTERVAL}s")
    available = set()  # stores we've already alerted for
    failures = 0
    while True:
        try:
            stores = check_all()
            failures = 0
            now = {num for num, *_, avail, _q in stores.values() if avail}
            for num in now - available:
                _, name, city, dist, _, quote = stores[num]
                log(f"IN STOCK at {name}")
                send_telegram(
                    f"📱 iPhone Duo 256GB Night Sky is AVAILABLE\n"
                    f"Apple {name}, {city} ({dist})\n{quote}\n\n"
                    f"Reserve now: {BUY_URL}")
            for num in available - now:
                log(f"Sold out again at {stores.get(num, (num, num))[1]}")
            available = now
            if not now:
                log(f"Not available at {len(stores)} nearby stores")
        except (urllib.error.URLError, TimeoutError, ValueError, RuntimeError) as e:
            failures += 1
            log(f"Check failed ({failures}): {e}")
            if failures == 10:
                try:
                    send_telegram("⚠️ iPhone Duo bot: 10 checks in a row failed. "
                                  "Apple may be blocking this IP; check the logs.")
                except Exception as te:
                    log(f"Could not send failure alert: {te}")
        # back off on repeated failures; small jitter so we don't poll on a fixed beat
        delay = INTERVAL * min(2 ** max(failures - 1, 0), 10) if failures else INTERVAL
        time.sleep(delay + random.uniform(0, 10))


if __name__ == "__main__":
    main()
