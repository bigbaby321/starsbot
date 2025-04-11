import os
import logging
import json
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# === Logging ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Config ===
TOKEN = os.getenv("TOKEN")
print("TOKEN =", os.getenv("TOKEN"))
DATA_FILE = "data.json"
WAIT_TIME = 8 * 60 * 60
LEVELS = [(150000, 5, 1), (100000, 4, 3), (20000, 3, 12), (10000, 2, 17), (0, 1, 21)]
REWARDS = {1: 0.5, 2: 2, 3: 5, 4: 10, 5: 20}

# === Data ===
def load_data():
    if Path(DATA_FILE).exists():
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(user_data, f)

user_data = load_data()

def get_level_info(total_deposit):
    for amount, level, days in LEVELS:
        if total_deposit >= amount:
            return level, days
    return 1, 21

def get_reward(level): return REWARDS.get(level, 0.5)

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🪓 Khai Thác", callback_data="mine_menu"),
         InlineKeyboardButton("💼 Ví", callback_data="wallet")],
        [InlineKeyboardButton("📜 Lịch sử", callback_data="history_0")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in user_data:
        user_data[user_id] = {"balance": 0, "last_claim": 0, "deposits": [], "withdraw_requests": [], "mining_logs": []}
        save_data()
    total = sum(d["amount"] for d in user_data[user_id]["deposits"])
    level, _ = get_level_info(total)
    await update.message.reply_text(f"Welcome!

Balance: {user_data[user_id]['balance']}
Level: {level}", reply_markup=main_menu())

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    data = user_data[user_id]

    if query.data.startswith("history"):
        page = int(query.data.split("_")[1])
        logs = [f"➕ Nạp {d['amount']} sao - {datetime.fromtimestamp(d['time']).strftime('%d/%m/%Y %H:%M')}" for d in data["deposits"]]
        logs += [f"➖ Rút {w['amount']} sao - {datetime.fromtimestamp(w['time']).strftime('%d/%m/%Y %H:%M')}" for w in data["withdraw_requests"] if w.get("status") == "success"]
        logs += [f"⛏ Khai thác {m['amount']} sao - {datetime.fromtimestamp(m['time']).strftime('%d/%m/%Y %H:%M')}" for m in data["mining_logs"]]
        logs = sorted(logs, reverse=True)
        per_page, start, end = 10, page * 10, (page + 1) * 10
        sliced = logs[start:end]
        text = "*📜 Lịch sử giao dịch:*
" + "
".join(sliced) if sliced else "🔍 Không có giao dịch."
        buttons = []
        if page > 0: buttons.append(InlineKeyboardButton("⬅️ Trước", callback_data=f"history_{page - 1}"))
        if end < len(logs): buttons.append(InlineKeyboardButton("Tiếp ➡️", callback_data=f"history_{page + 1}"))
        buttons.append(InlineKeyboardButton("⬅️ Quay lại", callback_data="mine_menu"))
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([buttons]))

    elif query.data == "mine_menu":
        now, last = time.time(), data["last_claim"]
        level, _ = get_level_info(sum(d["amount"] for d in data["deposits"]))
        reward = get_reward(level)
        remaining = max(0, int(WAIT_TIME - (now - last)))
        msg = (f"🪓 *Khai Thác Sao*

"
               f"📈 Cấp độ: *{level}*
🎁 Phần thưởng: *{reward} sao*
"
               f"🌟 Số dư: `{data['balance']}`
"
               f"⏳ Thời gian còn lại: `{time.strftime('%H:%M:%S', time.gmtime(remaining))}`")
        btn = [[InlineKeyboardButton("🪓 Thu Hoạch", callback_data="mine_now")]]
        await query.edit_message_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(btn))

    elif query.data == "mine_now":
        now, last = time.time(), data["last_claim"]
        if now - last >= WAIT_TIME:
            level, _ = get_level_info(sum(d["amount"] for d in data["deposits"]))
            reward = get_reward(level)
            data["balance"] += reward
            data["last_claim"] = now
            data["mining_logs"].append({"amount": reward, "time": now})
            save_data()
            await query.edit_message_text(f"✅ Đã khai thác thành công! 🌟 +{reward} sao.", reply_markup=main_menu())
        else:
            await query.edit_message_text("⏳ Chưa đến thời gian khai thác. Vui lòng chờ thêm!", reply_markup=main_menu())

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button))
    print("✅ Bot started.")
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())