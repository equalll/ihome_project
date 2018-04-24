# !/usr/bin/env python
# coding:utf-8

# @Time    : 18-4-20 下午4:28
# @Author  : LiGang
# @File    : houses.py
# @Software: PyCharm

"""
功能:获取城区信息,发布房屋信息,发布房屋图片,获取首页热门房源,获取房源详情信息,搜索房屋
"""
import datetime
from flask import current_app, jsonify
from flask import g
from flask import json
from flask import request
from flask import session
from ihome import constants
from ihome import redis_store, db
from ihome.api_1_0 import api
from ihome.models import Area, House, Facility, HouseImage, Order
from ihome.utils.commons import login_required
from ihome.utils.image_storage import image_storage
from ihome.utils.response_code import RET


# 功能描述：　获取城区信息
# 求路径：　/api/v1.0/areas
# 请求方式: GET
# 请求参数: 无
@api.route('/areas')
def get_areas():
	"""
	1.查询数据库的城区信息
	2.将城区信息装成字典
	3.响应给前端页面
	:return:
	"""
	# 0.先到redis中查询是否已经有城区信息了
	try:
		areas = redis_store.get("areas")
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="缓冲中没有区域信息")

	# 如果有内容,转成字典返回
	if areas:
		area_list = json.loads(areas)
		return jsonify(errno=RET.OK, errmsg="缓冲中获取地域信息成功", data=area_list)

	# 1.查询数据库的城区信息
	try:
		areas = Area.query.all()
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="数据库查询城区信息失败")

	if not areas:
		return jsonify(errno=RET.DATAERR, errmsg="数据库中城区信息不存在")

	# 2.将城区信息装成字典
	# 因为查询出来全是对象实例，不能直接进行 JSON 转化，所以定义一个数组保存所有对象的字典信息
	area_list = []
	for area in areas:
		area_list.append(area.to_dict())

	# 2.1 纯属数据到redis中
	try:
		redis_store.set("areas", json.dumps(area_list))
	except Exception as e:
		current_app.logger.error(e)

	# 3.响应给前端页面
	return jsonify(errno=RET.OK, errmsg="获取城区信息成功", data=area_list)


# 功能描述: 发布房屋的基本信息
# 请求路径: /api/v1.0/houses
# 请求方式: POST
# 请求参数: 价格,标题...等等
@api.route('/houses', methods=["post"])
@login_required
def set_house_info():
	"""
	1.获取用户编号
	2.获取房屋的基本信息, 设施信息
	3.校验参数
	4.房屋价格, 押金的整数处理
	5.创建房屋对象
	6.将房屋的基本信息设置到房屋对象中
	7.通过设施信息,取出设置列表,设置到房屋对象中
	8.设置房屋的主人
	9.更新内容数据库
	10.返回,携带房屋编号
	:return:
	"""
	# 1.获取用户编号
	user_id = g.user_id

	# 2.获取房屋的基本信息, 设施信息
	dict_data = request.json

	title = dict_data.get("title")
	price = dict_data.get("price")
	area_id = dict_data.get("area_id")
	address = dict_data.get("address")
	room_count = dict_data.get("room_count")
	acreage = dict_data.get("acreage")
	unit = dict_data.get("unit")
	beds = dict_data.get("beds")
	deposit = dict_data.get("deposit")
	min_days = dict_data.get("min_days")
	max_days = dict_data.get("max_days")
	facilities = dict_data.get("facility")

	# 3.校验参数
	if not all([title, price, area_id, address, room_count, acreage, unit, beds, deposit, min_days, max_days]):
		return jsonify(errno=RET.DATAERR, errmsg="参数不完整")

	# 4.房屋价格, 押金的整数处理
	# 由于在使用支付宝支付的时候,最小单位是分, 所以保存在数据库中的价格,单位是分
	try:
		price = int(float(price) * 100)
		deposit = int(float(deposit) * 100)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DATAERR, errmsg="单价或者押金格式不正确")

	# 5.创建房屋对象
	house = House()

	# 6.将房屋的基本信息设置到房屋对象中
	house.title = title
	house.price = price
	house.area_id = area_id
	house.address = address
	house.room_count = room_count
	house.acreage = acreage
	house.unit = unit
	house.beds = beds
	house.deposit = deposit
	house.min_days = min_days
	house.max_days = max_days

	# 7.通过设施信息,取出设施列表,设置到房屋对象中
	facilities = Facility.query.filter(Facility.id.in_(facilities)).all()
	house.facilities = facilities

	# 8.设置房屋的主人
	house.user_id = user_id

	# 9.更新内容数据库
	try:
		db.session.add(house)
		db.session.commit()
	except Exception as e:
		current_app.logger.error(e)
		db.session.rollback()
		return jsonify(errno=RET.DBERR, errmsg="数据保存异常")

	# 10.返回,携带房屋编号
	return jsonify(errno=RET.OK, errmsg="房屋发布成功", data={"house_id": house.id})


