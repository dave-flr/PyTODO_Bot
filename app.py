import os
import telebot

from flask import Flask, request
from pony.orm import db_session, commit, TransactionIntegrityError

from models import Task, Chat, db

TOKEN = '987514099:AAFKLnBbQHgnIGBdGxpcoOGt598dei-v0_U'

app = Flask(__name__)
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Howdy, how are you doing?")


@bot.message_handler(commands=['add'])
def add_task(message):
    with db_session:
        try:
            Chat(id=message.chat.id, type=message.chat.type)
            commit()
        except TransactionIntegrityError:
            pass
        else:
            pass


bot.polling()
# @app.route('/' + TOKEN, methods=['POST'])
# def get_message():
#     bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
#     return "!", 200
#
#
# @app.route("/")
# def webhook():
#     bot.remove_webhook()
#     bot.set_webhook(url='https://your_heroku_project.com/' + TOKEN)
#     return "!", 200
#
#
# if __name__ == "__main__":
#     app.run(debug=True)
#     # server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
