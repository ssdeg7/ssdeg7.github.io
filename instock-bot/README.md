# iphone-check

A small bot that sends you a Telegram message when **iPhone Duo 256GB Night Sky**
(`MK1F4LL/A`) becomes available for in-store pickup at Apple Stores near you.

It polls Apple's own pickup-availability endpoint, the same data
[InStock Radar](https://instockradar.com/us/iphone-duo) shows, for the 12 nearest
stores to each ZIP code you give it. You get one alert each time a store goes from
sold out to available. Python 3 standard library only; nothing to install.

## Setup

1. **Create a Telegram bot:** message [@BotFather](https://t.me/BotFather), send
   `/newbot`, and copy the token.
2. **Get your chat ID:** send any message to your new bot, then open
   `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy `message.chat.id`.
3. **Run it:**

```sh
export TELEGRAM_BOT_TOKEN="123456:ABC..."
export TELEGRAM_CHAT_ID="123456789"
export ZIP_CODES="43215"          # comma-separated, e.g. "10001,07030"

python3 iphone_duo_bot.py --test  # sends a test Telegram message
python3 iphone_duo_bot.py --once  # prints current status per store
python3 iphone_duo_bot.py         # runs forever, checks every ~60s
```

Optional: `INTERVAL` (seconds, default 60). `PART` lets you watch another model, e.g.
`MK1H4LL/A` (512GB Night Sky) or `MK1E4LL/A` (256GB Star White).

## Where to run it

Run it on a machine with a **home internet connection** (your computer, a Raspberry
Pi, an old laptop). Apple blocks many datacenter/cloud IPs (it returns HTTP 541), and
restocks typically last only about 2 minutes, so GitHub Actions (5+ minute schedules,
often delayed) is too slow for this.

To keep it running in the background on macOS/Linux:

```sh
nohup python3 iphone_duo_bot.py >> bot.log 2>&1 &
```

If checks fail 10 times in a row, the bot sends you a Telegram warning.