# 功能描述: 上传房屋的图片
# 请求路径: /api/v1.0/houses/[int:house_id]/images
# 请求方式: POST
# 请求参数: house_image(file)
@api.route('/houses/<int:house_id>/images', methods=["post"])
@login_required
def upload_house_images(house_id):
	"""
	1.获取参数
	2.验证
	3.通过house_id查询房屋对象
	4.通过七牛云上传图片获取返回的url
	5.设置房屋的默认图像图像
    6.创建房屋图片对象
    7.设置图片对象的房屋编号
    8.更新数据库
    9.返回,携带图片的url
	:param house_id:
	:return:
	"""
	# 1.获取参数
	image_data = request.files.get("house_image").read()

	# 2.验证
	if not image_data:
		return jsonify(errno=RET.PARAMERR, errmsg="请选择图片")

	# 3.通过house_id查询房屋对象
	try:
		house = House.query.filter(House.id == house_id).first()
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="查询房屋失败")

	if not house:
		return jsonify(errno=RET.DATAERR, errmsg="该房屋不存在")

	# 4.通过七牛云上传图片获取返回的url
	try:
		image_url = image_storage(image_data)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errnp=RET.THIRDERR, errmsg="七牛云上传图片失败")

	# 5.设置房屋的默认图像图像
	if not house.index_image_url:
		house.index_image_url = image_url

	# 6.创建房屋图片对象
	house_image = HouseImage()
	house_image.url = image_url

	# 7.设置图片对象的房屋编号
	house_image.house_id = house_id

	# 8.更新数据库
	try:
		db.session.add(house_image)
		db.session.commit()
	except Exception as e:
		current_app.logger.error(e)
		db.session.rollback()
		return jsonify(errno=RET.DBERR, errmsg="房屋图片保存失败")

	# 9.返回, 携带图片的url
	house_image_url = constants.QINIU_DOMIN_PREFIX + image_url
	return jsonify(errno=RET.OK, errmsg="房屋图片保存失败", data={"url": house_image_url})


# 功能描述: 获取热门房源
# 请求路径: /api/v1.0/houses/index
# 请求方式: GET
# 请求参数: 无
# 注:数据缓存到redis中
@api.route('/houses/index')
def get_index_houses():
	"""
	1.查询数据库排名前五的房子对象
	2,将房子信息转换成字典
	3,返回给前端,携带房子字典信息
	:return:
	"""
	# 先从redis中加载数据
	try:
		house_info = redis_store.get('home_page_house_info')
	except Exception as e:
		house_info = None
		current_app.logger.error(e)
	if house_info:
		# print house_info
		# print type(house_info)
		# data = eval(house_info)
		# print data
		# print type(data)        # for test
		return jsonify(errno=RET.OK, errmsg='OK', data=eval(house_info))  # eval可以直接将从redis中取出的字符串转换成列表

	# 1.查询数据库排名前的房子对象
	try:
		houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, msg="数据库查询异常")

	if not houses:
		return jsonify(errno=RET.DATAERR, msg="数据库暂时没有房源数据")

	# 2,将房子信息转换成字典
	house_list = []
	for house in houses:
		house_list.append(house.to_basic_dict())

	# 将房子信息缓存到redis中
	try:
		redis_store.setex('home_page_house_info', constants.HOME_PAGE_DATA_REDIS_EXPIRES, house_list)
	except Exception as e:
		current_app.logger.error(e)

	# 3,返回给前端,携带房子字典信息
	return jsonify(errno=RET.OK, errmsg="首页房源获取成功", data=house_list)


# 功能描述: 获取房源详情
# 请求路径: /api/v1.0/houses/<int:house_id>
# 请求方式: GET
# 请求参数: house_id
# 注:
# 前端在房屋详情页面展示时，如果浏览页面的用户不是该房屋的房东，则展示预定按钮，否则不展示，
# 所以需要后端返回登录用户的user_id
# 尝试获取用户登录的信息，若登录，则返回给前端登录用户的user_id，否则返回user_id=-1
@api.route('/houses/<house_id>')
def get_house_detail(house_id):
	"""
	1.通过house_id查询房屋对象
	2.将房屋对象的信息转换成字典列表
	3.获取用户登录信息
	4.返回给前端,携带登录用户id
	:param house_id:
	:return:
	"""
	# 1.获取用户登录信息
	if not house_id:
		return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')

	user_id = session.get("user_id", -1)

	# 先从redis中读取缓存数据
	try:
		house_info = redis_store.get("house_info_" + house_id)
	except Exception as e:
		house_info = None
		current_app.logger.error(e)

	if house_info:
		current_app.logger.info("从redis中读取房屋信息成功")
		return jsonify(errno=RET.OK, errmsg="获取房屋信息成功", data={"house": eval(house_info), "user_id": user_id})

	# 2.没有缓存信息,就从数据库中通过house_id查询房屋对象
	try:
		house = House.query.filter(House.id == house_id).first()
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="查询数据库异常")
	if not house:
		return jsonify(errno=RET.DATAERR, errmsg="没有查到该房屋")

	# 2.将房屋对象的信息转换成字典列表
	house_info = house.to_full_dict()

	# 将数据缓存到redis中
	try:
		redis_store.setex("house_info_" + house_id, constants.HOUSE_LIST_REDIS_EXPIRES, house_info)
	except Exception as e:
		current_app.logger.error(e)

	resp = {"house": house_info, "user_id": user_id}
	# 4.返回给前端,携带登录用户id
	return jsonify(errno=RET.OK, errmsg="获取房屋详情成功", data=resp)


