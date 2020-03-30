import os
import telebot

from flask import Flask, request
from pony.orm import db_session, commit, TransactionIntegrityError, select

from models import Task, Chat, db

TOKEN = 'XXX'

app = Flask(__name__)
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    with db_session:
        if not Chat.exists(id=str(message.chat.id)):
            add_new_chat(str(message.chat.id),
                         message.chat.type,
                         message.chat.title,
                         message.chat.username,
                         message.chat.first_name,
                         message.chat.last_name,
                         message.chat.photo,
                         message.chat.description,
                         message.chat.invite_link,
                         message.chat.pinned_message)
    bot.reply_to(message, "Howdy, how are you doing?")


@bot.message_handler(commands=['add'])
def add_task(message):
    try:
        with db_session:
            if Chat.exists(id=str(message.chat.id)):
                if message.reply_to_message is not None:
                    add_new_task(message.reply_to_message.text, str(message.chat.id), False)
                else:
                    task = message.text.split("/add ", 1)[1]
                    add_new_task(task, str(message.chat.id), False)
            else:
                add_new_chat(str(message.chat.id),
                             message.chat.type,
                             message.chat.title,
                             message.chat.username,
                             message.chat.first_name,
                             message.chat.last_name,
                             message.chat.photo,
                             message.chat.description,
                             message.chat.invite_link,
                             message.chat.pinned_message)
    except TransactionIntegrityError:
        pass
    except IndexError:
        pass  # Empty command
    else:
        pass


@bot.message_handler(commands=['task'])
def list_all_task(message):
    try:
        with db_session:
            if not Chat.exists(id=str(message.chat.id)):
                add_new_chat(str(message.chat.id),
                             message.chat.type,
                             message.chat.title,
                             message.chat.username,
                             message.chat.first_name,
                             message.chat.last_name,
                             message.chat.photo,
                             message.chat.description,
                             message.chat.invite_link,
                             message.chat.pinned_message)
            else:
                task_list = list(Task.select(lambda t: t.chat.id == message.chat.id))
                if len(task_list) == 0:
                    bot.reply_to(message, "Your TO-DO list is empty")
                    return
                all_tasks = "*This is your TO-DO List:* \n"
                for task in task_list:
                    all_tasks += "📍" + task.task + "\n\n"
                bot.reply_to(message, all_tasks, parse_mode='markdown')
    except IndexError:
        pass
    else:
        pass


def add_new_task(task, chat, complete):
    with db_session:
        Task(task=task,
             chat=chat,
             complete=complete)
        commit()


def add_new_chat(chat_id, chat_type, title, username, first_name, last_name, photo, description, invite_link,
                 pinned_message):
    with db_session:
        Chat(id=str(chat_id),
             type=chat_type,
             title=title,
             username=username,
             first_name=first_name,
             last_name=last_name,
             photo=photo,
             description=description,
             invite_link=invite_link,
             pinned_message=pinned_message)
        commit()


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
