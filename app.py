import os
import telebot

from flask import Flask, request
from pony.orm import db_session, commit, TransactionIntegrityError, select, count
from pony.flask import Pony

from models import Task, Chat, db
from services import imgur_client, generate_qr, decode_qr, text_to_speech
from io import BytesIO
from telebot.apihelper import ApiException

TOKEN = '987514099:AAHj2pBjUtdcfAfyrivvrHvJNVv-RxcyEzI'
ME = 987514099

app = Flask(__name__)
bot = telebot.TeleBot(TOKEN)
Pony(app)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    with db_session:
        if not Chat.exists(id=str(message.chat.id)):
            add_new_chat(message)
        bot.reply_to(message, "Howdy, how are you doing?")


@bot.message_handler(commands=['add'])
def add_task(message):
    with db_session:
        try:
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
    with db_session:
        try:
            if not Chat.exists(id=str(message.chat.id)):
                add_new_chat(message)
            else:
                task_list = list(Task.select(
                    lambda t: t.chat.id == str(message.chat.id)))
                if len(task_list) == 0:
                    bot.reply_to(message, "Your TO-DO list is empty")
                    return
                all_tasks = "*This is your TO-DO List:* \n"
                for task in task_list:
                    all_tasks += "📍" + task.task + " \\`\\[" + str(task.id_in_chat) + "\\]\\`\n\n"
                bot.reply_to(message, all_tasks, parse_mode='markdown')
        except ApiException as e:
            print(str(e))
        else:
            pass


@bot.message_handler(commands=['del'])
def delete_a_task(message):
    with db_session:
        try:
            task_id = int(message.text.split("/del ", 1)[1])
            delete_a_task_by_id(task_id=task_id,
                                chat=str(message.chat.id))
        except IndexError as error:
            # is a group
            if not message.text.startswith("/del@Todo_taskBot"):
                return

            task_id = int(message.text.split("/del@Todo_taskBot ", 1)[1])
            delete_a_task_by_id(task_id=task_id,
                                chat=str(message.chat.id))
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


@bot.message_handler(commands=['qrcode'])
def generate_qr_code_method(message):
    try:
        if message.reply_to_message is not None:
            img = generate_qr(text=message.reply_to_message.text)
            send_qr_to_chat(image=img, chat_id=message.chat.id)
        else:
            text = message.text.split("/qrcode ", 1)[1]
            img = generate_qr(text)
            send_qr_to_chat(image=img, chat_id=message.chat.id)
    except IndexError as error:
        # If we got this error it means the command is empty
        pass


@bot.message_handler(commands=['qrdecode'])
def decode_qr_code_method(message):
    if message.reply_to_message is not None:
        if message.reply_to_message.photo is not None:
            file_info_url = bot.get_file_url(
                message.reply_to_message.photo[-1].file_id)

            qr_decoded = decode_qr(file_info_url)
            bot.reply_to(message, qr_decoded)


def send_qr_to_chat(image, chat_id):
    buf = BytesIO()
    image.save(buf, format='PNG')
    bytes_img = buf.getvalue()
    bot.send_photo(chat_id, bytes_img)  # send qr photo


@bot.message_handler(commands=['tts'])
def text_to_speech_method(message):
    try:
        if message.reply_to_message is not None:
            tts = text_to_speech(text=message.reply_to_message.text,
                                 lang='es',
                                 slow=False)
            send_tts_to_chat(audio=tts, chat_id=message.chat.id)
        else:
            text = message.text.split("/tts ", 1)[1]
            tts = text_to_speech(text=text,
                                 lang='es',
                                 slow=False)
            send_tts_to_chat(audio=tts, chat_id=message.chat.id)
    except IndexError as error:
        # If we got this error it means the command is empty
        pass


def send_tts_to_chat(audio, chat_id):
    mp3_bf = BytesIO()
    audio.write_to_fp(mp3_bf)
    bytes_audio = mp3_bf.getvalue()
    bot.send_voice(chat_id, bytes_audio)  # send voice note


@db_session
def delete_a_task_by_id(task_id, chat):
    real_task = list(Task.select(lambda t: t.chat.id ==
                                 chat and t.id_in_chat == task_id))
    Task[real_task[0].id].delete()


@db_session
def add_new_task(task, chat, complete):
    number_of_tasks_by_chat = select(
        t.id_in_chat for t in Task if t.chat.id == chat).max()
    Task(id_in_chat=1 if number_of_tasks_by_chat is None else number_of_tasks_by_chat + 1,
         task=task,
         chat=chat,
         complete=complete)
    # commit()


@db_session
def add_new_chat(message):
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
    # commit()


# bot.polling()

@app.route("/delete-webhook")
def delete_webhook():
    bot.remove_webhook()
    return {"status": "Webhook removed"}, 200


@app.route('/' + TOKEN, methods=['POST'])
def get_message():
    bot.process_new_updates(
        [telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://pytodobot.herokuapp.com/' + TOKEN)
    return "!", 200


if __name__ == "__main__":
    # app.run(debug=True)
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
