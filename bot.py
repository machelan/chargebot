#!/usr/bin/python3.4
# -- coding: utf-8 --
import config
import telebot
import datetime
import sys
import threading
import re

#codes_dict = {'A01': ['Michael Glinka by Unknown Author', 91531717],'A02': ['Powerful Art ', 91531717]}
codes_dict = {}

bot = telebot.TeleBot(config.token)
admin_id = config.admin_id
shell_enable = 0
log_lock = threading.Lock()
dict_lock = threading.Lock()


def log(message=None, error=None):
    if message is not None:
        if message.chat.type == 'channel':
            line = str(datetime.datetime.now()) + ' ' + message.chat.title + ': ' + message.text + '\"\n'
        else:
            user = message.from_user
            first_name = user.first_name
            if first_name is None:
                first_name = 'None'
            first_name = first_name.encode('utf-8').decode('utf-8')
            last_name = user.last_name
            if last_name is None:
                last_name = 'None'
            last_name = last_name.encode('utf-8').decode('utf-8')
            line = str(datetime.datetime.now()) + ' ' + first_name + ' ' + last_name + u' id:'\
                + str(user.id) + u' in chat id: ' + str(message.chat.id) + u' wrote \"' + message.text + '\"\n'
    elif error is not None:
        line = str(datetime.datetime.now()) + ' ' + error + '\n'
    else:
        line = str(datetime.datetime.now()) + ' log with empty params'
    line = line.encode('utf8')
    log_lock.acquire()
    f = open('log.txt', 'ab')
    print(line)
    f.write(line)
    f.close()
    log_lock.release()


def load_dict():
    global codes_dict
    dict_lock.acquire()
    f = open('dict.txt', 'rb')
    lines = f.readlines()
    dict_lock.release()
    f.close()
    for line in lines:
        fields = line.split(b';')
        #codes_dict[fields[0].decode("utf-8")] = [fields[1], list(map(lambda x: int(x.decode("utf-8")), fields[2:]))]
        dict_value = list(map(lambda x: int(x.decode("utf-8")), fields[2:]))
        dict_value.insert(0, fields[1])
        codes_dict[fields[0].decode("utf-8")] = dict_value
    print(codes_dict)


def add_new_code(code):
    global codes_dict
    codes_dict[code] = 0
    print(codes_dict)


def quiting():
    bot.stop_polling()
    print(str(datetime.datetime.now()) + ' Poling stoped')


def recharging(message):
    res = re.findall(r': [A-Z]\d\d', str(message.text))
    for entry in res:
        dict_key = entry[2::]
        name = codes_dict.get(dict_key, 0)
        if name != 0:
            print('Charge ' + name[0].decode("utf-8"))
            id_arr = name[1:]
            for teleg_id in id_arr:
                try:
                    bot.send_message(teleg_id, u'Чардж портал ' + dict_key + ' ' + name[0].decode("utf-8"))
                except Exception:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    log(error=str(exc_type) + ' ' + str(exc_value))


def notrecharging(message):
    res = re.findall(r': [A-Z]\d\d', str(message.text))
    for entry in res:
        dict_key = entry[2::]
        name = codes_dict.get(dict_key, 0)
        if name != 0:
            print('Do not ' + name[0].decode("utf-8"))
            id_arr = name[1:]
            for teleg_id in id_arr:
                try:
                    bot.send_message(teleg_id, u'Не чардж портал ' + dict_key + ' ' + name[0].decode("utf-8"))
                except Exception:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    log(error=str(exc_type) + ' ' + str(exc_value))


@bot.message_handler(commands=['exit'])
def command_answer(message):
    log(message)
    if message.from_user.id == admin_id:
        bot.send_message(message.chat.id, u'Выключаюсь')
        quiting()
        sys.exit(0)


@bot.message_handler(commands=['add_code'])
def command_answer(message):
    log(message)
    fields = message.text.split(' ')
    if len(fields) > 1:
        add_new_code(fields[1])
        bot.send_message(message.chat.id, fields[1] + u' added')


@bot.message_handler(commands=['get_codes'])
def command_answer(message):
    log(message)
    if message.from_user.id == admin_id:
        bot.send_message(message.chat.id, '\n'.join(codes_dict.keys()))


@bot.message_handler(commands=['start'])
def command_answer(message):
    log(message)


@bot.message_handler(regexp="DO NOT RECHARGE")
def handle_message(message):
    log(message)
    notrecharging(message)


@bot.message_handler(regexp="Recharge")
def handle_message(message):
    log(message)
    recharging(message)


@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):
    log(message)


@bot.channel_post_handler(regexp="Recharge")
def handle_message(message):
    log(message)
    recharging(message)


@bot.channel_post_handler(regexp="DO NOT RECHARGE")
def handle_message(message):
    log(message)
    notrecharging(message)


@bot.channel_post_handler(content_types=["text"])
def repeat_all_posts(message):
    log(message)


def main_loop():
    try:
        print(str(datetime.datetime.now()) + ' Poling starting')
        load_dict()
        #bot._TeleBot__skip_updates()
        bot.polling(none_stop=True)
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log(error=str(exc_type) + ' ' + str(exc_value))
        bot.send_message(admin_id, 'Я в беде!')
        quiting()
        return -1
    return 0


if __name__ == '__main__':
    ret = main_loop()
    sys.exit(ret)

