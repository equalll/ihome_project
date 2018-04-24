# !/usr/bin/env python
# coding:utf-8

# @Time    : 18-4-16 下午6:15
# @Author  : LiGang
# @File    : verify.py
# @Software: PyCharm
"""
# 功能:生成图片验证码, 短信验证码
"""

import re
import random
from flask import current_app
from flask import json
from ihome.models import User
from ihome.utils.sms import CCP
from . import api
from ihome.utils.captcha.captcha import captcha
from ihome import redis_store
from flask import request, make_response, jsonify
from ihome import constants
from ihome.utils.response_code import RET
import logging


# 功能描述: 获取图片验证码
# 请求路径: /api/v1.0/image_code
# 请求方式:GET
# 请求参数: 图片验证码编号
@api.route("/image_code")
def generate_image_code():
    # 获取到之前的id和当前的id
    pre_image_id = request.args.get('pre_id')
    cur_image_id = request.args.get('cur_id')
    # 生成验证码
    name, text, image = captcha.generate_captcha()
    current_app.logger.debug(text)
    try:
        # 删除之前的
        redis_store.delete('ImageCode_' + pre_image_id)
        # print "删除之前的验证码"
        # 保存当前的
        redis_store.set('ImageCode_' + cur_image_id,text,constants.IMAGE_CODE_REDIS_EXPIRES)
        # print "保存当前的验证码"
    except Exception as e:
        current_app.logger.debug(e)
        # 返回响应内容
        # print '保存图片验证码失败'  # for test
        return make_response(jsonify(errno=RET.DATAERR, errmsg='保存图片验证码失败'))
    else:
        resp = make_response(image)
        # 设置内容类型
        resp.headers['Content-Type'] = 'image/jpg'
        return resp


#功能描述: 发送短信验证码
#请求路径: /api/v1.0/sms_code
#请求发送: POST
#请求参数:手机号,图片验证码A, 图片验证码编号
@api.route("/sms_code",methods=['POST'])
def send_sms_code():
    """
    1.获取请求的参数
    2.判断参数是否为空
    3.判断手机号的格式是否正确
    4.根据图片验证码编号取出redis中的图片验证码B
    5.判断验证码A,B是否相等
    6.创建要发送的短信验证码
    6.调用方法发送短信
    7.将短信验证码存储到redis中
    8.返回获取状态给前端页面
    :return:
    """
    # 1.获取请求的参数
    json_data = request.data
    dict_data = json.loads(json_data)

    mobile = dict_data.get("mobile")
    image_code = dict_data.get("image_code")
    image_code_id = dict_data.get("image_code_id")

    # 2. 验证参数是否为空
    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整11')

    # 3 验证手机号是否合法
    if not re.match(r"^1[34578][0-9]{9}$", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号不合法222')

    # 4 验证图片验证码是否正确
    try:
        real_image_code = redis_store.get('ImageCode_'+image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据异常333')

    # 4.1 判断验证码是否存在
    if not real_image_code:
        return jsonify(errno=RET.DATAERR, errmsg='验证码已失效444')

    # 4.2 比较传入的验证码和本地验证码是否一致
    if image_code.lower() != real_image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg='图片验证码错误555')

    # 5. 删除本地图片验证码
    try:
        redis_store.delete('ImageCode_'+image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='删除本地图片验证码失败666')

    # 思考：在 send_sms_code 方法中的哪个位置去判断该用户手机号已注册最合理？
    # 根据公司业务需求,判断手机号已经存在的时候是否需要刷新验证码,选择放在第5步前面还是第5步后面
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if user is not None:
            return jsonify(errno=RET.DBERR, errmsg='该手机已注册')

    # 6. 生成短信验证码
    sms_code = "%06d" %random.randint(0, 1000000)
    # TODO 7. 发送验证码,后续再做,默认提示发送成功
    # return jsonify(errno=RET.OK, errmsg='发送验证码成功')

    # 7.调用方法发送短信
    # try:
    #     cpp = CCP()
    #     result = cpp.sendTemplateSMS(mobile,[sms_code,5],1)
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.THIRDERR,errmsg = "短信发送出错")
	#
    # # 判断是否发送成功
    # if result == -1:
    #     return jsonify(errno=RET.DATAERR,errmsg = "短信发送成功")
    current_app.logger.debug("短信验证码:"+sms_code)

    # 8.将短信存储到redis中
    try:
        redis_store.set('SMSCode_'+mobile,sms_code,constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg = "短信存储异常")

    # 9.返回获取状态给前段页面
    return jsonify(errno=RET.OK,errmsg = "短信验证码发送成功")