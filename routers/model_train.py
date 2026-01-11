
import sys
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
import asyncio
from functools import partial
from core.path_store import path_store
# ===================== 全局配置 =====================
router = APIRouter(prefix="/model/train", tags=["模型训练总入口"])

# 映射字典：前端下拉选项 -> 模型实际需要的参数
TARGET_MAPPING = {
    "总成本预测模型": "总成本",
    "直接材料成本预测模型": "直接材料",
    "直接人工和制造费用成本预测模型": "直接人工+制造费用"
}


# ===================== 【公共模型】基础请求体（抽离通用字段） =====================
# class BaseTrainRequest(BaseModel):
#     file_path: str = Field(..., description="本产品上传接口返回的Excel绝对路径")
TARGET = Literal["总成本预测模型", "直接材料成本预测模型", "直接人工和制造费用成本预测模型"]

# ===================== ✅ 产品一：ZD单筒 专属训练接口 =====================




class ZDSingleTrainRequest_no_path(BaseModel):
    target_var: TARGET = Field(..., description="产品一(ZD单筒)目标变量（下拉选择）")


# 导入产品一/二共用的ZD训练函数
from Job01.训练模型code.ZD_XGBoost import train_and_save_zd_model,save_zd_model_permanent


@router.post("/zd-single", summary="【产品一】ZD单模型训练【无参自动版】→ 自动读取最新上传Excel，无需传文件路径")
async def train_zd_single_auto(request: ZDSingleTrainRequest_no_path):
    try:
        # 核心：自动读取最新上传的ZD单筒Excel路径
        file_path = path_store.read_path("upload_zddt_path")
        # 映射前端参数到模型实际参数
        model_k = TARGET_MAPPING.get(request.target_var)
        if not model_k:
            raise HTTPException(status_code=400, detail=f"未知的目标变量：{request.target_var}")

        # 原有训练逻辑完全复用
        loop = asyncio.get_event_loop()
        train_func = partial(
            train_and_save_zd_model,
            file_path=file_path,
            k=model_k,
            zd_type="单筒"
        )
        train_result = await loop.run_in_executor(None, train_func)

        return {
            "code": 200,
            "msg": "【产品一】ZD单筒模型训练成功（自动读取最新上传Excel，模型已保存到临时目录）",
            "data": train_result
        }
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"❌ 前置数据缺失：{str(e)} → 请先执行【产品一】ZD单筒批量上传！")
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=f"❌ 文件不存在：{str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"【产品一】训练失败：{str(e)}")



@router.post("/zddt_save_auto", summary="ZD单筒模型永久保存【无参】→自动读取最新训练的临时路径，无需传参")
async def api_save_zdst_perm_auto():
    try:
        # 这里需要你在train_and_save_zd_model里，把训练后的temp路径也写入path_store，如下：
        # 训练函数里加一行：path_store.write_path("zd_temp_model_path", temp_model_path)
        temp_model_path = path_store.read_path("zddt_temp_model_path")
        temp_excel_path = path_store.read_path("zddt_temp_excel_path")
        save_result = save_zd_model_permanent(temp_model_path, temp_excel_path,"单筒")
        return {"code": 200, "msg": "模型永久保存成功", "data": save_result}
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"❌ 请先执行ZD单筒模型训练！{str(e)}")


# ===================== ✅ 产品二：ZD双筒 专属训练接口 =====================
class ZDDoubleTrainRequest_no_path(BaseModel):
    target_var: TARGET = Field(..., description="产品二(ZD双筒)目标变量（下拉选择）")


