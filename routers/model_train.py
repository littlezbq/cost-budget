
import sys
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
import asyncio
from functools import partial

# ===================== 全局配置 =====================
router = APIRouter(prefix="/model/train", tags=["模型训练总入口"])

# 映射字典：前端下拉选项 -> 模型实际需要的参数
TARGET_MAPPING = {
    "总成本预测模型": "总成本",
    "直接材料成本预测模型": "直接材料",
    "直接人工和制造费用成本预测模型": "直接人工+制造费用"
}


# ===================== 【公共模型】基础请求体（抽离通用字段） =====================
class BaseTrainRequest(BaseModel):
    file_path: str = Field(..., description="本产品上传接口返回的Excel绝对路径")


# ===================== ✅ 产品一：ZD单筒 专属训练接口 =====================
# 产品一目标变量下拉选项（按需修改为你的实际选项）
TARGET = Literal["总成本预测模型", "直接材料成本预测模型", "直接人工和制造费用成本预测模型"]


class ZDSingleTrainRequest(BaseTrainRequest):
    target_var: TARGET = Field(..., description="产品一(ZD单筒)目标变量（下拉选择）")


# 导入产品一/二共用的ZD训练函数
from Job01.训练模型code.ZD_XGBoost import train_and_save_zd_model,save_zd_model_permanent


@router.post("/zd-single", summary="【产品一】ZD单筒模型训练（专属接口）")
async def train_zd_single(request: ZDSingleTrainRequest):
    try:
        # 1. 校验文件存在
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=400, detail=f"文件不存在：{request.file_path}")

        # 2. 映射前端参数到模型实际参数
        model_k = TARGET_MAPPING.get(request.target_var)
        if not model_k:
            raise HTTPException(status_code=400, detail=f"未知的目标变量：{request.target_var}")

        # 3. 获取事件循环并执行训练函数
        loop = asyncio.get_event_loop()

        train_func = partial(
            train_and_save_zd_model,
            file_path=request.file_path,
            k=model_k,  # 使用映射后的参数
            zd_type="单筒"
        )
        train_result = await loop.run_in_executor(None, train_func)

        return {
            "code": 200,
            "msg": "【产品一】ZD单筒模型训练成功（模型已保存到临时目录）",
            "data": train_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"【产品一】训练失败：{str(e)}")


# ===================== ✅ 产品二：ZD双筒 专属训练接口 =====================
class ZDDoubleTrainRequest(BaseTrainRequest):
    target_var: TARGET = Field(..., description="产品二(ZD双筒)目标变量（下拉选择）")


@router.post("/zd-double", summary="【产品二】ZD双筒模型训练（专属接口）")
async def train_zd_double(request: ZDDoubleTrainRequest):
    try:
        # 1. 校验文件存在
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=400, detail=f"文件不存在：{request.file_path}")

        # 2. 映射前端参数到模型实际参数
        model_k = TARGET_MAPPING.get(request.target_var)
        if not model_k:
            raise HTTPException(status_code=400, detail=f"未知的目标变量：{request.target_var}")

        # 3. 获取事件循环并执行训练函数
        loop = asyncio.get_event_loop()

        train_func = partial(
            train_and_save_zd_model,
            file_path=request.file_path,
            k=model_k,  # 使用映射后的参数
            zd_type="双筒"
        )
        train_result = await loop.run_in_executor(None, train_func)

        return {
            "code": 200,
            "msg": "【产品二】ZD双筒模型训练成功（模型已保存到临时目录）",
            "data": train_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"【产品二】训练失败：{str(e)}")



@router.post("/zd_save", summary="ZD模型永久保存，单双筒共用（复制临时文件到永久目录）")
async def api_save_zd_perm(temp_model_path: str, temp_excel_path: str):
    try:
        save_result = save_zd_model_permanent(temp_model_path, temp_excel_path)
        return {"code": 200, "msg": "模型永久保存成功", "data": save_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"永久保存失败：{str(e)}")



# ===================== ✅ 产品三：XD 专属训练接口 =====================
class XDTrainRequest(BaseTrainRequest):
    target_var: TARGET = Field(..., description="产品三(XD)目标变量（下拉选择）")





# 导入XD专属训练函数
from Job01.训练模型code.XD_XGBoost import train_and_save_xd_model,save_xd_model_permanent


@router.post("/xd", summary="【产品三】XD模型训练（专属接口）")
async def train_xd(request: XDTrainRequest):
    try:
        # 1. 校验文件存在
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=400, detail=f"文件不存在：{request.file_path}")


        # 2. 映射前端参数到模型实际参数
        model_k = TARGET_MAPPING.get(request.target_var)
        if not model_k:
            raise HTTPException(status_code=400, detail=f"未知的目标变量：{request.target_var}")

        # 3. 获取事件循环并执行训练函数
        loop = asyncio.get_event_loop()

        train_func = partial(
            train_and_save_xd_model,
            file_path=request.file_path,
            k=model_k  # 使用映射后的参数
        )
        train_result = await loop.run_in_executor(None, train_func)

        return {
            "code": 200,
            "msg": "【产品三】XD模型训练成功（模型已保存到临时目录）",
            "data": train_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"【产品三】训练失败：{str(e)}")

@router.post("/xd_save", summary="XD模型永久保存（复制临时文件到永久目录）")
async def api_save_xd_perm(temp_model_path: str, temp_excel_path: str):
    try:
        save_result = save_xd_model_permanent(temp_model_path, temp_excel_path)
        return {"code": 200, "msg": "模型永久保存成功", "data": save_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"永久保存失败：{str(e)}")

