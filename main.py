import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from datetime import datetime
from collections import defaultdict
import os

API_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# 用于存储用户的记账数据（内存中，重启会丢失，可改为数据库）
expenses = defaultdict(list)

@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    await message.reply("欢迎使用记账机器人！直接发送“早餐 15”就能记账。用 /total 查看今日花费。")

@dp.message_handler(commands=["total"])
async def total_today(message: types.Message):
    user_id = message.from_user.id
    today = datetime.now().date()
    total = sum(amount for (desc, amount, dt) in expenses[user_id] if dt.date() == today)
    await message.reply(f"今天的总支出是：{total} 元")

@dp.message_handler()
async def record_expense(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()
    try:
        parts = text.split()
        if len(parts) != 2:
            raise ValueError("格式不对")
        desc = parts[0]
        amount = float(parts[1])
        now = datetime.now()
        expenses[user_id].append((desc, amount, now))
        await message.reply(f"已记录：{desc} - {amount} 元")
    except Exception as e:
        await message.reply("请发送格式：项目 金额，例如“早餐 15”")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
