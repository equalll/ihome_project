# !/usr/bin/env python
# coding:utf-8

# @Time    : 18-4-23 上午9:12
# @Author  : LiGang
# @File    : orders.py
# @Software: PyCharm

# 功能:创建订单
# 功能:创建订单,获取订单,改变订单状态(接单,拒单),评论订单

from datetime import datetime
from flask import current_app
from flask import g
from flask import request, jsonify
from ihome import db, redis_store
from ihome.api_1_0 import api
from ihome.models import Order, House
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET


# 功能:创建订单
# 请求路径:/api/v1.0/orders
# 请求方式:post
# 请求参数:房屋编号,开始时间,结束时间
@api.route('/orders', methods=['post'])
@login_required
def submit_order():
	"""
	1.获取参数
	2.校验参数
	3.查询冲突订单
	4.创建订单
	5.设置订单参数
	6.提交到数据库
	7.返回响应信息给前端
	:return:
	"""
	# 1.获取参数
	user_id = g.user_id

	data_dict = request.json
	house_id = data_dict.get("house_id")
	start_date_str = data_dict.get("start_date")
	end_date_str = data_dict.get("end_date")

	# 2.校验参数
	if not all([house_id, start_date_str, end_date_str]):
		return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

	try:
		start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
		end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
		assert start_date < end_date, Exception('开始日期大于结束日期')
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.PARAMERR, errmsg="日期格式错误")

	# 判断房屋是否存在
	try:
		house = House.query.get(house_id)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="数据库查询异常")
	if not house:
		return jsonify(errno=RET.DATAERR, errmsg="该房屋不存在")

	# 判断房屋是否是当前登录用户的
	if user_id == house.user_id:
		return jsonify(errno=RET.ROLEERR, errmsg='不能预订自己的房屋')

	# 3.查询冲突订单
	try:
		orders = Order.query.filter(Order.house_id == house_id, start_date < Order.end_date,
									end_date > Order.begin_date).all()
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="数据库查询异常")

	if orders:
		return jsonify(errno=RET.DATAERR, errmsg="该时间段内已被预定")

	# 查询是否存在冲突的订单    # 讲义上面查询冲突订单的方式
	# try:
	# 	filters = [Order.house_id == house_id, Order.begin_date < end_date, Order.end_date > start_date]
	# 	count = Order.query.filter(*filters).count()
	# except Exception as e:
	# 	logging.error(e)
	# 	return jsonify(errno=RET.DBERR, errmsg='数据查询错误')
	#
	# if count > 0:
	# 	return jsonify(errno=RET.DATAERR, errmsg='该房屋已被预订')

	# 4.创建订单
	order = Order()
	days = (end_date - start_date).days
	amount = days * house.price

	# 5.设置订单参数
	order.user_id = g.user_id
	order.house_id = house_id
	order.begin_date = start_date
	order.end_date = end_date
	order.days = days
	order.house_price = house.price
	order.amount = amount

	# 6.提交到数据库
	try:
		db.session.add(order)
		db.session.commit()
	except Exception as e:
		current_app.logger.error(e)
		db.session.rollback()
		return jsonify(errno=RET.DBERR, errmsg="保存到数据库失败")

	# 7.返回响应信息给前端
	return jsonify(errno=RET.OK, errmsg="订单保存成功")


# 功能描述: 获取订单, (区分房东,房客)
# 请求路径: /api/v.0/orders
# 请求方式:get
# 请求参数：role角色
"""
一个接口实现两个功能：
以房东的身份查询订单：查询属于自己房子的订单
以房客的身份查询订单：查询自己预订的订单
"""


@api.route('/orders')
@login_required
def get_orders():
	"""
   1.获取参数,role
   2.校验参数
   3.判断角色类型,查询对应的订单
   4.将订单对象列表,转成字典列表
   5.响应,携带字典列表
   :return:
   """

	# 1.获取参数, role
	user_id = g.user_id
	role = request.args.get("role")

	# 2.校验参数
	if role not in ["custom", "landlord"]:
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

	# 3.判断角色类型, 查询对应的订单
	try:
		if role == "custom":
			# 查询当前自己下了哪些订单
			orders = Order.query.filter(Order.user_id == user_id).all()
		else:
			houses = House.query.filter(House.user_id == user_id).all()
			houses_ids = [house.id for house in houses]
			# 订单中的hosue_id在房子编号中就是房东的
			orders = Order.query.filter(Order.house_id.in_(houses_ids)).all()
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="数据库查询异常")

	if not orders:
		return jsonify(errno=RET.DATAERR, errmsg="您当前没有订单信息")

	# 4.将订单对象列表, 转成字典列表
	order_list = []
	for order in orders:
		order_list.append(order.to_dict())

	# 5.响应, 携带字典列表
	return jsonify(errno=RET.OK, errmsg="订单信息获取成功", data={"orders": order_list})


