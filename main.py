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
    category = Column(String)
    description = Column(String)
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
        '/add <金额> <类别> <描述> - 添加一笔支出\n'
        '/list - 查看最近的支出记录\n'
        '/stats - 查看支出统计'
    )

async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # 解析命令参数
        args = context.args
        if len(args) < 3:
            await update.message.reply_text('请使用格式：/add <金额> <类别> <描述>')
            return

        amount = float(args[0])
        category = args[1]
        description = ' '.join(args[2:])

        # 保存到数据库
        session = Session()
        expense = Expense(
            user_id=update.effective_user.id,
            amount=amount,
            category=category,
            description=description
        )
        session.add(expense)
        session.commit()
        session.close()

        await update.message.reply_text(f'已记录支出：{amount}元 - {category} - {description}')
    except ValueError:
        await update.message.reply_text('金额必须是数字！')
    except Exception as e:
        await update.message.reply_text(f'发生错误：{str(e)}')

async def list_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    expenses = session.query(Expense).filter_by(user_id=update.effective_user.id).order_by(Expense.date.desc()).limit(10).all()
    session.close()

    if not expenses:
        await update.message.reply_text('暂无支出记录')
        return

    message = '最近的支出记录：\n\n'
    for expense in expenses:
        message += f'{expense.date.strftime("%Y-%m-%d")} - {expense.amount}元 - {expense.category} - {expense.description}\n'

    await update.message.reply_text(message)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    expenses = session.query(Expense).filter_by(user_id=update.effective_user.id).all()
    session.close()

    if not expenses:
        await update.message.reply_text('暂无支出记录')
        return

    total = sum(expense.amount for expense in expenses)
    categories = {}
    for expense in expenses:
        categories[expense.category] = categories.get(expense.category, 0) + expense.amount

    message = f'总支出：{total}元\n\n按类别统计：\n'
    for category, amount in categories.items():
        message += f'{category}: {amount}元\n'

    await update.message.reply_text(message)

def main():
    # 创建应用
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

    # 添加命令处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_expense))
    application.add_handler(CommandHandler("list", list_expenses))
    application.add_handler(CommandHandler("stats", stats))

    # 启动机器人
    application.run_polling()

if __name__ == '__main__':
    main() 