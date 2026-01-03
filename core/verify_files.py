# 依赖方法
from fastapi import UploadFile

from entites.data_model import EnterDataReq, EnterDataReq


def verify_file(file: UploadFile) -> UploadFile:
    """
    上传文件校验
    :param file:
    :return:
    """
    return file


def verify_data(data: EnterDataReq) -> EnterDataReq:
    """
    输入数据字段校验
    :param data:
    :return:
    """

    return data
