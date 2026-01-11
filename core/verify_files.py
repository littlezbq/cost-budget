# 依赖方法
from fastapi import UploadFile, HTTPException
from typing import Union
from entites.data_model import EnterDataReq_ZD, EnterDataReq_XD,EnterDataReq_DFX


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


# verify_files.py 末尾新增
# 单独的 DFX 数据校验函数
def verify_data_dfx(data: EnterDataReq_DFX) -> EnterDataReq_DFX:
    """DFX 输入数据字段校验"""
    # 自定义校验逻辑示例：
    # 1. 符合率数值范围校验（假设是 0-100 的百分比）
    numeric_fields = [
        data.工艺性符合率含装配_输入数值,
        data.加工要求符合率_输入数值,
        data.试验设备优选率_输入数值,
        data.装配返工率_输入数值,
        data.新增专用工装夹具_输入数值,

        data.二配件成本占比_输入数值,
        data.成件优选率_输入数值,
        data.单一来源占比_不含协议和特殊规定_输入数值,


        data.自制件CBB复用率_输入数值,
        data.标准化率_输入数值,
        data.材料优选率_输入数值,

        # DFS （Design For Service） 可维修性
        data.有寿件成本占比_输入数值,
        data.二配有寿件成本占比_输入数值,
        data.非必换报废件成本占比_输入数值,
        data. 维修返工_修_占比_输入数值
    ]
    for val in numeric_fields:
        if not (0 <= val <= 100):
            raise HTTPException(status_code=400, detail="符合率和占比数值必须在 0-100 之间！")

    # 2. 权重总和校验（保证所有权重加起来等于1）
    weight_fields = [
        data.工艺性符合率含装配_指标权重,
        data.加工要求符合率_指标权重,
        data.试验设备优选率_指标权重,
        data.装配返工率_指标权重,
        data.新增专用工装夹具_指标权重,

        data.二配件成本占比_指标权重,
        data.成件优选率_指标权重,
        data.单一来源占比_不含协议和特殊规定_指标权重,


        data.自制件CBB复用率_指标权重,
        data.标准化率_指标权重,
        data.材料优选率_指标权重,

        # DFS （Design For Service） 可维修性
        data.有寿件成本占比_指标权重,
        data.二配有寿件成本占比_指标权重,
        data.非必换报废件成本占比_指标权重,
        data. 维修返工_修_占比_指标权重
    ]
    total_weight = sum(weight_fields)
    # 允许微小误差（浮点精度问题）
    if not (abs(total_weight - 1.0) < 1e-6):
        raise HTTPException(status_code=400, detail=f"所有指标权重总和必须为1（当前总和：{total_weight}）！")

    return data