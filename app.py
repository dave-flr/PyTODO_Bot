import os
import telebot

from flask import Flask, request
from pony.orm import db_session, commit, TransactionIntegrityError, select, count

from models import Task, Chat, db
from services import imgur_client

TOKEN = '987514099:AAHj2pBjUtdcfAfyrivvrHvJNVv-RxcyEzI'
ME = 987514099

app = Flask(__name__)
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    with db_session:
        if not Chat.exists(id=str(message.chat.id)):
            add_new_chat(message)
    bot.reply_to(message, "Howdy, how are you doing?")


@bot.message_handler(commands=['add'])
def add_task(message):
    try:
        with db_session:
            if Chat.exists(id=str(message.chat.id)):
                if message.reply_to_message is not None:
                    if message.reply_to_message.from_user.id == ME:
                        bot.reply_to(message, "Cannot save my own messages")
                        return
                    add_new_task(task=message.reply_to_message.text,
                                 chat=str(message.chat.id),
                                 complete=False)
                    bot.reply_to(message, "Task was added.")
                else:
                    task = message.text.split("/add ", 1)[1]
                    add_new_task(task=task,
                                 chat=str(message.chat.id),
                                 complete=False)
                    bot.reply_to(message, "Task was added.")
            else:
                add_new_chat(message)
    except TransactionIntegrityError as e:
        print(str(e))
    except IndexError as error:
        # is a group
        if not message.text.startswith("/add@Todo_taskBot"):
            return
        task = message.text.split("/add@Todo_taskBot ", 1)[1]
        add_new_task(task=task,
                     chat=str(message.chat.id),
                     complete=False)
        bot.reply_to(message, "Task was added.")
    else:
        pass


@bot.message_handler(commands=['tasks'])
def list_all_task(message):
    try:
        with db_session:
            if not Chat.exists(id=str(message.chat.id)):
                add_new_chat(message)
            else:
                task_list = list(Task.select(
                    lambda t: t.chat.id == message.chat.id))
                if len(task_list) == 0:
                    bot.reply_to(message, "Your TO-DO list is empty")
                    return
                all_tasks = "*This is your TO-DO List:* \n"
                for task in task_list:
                    all_tasks += "📍" + task.task + \
                                 " `[" + str(task.id_in_chat) + "]`\n\n"
                bot.reply_to(message, all_tasks, parse_mode='markdown')
    except IndexError:
        pass
    else:
        pass


@bot.message_handler(commands=['del'])
def delete_a_task(message):
    try:
        task_id = int(message.text.split("/del ", 1)[1])
        delete_a_task_by_id(task_id=task_id,
                            chat=message.chat.id)
    except IndexError as error:
        # is a group
        if not message.text.startswith("/del@Todo_taskBot"):
            return

        task_id = int(message.text.split("/del@Todo_taskBot ", 1)[1])
        delete_a_task_by_id(task_id=task_id,
                            chat=message.chat.id)
        bot.reply_to(message, "Task was deleted.")
    else:
        bot.reply_to(message, "Task was deleted.")


# Upload an image to Imgur
@bot.message_handler(commands=['imgur'])
def upload_to_imgur(message):
    if message.reply_to_message is not None:
        if message.reply_to_message.photo is not None:
            file_info_url = bot.get_file_url(
                message.reply_to_message.photo[-1].file_id)

            # Upload the Image
            image = imgur_client.upload_from_url(file_info_url)
            bot.send_message(message.chat.id, image['link'])


@db_session
def delete_a_task_by_id(task_id, chat):
    real_task = list(Task.select(lambda t: t.chat.id == chat and t.id_in_chat == task_id))
    Task[real_task[0].id].delete()


def add_new_task(task, chat, complete):
    number_of_tasks_by_chat = select(t.id_in_chat for t in Task if t.chat.id == chat).max()
    with db_session:
        Task(id_in_chat=1 if number_of_tasks_by_chat is None else number_of_tasks_by_chat + 1,
             task=task,
             chat=chat,
             complete=complete)
        commit()


def add_new_chat(message):
    with db_session:
        Chat(id=str(message.chat.id),
             type=message.chat.type,
             title=message.chat.title,
             username=message.chat.username,
             first_name=message.chat.first_name,
             last_name=message.chat.last_name,
             photo=message.chat.photo,
             description=message.chat.description,
             invite_link=message.chat.invite_link,
             pinned_message=message.chat.pinned_message)
        commit()


# bot.polling()
# @app.route("/createdb")
# def create_db():
#     db.bind(provider='sqlite', filename='database.sqlite', create_db=True)
#     db.generate_mapping(create_tables=True)
#     return {'Success': 'ok'}, 200


@app.route("/delete-webhook")
def delete_webhook():
    bot.remove_webhook()
    return {"status": "Webhook removed"}, 200


@app.route('/' + TOKEN, methods=['POST'])
def get_message():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://pytodobot.herokuapp.com/' + TOKEN)
    return "!", 200


if __name__ == "__main__":
    # app.run(debug=True)
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
