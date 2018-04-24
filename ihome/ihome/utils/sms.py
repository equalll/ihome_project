#coding=gbk

#coding=utf-8

#-*- coding: UTF-8 -*-  

from ihome.libs.yuntongxun.CCPRestSDK import REST
import ConfigParser

#主帐号
accountSid= '8aaf070862b902de0162cc7f389806f5';

#主帐号Token
accountToken= '9cbe8c35519841a78d9512a47a0091cd';

#应用Id
appId='8aaf070862b902de0162cc7f38f606fc';

#请求地址，格式如下，不需要写http://
serverIP='app.cloopen.com';

#请求端口 
serverPort='8883';

#REST版本号
softVersion='2013-12-26';

#将发送短信的过程变成一个单利类的形式
class CCP(object):
    #重写__new__方法
    def __new__(cls, *args, **kwargs):
        #判断cls是否有_instance属性,如果没有创建对象属性
        if not hasattr(cls,"_instance"):
            cls._instance = super(CCP, cls).__new__(cls,*args,**kwargs)
            # 初始化REST SDK
            cls._instance.rest = REST(serverIP, serverPort, softVersion)
            cls._instance.rest.setAccount(accountSid, accountToken)
            cls._instance.rest.setAppId(appId)
            return cls._instance

        return cls._instance

    #发送短信方法
    def sendTemplateSMS(self,to, datas, tempId):

        result = self.rest.sendTemplateSMS(to, datas, tempId)

        #如果返回0表示发送成功,如果返回-1发送失败
        if result["statusCode"] == "000000":
            return 0
        else:
            return -1

# 测试
# print CCP().rest
# print CCP().rest

# ccp = CCP()
# ccp.sendTemplateSMS("18610820967",["900789","5"],1)

  # 发送模板短信
  # @param to 手机号码
  # @param datas 内容数据 格式为列表例如：["内容",过期时间]，如不需替换请填 ''
  # @param $tempId 模板Id  提供的默认模板编号是1

# def sendTemplateSMS(to,datas,tempId):
#     rest = REST(serverIP, serverPort, softVersion)
#     rest.setAccount(accountSid, accountToken)
#     rest.setAppId(appId)
#     result = rest.sendTemplateSMS(to,datas,tempId)
#     for k,v in result.iteritems():
#
#         if k=='templateSMS' :
#                 for k,s in v.iteritems():
#                     print '%s:%s' % (k, s)
#         else:
#             print '%s:%s' % (k, v)
#
   
#sendTemplateSMS(手机号码,内容数据,模板Id)
# sendTemplateSMS("18210094341",["666666","5"],1)