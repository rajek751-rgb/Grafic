import os
import sqlite3
import pandas as pd
from datetime import datetime

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
Updater,
CommandHandler,
MessageHandler,
ConversationHandler,
CallbackContext,
Filters
)

TOKEN = os.getenv("BOT_TOKEN")

(
DATE,
SHIFT,
NAME,
START,
END,
TECH,
REP,
EQUIP,
ACTION
) = range(9)

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

def start(update: Update, context: CallbackContext):

keyboard = [["🚀 Начать заполнение"]]

update.message.reply_text(
"👋 Сетевой график ТКРС\n\nНажмите кнопку, чтобы начать",
reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
)

return DATE

def get_date(update: Update, context: CallbackContext):

context.user_data["date"] = update.message.text

keyboard = [["I смена","II смена"],["Обе смены"]]

update.message.reply_text(
"🔄 Выберите смену",
reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
)

return SHIFT

def shift(update: Update, context: CallbackContext):

context.user_data["shift"] = update.message.text

update.message.reply_text(
"📝 Введите название операции",
reply_markup=ReplyKeyboardRemove()
)

return NAME

def name(update: Update, context: CallbackContext):

context.user_data["name"] = update.message.text

update.message.reply_text(
"⏰ Введите время начала (ЧЧ:ММ)"
)

return START

def start_time(update: Update, context: CallbackContext):

context.user_data["start"] = update.message.text

update.message.reply_text(
"⏰ Введите время окончания (ЧЧ:ММ)"
)

return END

def end_time(update: Update, context: CallbackContext):

context.user_data["end"] = update.message.text

keyboard = [tech_list[i:i+2] for i in range(0,len(tech_list),2)]

update.message.reply_text(
"🔧 Выберите технику",
reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
)

return TECH

def tech(update: Update, context: CallbackContext):

context.user_data["tech"] = update.message.text

update.message.reply_text(
"👤 Представитель заказчика (или напишите 'нет')",
reply_markup=ReplyKeyboardRemove()
)

return REP

def rep(update: Update, context: CallbackContext):

context.user_data["rep"] = update.message.text

update.message.reply_text(
"📦 Оборудование и материалы (или 'нет')"
)

return EQUIP

def equip(update: Update, context: CallbackContext):

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
)
)

conn.commit()

keyboard = [["➕ Добавить ещё операцию"],["✅ Завершить отчет"]]

update.message.reply_text(
"✅ Операция добавлена\n\nЧто дальше?",
reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
)

return ACTION

def action(update: Update, context: CallbackContext):

text = update.message.text

if text == "➕ Добавить ещё операцию":

update.message.reply_text("📝 Введите название операции")

return NAME

else:

update.message.reply_text(
"✅ Отчет завершен\nСпасибо за работу 👋",
reply_markup=ReplyKeyboardRemove()
)

return ConversationHandler.END

def excel(update: Update, context: CallbackContext):

df = pd.read_sql_query("SELECT * FROM operations", conn)

file = "tkrs_report.xlsx"

df.to_excel(file,index=False)

update.message.reply_document(open(file,"rb"))

def main():

updater = Updater(TOKEN)

dp = updater.dispatcher

conv = ConversationHandler(

entry_points=[CommandHandler("start", start)],

states={

DATE:[MessageHandler(Filters.text,get_date)],
SHIFT:[MessageHandler(Filters.text,shift)],
NAME:[MessageHandler(Filters.text,name)],
START:[MessageHandler(Filters.text,start_time)],
END:[MessageHandler(Filters.text,end_time)],
TECH:[MessageHandler(Filters.text,tech)],
REP:[MessageHandler(Filters.text,rep)],
EQUIP:[MessageHandler(Filters.text,equip)],
ACTION:[MessageHandler(Filters.text,action)]

},

fallbacks=[]

)

dp.add_handler(conv)

dp.add_handler(CommandHandler("excel",excel))

updater.start_polling()

updater.idle()

if __name__ == "__main__":
main()