# 功能: 改变订单状态 (接单,拒单)
# 请求路径: /api/v1.0/orders/<int:order_id>
# 求方式: PUT
# 求参数: 订单编号,行为
"""
接单和拒单同一个接口，传处不同的 action 实现
action: accept(接单)，reject(拒单)
"""


@api.route('/orders/<int:order_id>', methods=['put'])
@login_required
def change_order_status(order_id):
	"""
	1.获取参数
	2.校验参数
	3.根据订单编号查询订单对象
	4.判断订单是否存在
	5.根据action的不同分别处理订单
	6.保存到数据库
	7.返回状态信息给前端
	:param order_id:
	:return:
	"""
	# 1.获取参数
	user_id = g.user_id
	action = request.args.get("action")

	# 2.校验参数
	if action not in ['accept', 'reject']:
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

	# 3.根据订单编号查询订单对象
	try:
		order = Order.query.filter(Order.id == order_id, Order.status == 'WAIT_ACCEPT').first()
		house = order.house
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg='查询数据库异常')

	# 4.判断订单是否存在并且当前房屋的用户id是当前用户的id
	if not order or house.user_id != user_id:
		return jsonify(errno=RET.DATAERR, errmsg='数据有误')

	# 5.根据action的不同分别处理订单
	if action == "accept":  # 接单
		order.status = 'WAIT_COMMENT'
	else:
		reason = request.json.get("reason")  # 获取拒单原因
		# if not reason:
		# 	return jsonify(errno=RET.PARAMERR, errmsg="未填写拒单原因")
		# 设置状态为拒单并且设置拒单原因
		order.status = 'REJECTED'
		order.comment = reason

	# 6.保存到数据库
	try:
		db.session.add(order)  # TODO是否需要有待考证
		db.session.commit()
	except Exception as e:
		current_app.logger.error(e)
		db.session.rollback()
		return jsonify(errno=RET.DBERR, errmsg="数据保存出现异常")

	# 7.返回状态信息给前端
	return jsonify(errno=RET.OK, errmsg="订单处理完成")


# 功能: 评论
# 请求路径:/api/v1.0/orders/<int:order_id>/comment
# 请求方式：post
# 请求参数：评论
@api.route('/orders/<int:order_id>/comment', methods=["POST"])
@login_required
def send_commnet(order_id):
	"""
    1.获评论信息
    2.根据订单编号,查询订单
    3.判断订单是否存在
    4.设置订单的评论信息,设置订单数据量+1
    5.响应
    :return:
    """
	# 1.获评论信息
	comment = request.json.get("comment")
	if not comment:
		return jsonify(errno=RET.PARAMERR, errmsg='请输入评论内容')

	# 2.根据订单编号,查询订单
	try:
		order = Order.query.filter(Order.id == order_id, Order.status == 'WAIT_COMMENT').first()
		# house = order.house    # 待理解
		house = House.query.get(order.house_id)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="订单查询失败")

	# 3.判断订单是否存在
	if not order:
		return jsonify(errno=RET.DATAERR, errmsg="该订单不存在")

	# 4.设置订单的评论信息
	order.status = "COMPLETE"
	order.comment = comment

	# 与该订单相关的房屋订单数量+1
	house.order_count += 1

	# 跟新数据库
	try:
		db.session.commit()
	except Exception as e:
		current_app.logger.error(e)
		db.session.rollback()
		return jsonify(errno=RET.DBERR, errmsg="更新数据库失败")

	# 删除redis中缓存的房屋详情信息,因为房屋详情信息已经更新
	try:
		redis_store.delete('house_info_' + house.id)
	except Exception as e:
		current_app.logger.error(e)

	# 5.响应
	return jsonify(errno=RET.OK, errmsg="更新成功")
