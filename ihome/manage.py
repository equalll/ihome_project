# !/usr/bin/env python
# coding:utf-8

# @Time    : 18-4-14 下午5:48
# @Author  : LiGang
# @File    : manage.py.py
# @Software: PyCharm

# -*- coding:utf-8 -*-

from flask import Flask

app = Flask(__name__)

@app.route('/index')
def index():
    return 'index'

if __name__ == '__main__':
    app.run()