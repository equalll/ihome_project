# !/usr/bin/env python
# coding:utf-8

# @Time    : 18-4-15 下午4:22
# @Author  : LiGang
# @File    : web_html.py
# @Software: PyCharm
"""
需求:
    1. 如何使用全路径的静态文件路径方式, 直接主路径加上文件名就可以访问到资源了
    解决方式: current_app.send_static_file(文件名) ,  根据指定的文件名,找到static下面对应的资源

    2. 如果用户直接访问主路径,显示index首页页面
    比如: 127.0.0.1:5000  显示首页
    解决: 自定义转换器,使用正则来进行匹配, 拼接index.html

    3. 设置浏览器的默认图标
    当浏览器去加载web程序的时候,会自动在static中寻找favicon.ico的文件图标

"""""
from flask import Blueprint

html = Blueprint("html",__name__)