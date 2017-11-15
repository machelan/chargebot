#!/usr/bin/python3.4
# -- coding: utf-8 --
import os
import time

while True:
    ret = os.system('python3.4 bot.py')
    if int(ret) == 0:
        exit()
    time.sleep(1)