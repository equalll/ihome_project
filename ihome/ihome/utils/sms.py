#coding=gbk

#coding=utf-8

#-*- coding: UTF-8 -*-  

from ihome.libs.yuntongxun.CCPRestSDK import REST
import ConfigParser

#���ʺ�
accountSid= '8aaf070862b902de0162cc7f389806f5';

#���ʺ�Token
accountToken= '9cbe8c35519841a78d9512a47a0091cd';

#Ӧ��Id
appId='8aaf070862b902de0162cc7f38f606fc';

#�����ַ����ʽ���£�����Ҫдhttp://
serverIP='app.cloopen.com';

#����˿� 
serverPort='8883';

#REST�汾��
softVersion='2013-12-26';

#�����Ͷ��ŵĹ��̱��һ�����������ʽ
class CCP(object):
    #��д__new__����
    def __new__(cls, *args, **kwargs):
        #�ж�cls�Ƿ���_instance����,���û�д�����������
        if not hasattr(cls,"_instance"):
            cls._instance = super(CCP, cls).__new__(cls,*args,**kwargs)
            # ��ʼ��REST SDK
            cls._instance.rest = REST(serverIP, serverPort, softVersion)
            cls._instance.rest.setAccount(accountSid, accountToken)
            cls._instance.rest.setAppId(appId)
            return cls._instance

        return cls._instance

    #���Ͷ��ŷ���
    def sendTemplateSMS(self,to, datas, tempId):

        result = self.rest.sendTemplateSMS(to, datas, tempId)

        #�������0��ʾ���ͳɹ�,�������-1����ʧ��
        if result["statusCode"] == "000000":
            return 0
        else:
            return -1

# ����
# print CCP().rest
# print CCP().rest

# ccp = CCP()
# ccp.sendTemplateSMS("18610820967",["900789","5"],1)

  # ����ģ�����
  # @param to �ֻ�����
  # @param datas �������� ��ʽΪ�б����磺["����",����ʱ��]���粻���滻���� ''
  # @param $tempId ģ��Id  �ṩ��Ĭ��ģ������1

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
   
#sendTemplateSMS(�ֻ�����,��������,ģ��Id)
# sendTemplateSMS("18210094341",["666666","5"],1)