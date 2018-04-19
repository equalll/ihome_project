# !/usr/bin/env python
# coding:utf-8

# @Time    : 18-4-19 下午5:53
# @Author  : LiGang
# @File    : profile.py
# @Software: PyCharm

# 展示首页的用户名,个人信息页面, 上传图片, 修改用户名

from flask import current_app, jsonify
from flask import g
from flask import request
from flask import session

from ihome import constants
from ihome import db
from ihome.utils.commons import login_required
from ihome.models import User
from ihome.utils.commons import login_required, login_required, login_required
from ihome.utils.response_code import RET
from ihome.api_1_0 import api


# 功能描述: 显示首页的用户名
# 请求路径: /api/v1.0/session
# 请求方式: GET
# 请求参数: 无
@api.route("/session")
@login_required
def get_user_name():
    """
    1.获取到用户编号
    2.到数据库中查询用户的对象信息
    3.将用户对象内容,响应到前端页面中
    :return:
    """
    # 1.获取到用户编号
    user_id = g.user_id

    # 2.到数据库中查询用户的对象信息
    try:
        user =User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="数据库查询异常")

    if not user:
        return jsonify(errno=RET.DATAERR,errmsg="该用户不存在")

    # 3.将用户对象内容,响应到前端页面中
    return jsonify(errno=RET.OK,errmsg="获取成功",data={"user_id":user_id, "name":user.name})


# 功能描述: 展示个人信息
# 请求路径: /api/v1.0/user
# 请求方式: GET
# 请求参数: 无
@api.route('/user')
@login_required
def get_user_profile():
	"""
	# 1.获取到session中的手机号
	# 2.根据手机号查询用户的个人信息
	# 3.判断个人信息是否存在
	# 4.将个人信息转成字典格式
	# 5.将字典信息返回到前端页面展示
	"""
	# 1.获取到session中的手机号
	# mobile = session.get("mobile")
	user_id = g.user_id

	if not user_id:
		return jsonify(errno=RET.DATAERR, errmsg="用户状态信息过期")

	# 2.根据手机号查询用户的个人信息
	try:
		user = User.query.filter(User.id == user_id).first()
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="数据库查询异常")

	# 3.判断个人信息是否存在
	if not user:
		return jsonify(errno=RET.DATAERR, errmsg="该用户不存在")

	# 3.判断个人信息是否存在
	if not user:
		return jsonify(errno=RET.DATAERR,errmsg="用户信息已过期")

	# 4.将个人信息转成字典格式
		# 在模型类中定义方法实现

	# 5.将字典信息返回到前端页面展示
	return jsonify(errno=RET.OK,errmsg="获取成功",data=user.user_to_dict())


#功能描述: 上传头像
#请求路径: /api/v1.0/user/avatar
#请求方式: POST
#请求参数: 头像
@api.route("/user/avatar",methods=["POST"])
@login_required
def image_upload():
    """
    1.获取参数,头像, 用户编号
    2.校验参数
    3.调用工具类上传头像
    4.通过用户编号获取到用户对象
    5.将图片名称更新到用户对象
    6.提交用户对象到数据库中
    7.返回状态信息到前端页面
    :return:
    """
    # 1.获取参数,头像, 用户编号
    user_id = g.user_id
    image_data = request.files.get("avatar").read() #获取文件使用的是request.files方式

    # 2.校验参数
    if not all([user_id, image_data]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不完整")

    # 3.调用工具类上传头像
    try:
        image_name = image_storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg="七牛云上传失败")

    # 4.通过用户编号获取到用户对象
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return  jsonify(errno=RET.DBERR,errmsg="数据库查询异常")

    # 5.将图片名称更新到用户对象
    user.avatar_url = image_name

    # 6.提交用户对象到数据库中
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg="用户头像保存异常")

    # 7.返回状态信息到前端页面
    avatar_url = constants.QINIU_DOMIN_PREFIX + user.avatar_url
    return jsonify(errno=RET.OK,errmsg="头像上传成功",data={"avatar_url":avatar_url})


#功能描述: 修改用户名
#请求路径: /api/v1.0/user/name
#请求方式: POST/PUT都可以
#请求参数: 无
@api.route("/user/name",methods=["PUT"])
@login_required
def set_user_name():
    """
    1.获取用户编号,用户名
    2.通过用户编号在数据库中查询用户对象
    3.判断用户是否存在
    4.将用户对象的信息用户名,进行更新
    5.保存到数据库
    6.返回
    :return:
    """
    # 1.获取用户编号,用户名
    user_id = g.user_id
    username = request.json.get("name")

    # 2.通过用户编号在数据库中查询用户对象
    try:
        user = User.query.filter(User.id == user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="数据库查询异常")

    # 3.判断用户是否存在
    if not user:
        return jsonify(errno=RET.DATAERR,errmsg="该用户不存在")

    # 4.将用户对象的信息用户名,进行更新
    user.name = username

    # 5.保存到数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="数据更新异常")

    # 6.返回
    return jsonify(errno=RET.OK,errmsg="保存用户名成功")


