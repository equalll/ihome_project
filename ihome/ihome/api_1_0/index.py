# !/usr/bin/env python
# coding:utf-8

# @Time    : 18-4-14 下午9:32
# @Author  : LiGang
# @File    : index.py
# @Software: PyCharm

from manage import app
from . import api



@api.route('/',methods=['GET','POST'])
def index():
	return '欢迎使用api_v1.0'
