# !/usr/bin/env python
# coding:utf-8

# @Time    : 18-4-14 下午7:54
# @Author  : LiGang
# @File    : __init__.py.py
# @Software: PyCharm

import logging
from logging.handlers import RotatingFileHandler

import redis
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from config import config_dict
from ihome.utils.commons import RegexConverter


# 数据库
db = SQLAlchemy()
# redis
redis_store = None
# 开启csrf保护
csrf = CSRFProtect()


def create_app(config_name):
	"""通过传入不同的配置名字，初始化其对应配置的应用实例"""

	app = Flask(__name__)

	#通过配置名获取到配置类
	config = config_dict.get(config_name)

	# 将配置信息加载到app中
	app.config.from_object(config)

	# 初始化数据库
	db.init_app(app)

	# 设置redis
	global redis_store
	redis_store = redis.StrictRedis(host=config.REDIS_HOST,port=config.REDIS_PORT)

	# 创建日志记录文件
	log_file(config.DEBUG_LEVEL)

	# 开启session
	Session(app)

	# 开启csrf保护
	csrf.init_app(app)

	# 向app中添加自定义的路由转换器
	app.url_map.converters['re'] = RegexConverter

	# 注册蓝图
	import api_1_0  # 注意，蓝图在注册的时候在导入，否则可能会出现循环导入
	app.register_blueprint(api_1_0.api, url_prefix='/api/v1.0')  # url_prefix关键字参数（这个参数默认是/）,通过/api/v1.0可以访问到蓝图中定义的视图函数

	# 注册html静态文件蓝图
	import web_html
	app.register_blueprint(web_html.html)

	return app


def log_file(debug_level):
	# 常见的日志等级如下: DEBUG < INFO <Waring < ERROR
	# 比如,如果等级设置为INFO那么,大于等于INFO级别的才会显示
	# 设置日志的记录等级
	logging.basicConfig(level=debug_level)     # 调试debug级
	# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
	file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
	# 创建日志记录的格式                 日志等级    输入日志信息的文件名 行数    日志信息
	formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
	# 为刚创建的日志记录器设置日志记录格式
	file_log_handler.setFormatter(formatter)
	# 为全局的日志工具对象（flask app使用的）添加日记录器
	logging.getLogger().addHandler(file_log_handler)