# ===================== ✅ 新增：【产品二】ZD双筒 无参训练接口（自动读取最新上传的Excel） =====================
@router.post("/zd-double-auto", summary="【产品二】ZD双筒模型训练【无参自动版】→ 自动读取最新上传Excel，无需传文件路径")
async def train_zd_double_auto(request: ZDDoubleTrainRequest_no_path):
    try:
        # 核心：自动读取最新上传的ZD双筒Excel路径
        file_path = path_store.read_path("upload_zdst_path")
        # 映射前端参数到模型实际参数
        model_k = TARGET_MAPPING.get(request.target_var)
        if not model_k:
            raise HTTPException(status_code=400, detail=f"未知的目标变量：{request.target_var}")

        # 原有训练逻辑完全复用
        loop = asyncio.get_event_loop()
        train_func = partial(
            train_and_save_zd_model,
            file_path=file_path,
            k=model_k,
            zd_type="双筒"
        )
        train_result = await loop.run_in_executor(None, train_func)

        return {
            "code": 200,
            "msg": "【产品二】ZD双筒模型训练成功（自动读取最新上传Excel，模型已保存到临时目录）",
            "data": train_result
        }
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"❌ 前置数据缺失：{str(e)} → 请先执行【产品二】ZD双筒批量上传！")
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=f"❌ 文件不存在：{str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"【产品二】训练失败：{str(e)}")


# ===================== ✅ ZD双筒模型永久保存【无参自动版】 =====================
@router.post("/zdst_save_auto", summary="ZD双筒模型永久保存【无参】→自动读取最新训练的临时路径，无需传参")
async def api_save_zdst_perm_auto():
    try:
        # 这里需要你在train_and_save_zd_model里，把训练后的temp路径也写入path_store，如下：
        # 训练函数里加一行：path_store.write_path("zd_temp_model_path", temp_model_path)
        temp_model_path = path_store.read_path("zdst_temp_model_path")
        temp_excel_path = path_store.read_path("zdst_temp_excel_path")
        save_result = save_zd_model_permanent(temp_model_path, temp_excel_path,"双筒")
        return {"code": 200, "msg": "模型永久保存成功", "data": save_result}
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"❌ 请先执行ZD双筒模型训练！{str(e)}")



# ===================== ✅ 产品三：XD 专属训练接口 =====================
class XDTrainRequest_no_path(BaseModel):
    target_var: TARGET = Field(..., description="产品三(XD)目标变量（下拉选择）")


# 导入XD专属训练函数
from Job01.训练模型code.XD_XGBoost import train_and_save_xd_model,save_xd_model_permanent


# ===================== ✅ 新增：【产品三】XD 无参训练接口（自动读取最新上传的Excel） =====================
@router.post("/xd-auto", summary="【产品三】XD模型训练【无参自动版】→ 自动读取最新上传Excel，无需传文件路径")
async def train_xd_auto(request: XDTrainRequest_no_path):
    try:
        # 核心：自动读取最新上传的XD Excel路径
        file_path = path_store.read_path("upload_xd_path")
        # 映射前端参数到模型实际参数
        model_k = TARGET_MAPPING.get(request.target_var)
        if not model_k:
            raise HTTPException(status_code=400, detail=f"未知的目标变量：{request.target_var}")

        # 原有训练逻辑完全复用
        loop = asyncio.get_event_loop()
        train_func = partial(
            train_and_save_xd_model,
            file_path=file_path,
            k=model_k
        )
        train_result = await loop.run_in_executor(None, train_func)

        return {
            "code": 200,
            "msg": "【产品三】XD模型训练成功（自动读取最新上传Excel，模型已保存到临时目录）",
            "data": train_result
        }
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"❌ 前置数据缺失：{str(e)} → 请先执行【产品三】XD批量上传！")
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=f"❌ 文件不存在：{str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"【产品三】训练失败：{str(e)}")

# ===================== ✅ 新增：XD模型永久保存【无参自动版】 =====================
@router.post("/xd_save_auto", summary="XD模型永久保存【无参】→自动读取最新训练的临时路径，无需传参")
async def api_save_xd_perm_auto():
    try:
        temp_model_path = path_store.read_path("xd_temp_model_path")
        temp_excel_path = path_store.read_path("xd_temp_excel_path")
        save_result = save_xd_model_permanent(temp_model_path, temp_excel_path)
        return {"code": 200, "msg": "模型永久保存成功", "data": save_result}
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"❌ 请先执行XD模型训练！{str(e)}")