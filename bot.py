import os
import sqlite3
import pandas as pd
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")

DATE, SHIFT, NAME, START, END, TECH, REP, EQUIP, ACTION = range(9)

conn = sqlite3.connect("tkrs.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS operations(
id INTEGER PRIMARY KEY AUTOINCREMENT,
date TEXT,
shift TEXT,
name TEXT,
start TEXT,
end TEXT,
tech TEXT,
rep TEXT,
equip TEXT
)
""")

conn.commit()

tech_list = [
"ЦА","АЦН-10","АКН","АХО","ППУ",
"Цементосмеситель","Автокран","Звено глушения",
"Звено СКБ","Тягач","Седельный тягач",
"АЗА","Седельный тягач с КМУ",
"Бортовой с КМУ","Топливозаправщик",
"Водовозка","АРОК","Вахтовый автобус","УАЗ"
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [["🚀 Начать заполнение"]]

    await update.message.reply_text(
        "👋 Сетевой график ТКРС\n\nНажмите кнопку чтобы начать",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return DATE


async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["date"] = update.message.text

    keyboard = [["I смена", "II смена"], ["Обе смены"]]

    await update.message.reply_text(
        "🔄 Выберите смену",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return SHIFT


async def shift(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["shift"] = update.message.text

    await update.message.reply_text(
        "📝 Введите название операции",
        reply_markup=ReplyKeyboardRemove()
    )

    return NAME


async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["name"] = update.message.text

    await update.message.reply_text(
        "⏰ Введите время начала (пример 11:00)"
    )

    return START


async def start_time(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["start"] = update.message.text

    await update.message.reply_text(
        "⏰ Введите время окончания (пример 18:00)"
    )

    return END


async def end_time(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["end"] = update.message.text

    keyboard = [tech_list[i:i+2] for i in range(0, len(tech_list), 2)]

    await update.message.reply_text(
        "🔧 Выберите технику",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return TECH


async def tech(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["tech"] = update.message.text

    await update.message.reply_text(
        "👤 Представитель заказчика (или 'нет')",
        reply_markup=ReplyKeyboardRemove()
    )

    return REP


async def rep(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["rep"] = update.message.text

    await update.message.reply_text(
        "📦 Оборудование и материалы (или 'нет')"
    )

    return EQUIP


async def equip(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["equip"] = update.message.text

    cursor.execute("""
    INSERT INTO operations
    (date,shift,name,start,end,tech,rep,equip)
    VALUES (?,?,?,?,?,?,?,?)
    """,
    (
        context.user_data["date"],
        context.user_data["shift"],
        context.user_data["name"],
        context.user_data["start"],
        context.user_data["end"],
        context.user_data["tech"],
        context.user_data["rep"],
        context.user_data["equip"]
    ))

    conn.commit()

    keyboard = [["➕ Добавить ещё операцию"], ["✅ Завершить отчет"]]

    await update.message.reply_text(
        "✅ Операция добавлена\n\nЧто дальше?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return ACTION


async def action(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "➕ Добавить ещё операцию":

        await update.message.reply_text(
            "📝 Введите название операции",
            reply_markup=ReplyKeyboardRemove()
        )

        return NAME

    else:

        await update.message.reply_text(
            "✅ Отчет завершен\nСпасибо за работу 👋",
            reply_markup=ReplyKeyboardRemove()
        )

        return ConversationHandler.END


async def excel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    df = pd.read_sql_query("SELECT * FROM operations", conn)

    file = "tkrs_report.xlsx"

    df.to_excel(file, index=False)

    await update.message.reply_document(open(file, "rb"))


def main():

    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(

        entry_points=[CommandHandler("start", start)],

        states={

            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
            SHIFT: [MessageHandler(filters.TEXT & ~filters.COMMAND, shift)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            START: [MessageHandler(filters.TEXT & ~filters.COMMAND, start_time)],
            END: [MessageHandler(filters.TEXT & ~filters.COMMAND, end_time)],
            TECH: [MessageHandler(filters.TEXT & ~filters.COMMAND, tech)],
            REP: [MessageHandler(filters.TEXT & ~filters.COMMAND, rep)],
            EQUIP: [MessageHandler(filters.TEXT & ~filters.COMMAND, equip)],
            ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, action)]

        },

        fallbacks=[]
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("excel", excel))

    print("Бот запущен...")

    app.run_polling()


if __name__ == "__main__":
    main()