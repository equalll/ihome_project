# !/usr/bin/env python
# coding:utf-8

# @Time    : 18-4-14 下午5:48
# @Author  : LiGang
# @File    : manage.py.py
# @Software: PyCharm

# -*- coding:utf-8 -*-
import redis
from flask import Flask
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)

class Config(object):
    """工程配置信息"""
    SECRET_KEY = "lgwjwl"

    DEBUG = True

    # 数据库配置信息
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/ihome"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis配置
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # flask_session配置信息
    SESSION_TYPE = "redis"
    SESSION_USE_SIGNER = True
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST,port=REDIS_PORT)
    PERMANENT_SESSION_LIFETIME = 86400  # session 的有效期，单位是秒





app.config.from_object(Config)
db = SQLAlchemy(app)
redis_store = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)
Session(app)
csrf = CSRFProtect(app)
manager = Manager(app)
Migrate(app,db)
manager.add_command('db',MigrateCommand)

@app.route('/index')
def index():
    return 'nihao'

if __name__ == '__main__':
    app.run()