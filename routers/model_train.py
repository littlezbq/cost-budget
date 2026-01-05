import sys
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
import asyncio
from functools import partial

# ===================== 全局配置 =====================
router = APIRouter(prefix="/model/train", tags=["模型训练总入口"])
# # 训练代码根路径（根据你的实际路径修改，统一配置）
# TRAIN_CODE_ROOT = r"cost-budget\Job01\训练模型code"
# sys.path.append(os.path.abspath(TRAIN_CODE_ROOT))


# ===================== 【公共模型】基础请求体（抽离通用字段） =====================
class BaseTrainRequest(BaseModel):
    file_path: str = Field(..., description="本产品上传接口返回的Excel绝对路径")


# ===================== ✅ 产品一：ZD单筒 专属训练接口 =====================
# 产品一目标变量下拉选项（按需修改为你的实际选项）
TARGET = Literal["总成本预测模型", "直接材料成本预测模型", "直接人工和制造费用成本预测模型"]


class ZDSingleTrainRequest(BaseTrainRequest):
    target_var: TARGET = Field(..., description="产品一(ZD单筒)目标变量（下拉选择）")


# 导入产品一/二共用的ZD训练函数
from Job01.训练模型code.ZD_XGBoost import train_and_save_zd_model


@router.post("/zd-single", summary="【产品一】ZD单筒模型训练（专属接口）")
async def train_zd_single(request: ZDSingleTrainRequest):
    try:
        # 1. 校验文件存在
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=400, detail=f"文件不存在：{request.file_path}")

        # 2. ✅ 核心：接口固化绑定「单筒」，无需前端传参
        # train_result = train_and_save_zd_model(
        #     file_path=request.file_path,
        #     k=request.target_var,
        #     zd_type="单筒"  # 产品一 永久绑定 单筒，写死传参
        # )
        # 接口内调用训练函数时，改为异步执行（示例）
        train_func = partial(train_and_save_zd_model, file_path=request.file_path, k=request.target_var, zd_type="单筒")
        train_result = await asyncio.to_thread(train_func)

        return {
            "code": 200,
            "msg": "【产品一】ZD单筒模型训练成功",
            "data": train_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"【产品一】训练失败：{str(e)}")


# ===================== ✅ 产品二：ZD双筒 专属训练接口 =====================
# 产品二目标变量下拉选项（和产品一一致可复用，不一致则单独定义）



class ZDDoubleTrainRequest(BaseTrainRequest):
    target_var: TARGET = Field(..., description="产品二(ZD双筒)目标变量（下拉选择）")


@router.post("/zd-double", summary="【产品二】ZD双筒模型训练（专属接口）")
async def train_zd_double(request: ZDDoubleTrainRequest):
    try:
        # 1. 校验文件存在
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=400, detail=f"文件不存在：{request.file_path}")

        # 2. ✅ 核心：接口固化绑定「双筒」，无需前端传参
        # train_result = train_and_save_zd_model(
        #     file_path=request.file_path,
        #     k=request.target_var,
        #     zd_type="双筒"  # 产品二 永久绑定 双筒，写死传参
        # )
        #
        # 接口内调用训练函数时，改为异步执行（示例）
        train_func = partial(train_and_save_zd_model, file_path=request.file_path, k=request.target_var, zd_type="双筒")
        train_result = await asyncio.to_thread(train_func)

        return {
            "code": 200,
            "msg": "【产品二】ZD双筒模型训练成功",
            "data": train_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"【产品二】训练失败：{str(e)}")


# ===================== ✅ 产品三：XD 专属训练接口 =====================
# 产品三目标变量下拉选项（XD专属，按需修改为你的实际下拉值）



class XDTrainRequest(BaseTrainRequest):
    target_var: TARGET = Field(..., description="产品三(XD)目标变量（下拉选择）")

# 导入XD专属训练函数（你的XD训练代码文件，自行替换文件名）
from Job01.训练模型code.XD_XGBoost import train_and_save_xd_model

@router.post("/xd", summary="【产品三】XD模型训练（专属接口）")
async def train_xd(request: XDTrainRequest):
    try:
        # 1. 校验文件存在
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=400, detail=f"文件不存在：{request.file_path}")

        # 2. ✅ 核心：调用XD专属训练函数，无额外绑定参数（函数本身是XD专属）
        # train_result = train_and_save_xd_model(
        #     file_path=request.file_path,
        #     k=request.target_var  # XD函数无需zd_type，仅传文件路径+目标变量
        # )
        # 接口内调用训练函数时，改为异步执行（示例）
        train_func = partial(train_and_save_zd_model, file_path=request.file_path, k=request.target_var)
        train_result = await asyncio.to_thread(train_func)

        return {
            "code": 200,
            "msg": "【产品三】XD模型训练成功",
            "data": train_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"【产品三】训练失败：{str(e)}")