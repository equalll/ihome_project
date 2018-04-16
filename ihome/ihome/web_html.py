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
from flask import current_app
from flask.ext.wtf.csrf import generate_csrf

html = Blueprint("html",__name__)

# 使用蓝图装饰视图函数
@html.route("/<re(r'.*'):file_name>")
def get_html_page(file_name):
	# 判断是否是访问的根路径, 如果是根路径,拼接index.html
	if not file_name:
		file_name = "index.html"

	# 判断不是favicon.ico才进行拼接
	if file_name != "favicon.ico":
		file_name = "html/" + file_name

	response = current_app.send_static_file(file_name)
	# 给cookie中设置csrf_token
	token = generate_csrf()
	response.set_cookie("csrf_token", token)

	return response