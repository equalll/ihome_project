# !/usr/bin/env python
# coding:utf-8

# @Time    : 18-4-16 下午6:15
# @Author  : LiGang
# @File    : verify.py
# @Software: PyCharm

# 注册 imagecode 路由
# 步骤：
	# 获取参数
	# 生成验证码
	# 删除之前验证码并保存当前验证码
	# 错误处理
	# 响应返回
import re

from . import api
from ihome.utils.captcha.captcha import captcha
from ihome import redis_store
from flask import request, make_response, jsonify
from ihome import constants
from ihome.utils.response_code import RET
import logging

@api.route("/image_code")
def generate_image_code():
    # 获取到之前的id和当前的id
    pre_image_id = request.args.get('pre_id')
    cur_image_id = request.args.get('cur_id')
    # 生成验证码
    name, text, image = captcha.generate_captcha()
    # print "生成验证码成功"
    try:
        # 删除之前的
        redis_store.delete('ImageCode_' + pre_image_id)
        # 保存当前的
        redis_store.set('ImageCode_' + cur_image_id,text,constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        logging.error(e)
        # 返回响应内容
        # print '保存图片验证码失败'
        return make_response(jsonify(errno=RET.DATAERR, errmsg='保存图片验证码失败'))
    else:
        resp = make_response(image)
        # print "1111111111111111"
        # 设置内容类型
        resp.headers['Content-Type'] = 'image/jpg'
        return resp


@api.route("/sms_code/<mobile>")
def send_sms_code(mobile):

    # 1. 获取参数
    image_code = request.args['text']
    image_code_id = request.args['id']

    # 2. 验证参数是否为空
    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 3 验证手机号是否合法
    if not re.match(r"^1[34578][0-9]{9}$", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号不合法')

    # 4 验证图片验证码是否正确
    try:
        real_image_code = redis_store.get('ImageCode_'+image_code_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据异常')

    # 4.1 判断验证码是否存在
    if not real_image_code:
        return jsonify(errno=RET.DATAERR, errmsg='验证码已过期')

    # 4.2 比较传入的验证码和本地验证码是否一致
    if image_code.lower() != real_image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg='图片验证码错误')

    # 5. 删除本地图片验证码
    try:
        redis_store.delete('ImageCode_'+image_code_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='删除本地图片验证码失败')

    # 6. 生成短信验证码
    sms_code = "%06d" %random.randint(0, 1000000)
    print sms_code
    # TODO 7. 发送验证码,后续再做,默认提示发送成功
    return jsonify(errno=RET.OK, errmsg='发送验证码成功')