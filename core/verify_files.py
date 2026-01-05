# 依赖方法
from fastapi import UploadFile
from typing import Union
from entites.data_model import EnterDataReq_ZD, EnterDataReq_XD


def verify_file(file: UploadFile) -> UploadFile:
    """
    上传文件校验
    :param file:
    :return:
    """
    return file



# 单独的 ZD 数据校验函数
def verify_data_zd(data: EnterDataReq_ZD) -> EnterDataReq_ZD:
    """ZD 输入数据字段校验"""
    # 可添加 ZD 专属校验逻辑
    return data

# 单独的 XD 数据校验函数
def verify_data_xd(data: EnterDataReq_XD) -> EnterDataReq_XD:
    """XD 输入数据字段校验"""
    # 可添加 XD 专属校验逻辑
    return data

#
#
# def verify_data(data: Union[EnterDataReq_ZD,EnterDataReq_XD]) -> Union[EnterDataReq_ZD,EnterDataReq_XD]:
#     """
#     输入数据字段校验
#     :param data:
#     :return:
#     """
#
#     return data
