#!/usr/bin/python3.4
# -- coding: utf-8 --
import config
import datetime
import re
import sys
import telebot
import threading


codes_dict = {}
members_dict = {}

bot = telebot.TeleBot(config.token)
admin_id = config.admin_id

log_lock = threading.Lock()
dict_lock = threading.Lock()
members_lock = threading.Lock()


def is_approver(id):
    return id in config.approvers


def get_id_by_username(username):
    for id, name in members_dict.items():
        if name == username:
            return id
    return 0


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
    codes_dict.clear()
    dict_lock.acquire()
    f = open('dict.txt', 'rb')
    lines = f.readlines()
    dict_lock.release()
    f.close()
    for line in lines:
        fields = line.split(b';')
        #codes_dict[fields[0].decode("utf-8")] = [fields[1], list(map(lambda x: int(x.decode("utf-8")), fields[2:]))]
        if fields[2] == b'\n':
            continue
        dict_value = list(map(lambda x: int(x.decode("utf-8")), fields[2:]))
        dict_value.insert(0, fields[1])
        codes_dict[fields[0].decode("utf-8")] = dict_value
    print(codes_dict)


def save_dict():
    global codes_dict
    dict_lock.acquire()
    f = open('dict.txt', 'wb')
    for key in codes_dict:
        line = key + ";" + codes_dict[key][0].decode("utf-8") + ";" + ';'.join(map(lambda x: str(x), codes_dict[key][1:])) + "\n"
        f.write(line.encode("utf-8"))
    f.close()
    dict_lock.release()


def load_members():
    global members_dict
    members_lock.acquire()
    f = open('members.txt', 'rb')
    lines = f.readlines()
    members_lock.release()
    f.close()
    for line in lines:
        fields = line.split(b';')
        members_dict[int(fields[0].decode("utf-8"))] = fields[1][:-1]
    print(members_dict)


def add_new_code(code, name):
    global codes_dict
    name = name.replace(';', ':')
    codes_dict[code] = [name.encode("utf-8")]
    print(codes_dict)


def add_new_id(code, id):
    global codes_dict
    id = int(id)
    if code not in codes_dict:
        return -1
    if id in codes_dict[code][1:]:
        return -2
    codes_dict[code].append(id)
    print(codes_dict[code])
    return 0


def quiting():
    bot.stop_polling()
    print(str(datetime.datetime.now()) + ' Poling stoped')


def recharging(message):
    res = re.findall(r'Recharge: \w* ', str(message.text))
    for entry in res:
        splited_entry = entry[:-1].split(' ', 1)
        dict_key = splited_entry[1]
        name = codes_dict.get(dict_key, 0)
        if name == 0:
            continue
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
    res = re.findall(r'DO NOT RECHARGE: \w* ', str(message.text))
    for entry in res:
        splited_entry = entry[:-1].split(' ', 1)
        dict_key = splited_entry[1]
        name = codes_dict.get(dict_key, 0)
        if name == 0:
            continue
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
    if is_approver(message.from_user.id) == False:
        return
    if len(message.text) < 15:
        return
    str_arr = message.text.split(' ', 2)
    code = str_arr[1]
    name = str_arr[2]
    add_new_code(code, name)
    bot.send_message(message.chat.id, code + ' ' + name + u' added')


@bot.message_handler(commands=['get_codes'])
def command_answer(message):
    log(message)
    if is_approver(message.from_user.id) == False:
        return
    text = ""
    for key in codes_dict:
        line = key + " : " + codes_dict[key][0].decode("utf-8") + "\n"
        text += line
    if text == "":
        text = "There are no codes here!"
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['delete_code'])
def command_answer(message):
    log(message)
    if is_approver(message.from_user.id) == False:
        return
    str_arr = message.text.split(' ', 1)
    if len(str_arr) is 1:
        return
    code =  str_arr[1]
    if codes_dict.pop(code, 0) == 0:
        bot.send_message(message.chat.id, code + u' not found')
        return
    bot.send_message(message.chat.id, code + u' deleted')


@bot.message_handler(commands=['delete_all'])
def command_answer(message):
    log(message)
    if is_approver(message.from_user.id) == False:
        return
    codes_dict.clear()
    bot.send_message(message.chat.id, 'All clear! Don\'t forget to save changes.')


@bot.message_handler(commands=['add_member'])
def command_answer(message):
    log(message)
    if is_approver(message.from_user.id) == False:
        return
    if len(message.text) < 17:
        return
    str_arr = message.text.split(' ', 2)
    code = str_arr[1]
    username = str_arr[2]
    username = username.encode("utf-8")
    print(username)
    id = get_id_by_username(username)
    if id is 0:
        bot.send_message(message.chat.id, username + u' did not press start')
        return
    ret = add_new_id(code, id)
    if ret == -1:
        bot.send_message(message.chat.id, code + u' not found')
        return
    elif ret == -2:
        bot.send_message(message.chat.id, code + u' already exist')
        return
    bot.send_message(message.chat.id, str_arr[2] + u' added to ' + code)


@bot.message_handler(commands=['get_members'])
def command_answer(message):
    log(message)
    if is_approver(message.from_user.id) == False:
        return
    text = ""
    for key in codes_dict:
        line = key + " : " + ', '.join(map(lambda x: members_dict[x].decode("utf-8"), codes_dict[key][1:])) + "\n"
        text += line
    if text == "":
        text = "Nobody's here!"
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['reload'])
def command_answer(message):
    log(message)
    if is_approver(message.from_user.id) == False:
        return
    load_dict()
    bot.send_message(message.chat.id, u"Base reloaded")


@bot.message_handler(commands=['get_joined'])
def command_answer(message):
    log(message)
    if is_approver(message.from_user.id) == False:
        return
    text = ""
    for key in members_dict:
        line = str(key) + " : " + members_dict[key].decode("utf-8") + "\n"
        text += line
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['start'])
def command_answer(message):
    log(message)
    if members_dict.get(message.chat.id, 0) != 0:
        return
    try:
        members_dict[message.chat.id] = message.from_user.username.encode("utf-8")
        line = str(message.chat.id) + ";" + message.from_user.username + "\n"
        line = line.encode('utf-8')
        print(line)
        members_lock.acquire()
        f = open('members.txt', 'ab')
        f.write(line)
        f.close()
        members_lock.release()
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log(error=str(exc_type) + ' ' + str(exc_value))


@bot.message_handler(commands=['save'])
def command_answer(message):
    log(message)
    if is_approver(message.from_user.id) == False:
        return
    save_dict()
    bot.send_message(message.chat.id, u"Changes commited")


@bot.channel_post_handler(regexp="DO NOT RECHARGE")
@bot.message_handler(regexp="DO NOT RECHARGE")
def handle_message(message):
    log(message)
    notrecharging(message)


@bot.channel_post_handler(regexp="Recharge")
@bot.message_handler(regexp="Recharge")
def handle_message(message):
    log(message)
    recharging(message)


@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):
    log(message)


@bot.channel_post_handler(content_types=["text"])
def repeat_all_posts(message):
    log(message)


def main_loop():
    try:
        print(str(datetime.datetime.now()) + ' Poling starting')
        load_dict()
        load_members()
        bot._TeleBot__skip_updates()
        bot.polling(none_stop=True, timeout=86400)
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