# 功能描述: 根据搜索条件搜索房屋
# 请求路径: /api/v1.0/houses/
# 请求方式: GET
# 请求参数: 区域编号，开始时间，结束时间，排序关键字，分页
@api.route('/houses')
def search_houses():
	"""
	1.获取参数
	2.校验参数
	3.
	:return:
	"""
	# 1.获取所有参数
	args = request.args
	area_id = args.get("aid", '')
	start_date_str = args.get("sd", '')
	end_date_str = args.get('ed', '')
	# booking(订单量),price_inc(低到高),price_desc(高到底)
	sort_key = args.get('sk', 'new')
	page = args.get('p', 1)

	# 参数校验
	try:
		page = int(page)
		start_date = None
		end_date = None
		if start_date_str:
			start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
		if end_date_str:
			end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
		# 如果开始时间大于或者等于结束时间,就报错
		if start_date and end_date:
			assert start_date < end_date, Exception('开始时间大于结束时间')
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

	# 查询redis,看是否有缓存数据
	try:
		redis_key = "houses_%s_%s_%s_%s" % (area_id, start_date_str, end_date_str, sort_key)
		response_data = redis_store.hget(redis_key, page)
		if response_data:
			current_app.logger.info('load data from redis')
			return jsonify(errno=RET.OK, errmsg='获取成功', data=eval(response_data))
	except Exception as e:
		current_app.logger.error(e)

	# 打印参数
	# print "area_id=%s,sd=%s,ed=%s,sk=%s,page=%s" % (area_id, start_date_str, end_date_str, sort_key, page)

	# 查询所有房屋
	# houses = House.query.all()

	# 查询房屋数据
	try:
		houses_query = House.query
		# 如果区域id存在
		if area_id:
			houses_query = houses_query.filter(House.area_id == area_id)

		# 增加时间筛选
		conflict_orders = []  # 定义数组保存冲突的订单
		if start_date and end_date:
			# 如果订单的开始时间 < 结束时间 and 订单的结束时间 > 开始时间
			conflict_orders = Order.query.filter(start_date < Order.end_date, end_date > Order.begin_date)
		elif start_date:
			# 订单的结束时间 > 开始时间
			conflict_orders = Order.quert.filter(start_date < Order.end_date).all()
		elif end_date:
			# 订单的开始时间 < 开始时间
			conflict_orders = Order.query.filter(end_date > Order.begin_date).all()

		# 通过冲突的订单找出冲突的房子编号, 然后添加到查询条件中
		if conflict_orders:
			# 取到冲突订单的房屋id
			conflict_houses_id = [order.house_id for order in conflict_orders]
			# 添加条件:查询出来的房屋不包括冲突订单中的房屋id
			houses_query = houses_query.filter(House.id__notin(conflict_houses_id))

		# 2.2判断排序的方式
		if sort_key == "booking":  # 订单量
			houses_query = houses_query.order_by(House.order_count.desc())
		elif sort_key == "price-inc":  # 低到高
			houses_query = houses_query.order_by(House.price.asc())
		elif sort_key == "price-des":  # 高到底
			houses_query = houses_query.order_by(House.price.desc())
		else:
			houses_query = houses_query.order_by(House.create_time.desc())
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="数据库查询异常")

	# 使用paginate进行分页
	house_pages = houses_query.paginate(page, constants.HOUSE_LIST_PAGE_CAPACITY, False)
	# 获取当前页对象
	houses = house_pages.items
	# 获取总页数
	total_page = house_pages.pages

	# 将房屋信息转换成字典列表
	house_list = []
	if houses:
		for house in houses:
			house_list.append(house.to_basic_dict())

	resp = {"houses": house_list, "total_page": total_page}

	# 提示 resp 用于缓存
	# if len(house_list) != 0:           # 判定条件一
	# 如果当前page小于总页数,则表明有数据
	if page <= total_page:  # 判定条件二
		# 将查询到的信息缓存到redis中
		try:
			# 获取管道对象, 用来做事物操作
			pipeline = redis_store.pipeline()
			# 开始事物
			pipeline.multi()
			redis_key = "search_%s_%s_%s_%s" % (area_id, sort_key, start_date, end_date)
			# 存储数据,设置有效期
			pipeline.hset(redis_key, page, resp)
			pipeline.expire(redis_key, constants.HOUSE_LIST_REDIS_EXPIRES)
			# 提交事物
			pipeline.execute()
		except Exception as e:
			current_app.logger.error(e)
			return jsonify(errno=RET.DBERR, errmsg="数据缓存失败")

	# 返回给前端
	return jsonify(errno=RET.OK, errmsg="请求成功", data=resp)
