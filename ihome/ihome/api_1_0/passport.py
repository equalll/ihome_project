# !/usr/bin/env python
# coding:utf-8

# @Time    : 18-4-17 下午5:09
# @Author  : LiGang
# @File    : passport.py
# @Software: PyCharm

#coding:utf-8
import re

from flask import current_app
from werkzeug.security import generate_password_hash

from ihome.utils.commons import login_required
from . import api
from flask import request, jsonify, session
from ihome.utils.response_code import RET
from ihome import redis_store
from ihome.models import User
from ihome import db

import logging

#功能描述: 注册
#请求路径: /api/v1.0/user
#请求方式: POST
#请求参数: 手机号, 短信验证码,密码
@api.route('/user', methods=['POST'])
def register():
	"""
	1. 获取参数
	2. 判断是否为空
	3. 获取redis保存的短信验证码
	4. 验证对比,并删除验证码
	5. 将用户数据保存到数据库,并缓存到Session
	6. 返回用户信息
	:return:
	"""

	# 1. 获取参数
	dict_data = request.json
	mobile = dict_data.get("mobile")
	sms_code = dict_data.get("phoneCode")
	password = dict_data.get("password")

	# 2. 判断是否为空
	if not all([mobile,sms_code,password]):
		return jsonify(errno=RET.PARAMERR,errmsg="参数不完整")

	if not re.match(r"1[35678]\d{9}",mobile):
		return jsonify(errno=RET.DATAERR,errmsg="手机号格式错误")


	# 3. 获取redis保存的短信验证码
	try:
		redis_sms_code = redis_store.get('SMSCode_'+mobile)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg='短信验证码读取异常')

	if not redis_sms_code:
		return jsonify(errno=RET.DATAERR, errmsg='短信验证码已过期')

	# 4. 验证对比,并删除验证码
	# print sms_code
	# print type(sms_code)
	# print redis_sms_code
	if sms_code != redis_sms_code:
		return jsonify(errno=RET.DATAERR,errmsg="短信验证错误")

	# 5.删除短信验证码
	try:
		redis_store.delete('SMSCode_'+mobile)
	except Exception as e:
		# logging.error(e)
		current_app.logger.error(e)

	user = User()
	user.name = mobile  # 用户名默认是手机号
	user.mobile = mobile
	# TODO 手机号稍后处理, 不能以明文的形式存储
	# print user.password_hash
	user.password_hash = generate_password_hash(password)
	print user.password_hash

	# 7.保存到数据库中
	try:
		print "正在保存用户信息...."
		db.session.add(user)
		db.session.commit()
	except Exception as e:
		current_app.logger.error(e)
		db.session.rollback()
		return jsonify(errno=RET.DBERR, errmsg="用户保存异常")

	# 8.可以记录用户登录状态(通过session)
	session["user_id"] = user.id
	session["user_name"] = user.name
	session["mobile"] = user.mobile

	# 9.返回注册的结果给前端
	print "注册成功"
	return jsonify(errno=RET.OK,errmsg="注册成功")


#功能描述: 登录
#请求路径: /api/v1.0/session
#请求方式: POST
#请求参数: 用户名(手机号), 密码
@api.route("/session",methods=["POST"])
def login_user():
	"""
	1.获取参数
	2.校验参数
	3.根据用户名取出用户对象
	4.判断用户对象是否存在
	5.判断密码是否正确
	6.记录用户的登录信息(使用session进行保存)
	7.返回登录信息给前端
	:return:
	"""
	# 1.获取参数
	dict_data =  request.get_json()
	mobile = dict_data.get("mobile")
	password = dict_data.get("password")

	# 2.校验参数
	if not all([mobile,password]):
		return jsonify(errno=RET.PARAMERR,errmsg="参数不完整")

	# 3.判断手机号是否合法
	if not re.match(u"^1[34578]\d{9}$", mobile):
		return jsonify(errno=RET.PARAMERR, errmsg="手机号格式不正确")

	# 取出用户的登录错误次数,对用户输入错误密码的次数进行限制
	try:
		number =  redis_store.get("login_error_number:"+mobile)
		# print number,type(number)
	except Exception as e:
		current_app.logger.error(e)
		number = 0

	try:
		number = int(number)    # int() argument must be a string or a number, not 'NoneType',第一次登陆的时候会出现
	except Exception as e:
		current_app.logger.error(e)
		number = 0

	if number >= 5:
		return jsonify(errno=RET.DATAERR,errmsg="一分钟之后再试")

	# 3.根据用户名取出用户对象
	try:
		user =  User.query.filter(User.mobile == mobile).first()
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR,errmsg="用户获取失败")

	# 4.判断用户对象是否存在
	if not user:
		return jsonify(errno=RET.DATAERR,errmsg="该用户不存在")

	# 5.判断密码是否正确
	if not user.check_password(password):  # 模型类中定义的检测密码是否相等的方法
	# if not user.password_hash == password:  # 直接存储明文密码时候的检测

		#记录用户的出错次数 +　１
		redis_store.incr("login_error_number:"+mobile)# incr每次执行该方法，会将ｋｅｙ增加１
		redis_store.expire("login_error_number:"+mobile,60)#60秒中有效期

		return jsonify(errno=RET.DATAERR,errmsg="密码错误")

	# 6.记录用户的登录信息(使用session进行保存)
	session["user_id"] = user.id
	session["user_name"] = user.name
	session["mobile"] = user.mobile

	# 7.返回登录信息给前端
	return jsonify(errno=RET.OK,errmsg="登录成功")


#功能描述: 登出登录
#请求路径: /api/v1.0/session
#请求方式: DELETE
#请求参数: 无
@api.route('/session',methods=['DELETE'])
@login_required
def logput():
	session.pop('name',None)
	session.pop('mobile',None)
	session.pop('user_id',None)
	return jsonify(errno=RET.OK,errmsg="已退出")

