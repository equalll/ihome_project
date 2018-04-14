# !/usr/bin/env python
# coding:utf-8

# @Time    : 18-4-14 下午5:48
# @Author  : LiGang
# @File    : manage.py.py
# @Software: PyCharm

# -*- coding:utf-8 -*-
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager
from ihome import create_app,db

# 创建 app，并传入配置模式：development / production
app = create_app("development")
manager = Manager(app)
Migrate(app,db)
manager.add_command('db',MigrateCommand)

@app.route('/index')
def index():
    return 'nihao'

if __name__ == '__main__':
    app.run()