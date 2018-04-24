# !/usr/bin/env python
# coding:utf-8

# @Time    : 18-4-14 下午9:31
# @Author  : LiGang
# @File    : __init__.py.py
# @Software: PyCharm

from flask import Blueprint

# 创建蓝图对象
api = Blueprint("api",__name__)

from . import index, verify, passport, profile, houses, orders
