# !/usr/bin/env python
# coding:utf-8

# @Time    : 18-4-14 下午5:48
# @Author  : LiGang
# @File    : manage.py.py
# @Software: PyCharm

# -*- coding:utf-8 -*-
import redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

class Config(object):
    """工程配置信息"""
    DEBUG = True

    # 数据库配置信息
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/ihome"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis配置
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379


app.config.from_object(Config)
db = SQLAlchemy(app)
redis_store = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)


@app.route('/index')
def index():
    return 'index'

if __name__ == '__main__':
    app.run()