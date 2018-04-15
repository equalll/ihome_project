# !/usr/bin/env python
# coding:utf-8

# @Time    : 18-4-15 下午4:35
# @Author  : LiGang
# @File    : commons.py
# @Software: PyCharm

from werkzeug.routing import BaseConverter

class RegexConverter(BaseConverter):
    """自定义正则转换器"""

    def __init__(self, url_map, *args):
        super(RegexConverter, self).__init__(url_map)
        self.regex = args[0]