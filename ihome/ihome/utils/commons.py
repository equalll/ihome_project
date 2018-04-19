# !/usr/bin/env python
# coding:utf-8

# @Time    : 18-4-15 下午4:35
# @Author  : LiGang
# @File    : commons.py
# @Software: PyCharm
import functools

from flask import g
from flask import session, jsonify
from werkzeug.routing import BaseConverter

from ihome.utils.response_code import RET


class RegexConverter(BaseConverter):
    """自定义正则转换器"""

    def __init__(self, url_map, *args):
        super(RegexConverter, self).__init__(url_map)
        self.regex = args[0]


def login_required(f):
    """
    用户是否登录判断装饰器
    :param f: 其装饰的函数
    :return: 装饰器
    """
    @functools.wraps(f)   # @functools.wraps(f) 这句代码可以防止装饰器更改原函数的 __name__ 属性
    def wrapper(*args, **kwargs):
        # 从 session 中获取当前用户 id
        g.user_id = session.get('user_id')
        # 如果user_id为None代表用户没有登录,直接返回未登录信息
        if g.user_id:
            return f(*args,**kwargs)
        else:
            return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    return wrapper