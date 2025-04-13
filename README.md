# Telegram记账机器人

一个简单的Telegram记账机器人，用于记录个人日常支出。

## 功能

- 添加支出记录
- 查看最近的支出记录
- 查看支出统计（总支出和按类别统计）

## 命令

- `/start` - 显示欢迎信息和命令列表
- `/add <金额> <类别> <描述>` - 添加一笔支出
- `/list` - 查看最近的10笔支出记录
- `/stats` - 查看支出统计

## 部署到Render

1. 在Render上创建一个新的Web Service
2. 连接你的GitHub仓库
3. 设置环境变量：
   - `TELEGRAM_BOT_TOKEN` - 你的Telegram Bot Token
4. 部署！

## 本地开发

1. 克隆仓库
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 创建 `.env` 文件并添加你的Bot Token：
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```
4. 运行机器人：
   ```bash
   python main.py
   ``` 