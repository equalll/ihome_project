# !/usr/bin/env python
# coding:utf-8

# @Time    : 18-4-14 下午7:47
# @Author  : LiGang
# @File    : config.py
# @Software: PyCharm
import logging
import redis


class Config(object):
	"""工程配置信息"""
	SECRET_KEY = "lgwjwlesfesfsefesfsa"

	DEBUG = True

	# 数据库配置信息
	SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/ihome"
	SQLALCHEMY_TRACK_MODIFICATIONS = False  # Ture和False均可压制警告信息,False可以降低数据库开销

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
	# 开发的时候是DEBUG级别
	DEBUG_LEVEL = logging.DEBUG


class ProductionConfig(Config):
	"""生产模式下的配置"""
	# 生产环境是ERROR级别
	DEBUG_LEVEL = logging.ERROR



config_dict = {
	"development": DevelopmentConfig,
	"production": ProductionConfig
}


