# !/usr/bin/env python
# coding:utf-8

# @Time    : 18-4-14 下午7:47
# @Author  : LiGang
# @File    : config.py
# @Software: PyCharm
import redis


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
	SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
	PERMANENT_SESSION_LIFETIME = 86400  # session 的有效期，单位是秒


class DevelopmentConfig(Config):
	"""开发模式下的配置"""
	DEBUG = True


class ProductionConfig(Config):
	"""生产模式下的配置"""
	pass



config = {
	"development": DevelopmentConfig,
	"production": ProductionConfig
}


