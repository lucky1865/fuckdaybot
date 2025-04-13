import os
import logging
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import asyncio
import time
import re

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 数据库配置
Base = declarative_base()

class Expense(Base):
    __tablename__ = 'expenses'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    amount = Column(Float)
    date = Column(DateTime, default=datetime.utcnow)

# 创建数据库引擎
engine = create_engine('sqlite:///expenses.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# 命令处理函数
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '欢迎使用记账机器人！\n'
        '使用以下命令：\n'
        '直接输入数字记录收支，例如：\n'
        '+100 - 记录收入100元\n'
        '-100 - 记录支出100元\n'
        '/list - 查看最近的收支记录\n'
        '/stats - 查看收支统计\n'
        '/clear - 清空账本'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.strip()
        
        # 检查是否是数字格式
        match = re.match(r'^([+-]\d+(?:\.\d+)?)$', text)
        if not match:
            return  # 如果不是数字格式，忽略消息

        amount = float(match.group(1))

        # 保存到数据库
        session = Session()
        expense = Expense(
            user_id=update.effective_user.id,
            amount=amount
        )
        session.add(expense)
        session.commit()
        session.close()

        # 根据正负号显示收入或支出
        if amount > 0:
            await update.message.reply_text(f'已记录收入：{amount}元')
        else:
            await update.message.reply_text(f'已记录支出：{abs(amount)}元')
    except Exception as e:
        logger.error(f"Error in handle_message: {str(e)}")
        await update.message.reply_text('记录收支时发生错误，请稍后重试')

async def list_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        session = Session()
        expenses = session.query(Expense).filter_by(user_id=update.effective_user.id).order_by(Expense.date.desc()).limit(10).all()
        session.close()

        if not expenses:
            await update.message.reply_text('暂无收支记录')
            return

        message = '最近的收支记录：\n\n'
        for expense in expenses:
            amount_type = '收入' if expense.amount > 0 else '支出'
            message += f'{expense.date.strftime("%Y-%m-%d")} - {amount_type} {abs(expense.amount)}元\n'

        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error in list_expenses: {str(e)}")
        await update.message.reply_text('获取收支记录时发生错误，请稍后重试')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        session = Session()
        expenses = session.query(Expense).filter_by(user_id=update.effective_user.id).all()
        session.close()

        if not expenses:
            await update.message.reply_text('暂无收支记录')
            return

        total_income = sum(expense.amount for expense in expenses if expense.amount > 0)
        total_expense = sum(abs(expense.amount) for expense in expenses if expense.amount < 0)
        balance = total_income - total_expense

        message = f'总收入：{total_income}元\n'
        message += f'总支出：{total_expense}元\n'
        message += f'结余：{balance}元'

        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error in stats: {str(e)}")
        await update.message.reply_text('获取统计信息时发生错误，请稍后重试')

async def clear_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        session = Session()
        session.query(Expense).filter_by(user_id=update.effective_user.id).delete()
        session.commit()
        session.close()
        await update.message.reply_text('账本已清空')
    except Exception as e:
        logger.error(f"Error in clear_expenses: {str(e)}")
        await update.message.reply_text('清空账本时发生错误，请稍后重试')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    # 获取Bot Token
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("No TELEGRAM_BOT_TOKEN found in environment variables")
        return

    # 创建应用
    application = Application.builder().token(token).build()

    # 添加命令处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list", list_expenses))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("clear", clear_expenses))
    
    # 添加消息处理器
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # 添加错误处理器
    application.add_error_handler(error_handler)

    # 启动机器人
    application.run_polling()

if __name__ == '__main__':
    main() 