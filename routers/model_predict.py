import os
import math
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import asyncio
from functools import partial
from typing import Any

# ===================== 全局配置 =====================
router = APIRouter(prefix="/model/predict", tags=["模型预测总入口"])

# ✅ 1. 模型路径规则【严格对齐你的训练代码保存路径】
BASE_OUTPUT_DIR = os.path.abspath("output")
MODEL_DIR_MAP = {
    # ZD单筒
    "zd-single": {
        "total_cost": os.path.join(BASE_OUTPUT_DIR, "zd_model"),
        "material": os.path.join(BASE_OUTPUT_DIR, "zd_model"),
        "manufacture_labour": os.path.join(BASE_OUTPUT_DIR, "zd_model")
    },
    # ZD双筒
    "zd-double": {
        "total_cost": os.path.join(BASE_OUTPUT_DIR, "zd_model"),
        "material": os.path.join(BASE_OUTPUT_DIR, "zd_model"),
        "manufacture_labour": os.path.join(BASE_OUTPUT_DIR, "zd_model")
    },
    # XD产品
    "xd": {
        "total_cost": os.path.join(BASE_OUTPUT_DIR, "xd_model"),
        "material": os.path.join(BASE_OUTPUT_DIR, "xd_model"),
        "manufacture_labour": os.path.join(BASE_OUTPUT_DIR, "xd_model")
    }
}

# ✅ 2. 导入预测函数（保持你的原有路径）
from Job01.ZD产品预测模型code.ZD_code.ZD_predict import batch_run_prediction as zd_run_prediction
from Job01.XD产品预测模型code.XD_code.XD_predict import batch_run_prediction as xd_run_prediction


# ===================== 核心工具函数：清洗inf/nan（解决JSON序列化报错） =====================
def clean_inf_nan(obj: Any) -> Any:
    """递归清洗结果中的inf/nan，替换为None（JSON兼容）"""
    if isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: clean_inf_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_inf_nan(item) for item in obj]
    else:
        return obj


# ===================== 请求体模型（保持不变） =====================
class PredictRequest(BaseModel):
    """所有预测接口通用请求体 → 前端固定传这4个参数"""
    file_path: str = Field(..., description="数据文件绝对路径（store_files下的Excel/JSON）")
    total_cost: str = Field(..., description="下拉选中的【总成本模型】文件名（如zddt_total_20260106.json）")
    material: str = Field(..., description="下拉选中的【直接材料模型】文件名（如zddt_material_20260106.json）")
    manufacture_labour: str = Field(..., description="下拉选中的【直接人工模型】文件名（如zddt_manlab_20260106.json）")


# ===================== 通用工具函数（核心修改：匹配test的model_map格式） =====================
def assemble_model_paths(product_key: str, req: PredictRequest) -> dict:
    """✅ 核心修改：返回和test一致的model_map（文件名+key为total_cost/material/manufacture_labour）
    :param product_key: 产品标识 zd-single/zd-double/xd
    :param req: 前端请求体
    :return: model_map → {"total_cost":文件名, "material":文件名, "manufacture_labour":文件名}
    """
    # 1. 构建模型文件路径（用于校验存在性）
    model_path_check = {
        "total_cost": os.path.join(MODEL_DIR_MAP[product_key]["total_cost"], req.total_cost),
        "material": os.path.join(MODEL_DIR_MAP[product_key]["material"], req.material),
        "manufacture_labour": os.path.join(MODEL_DIR_MAP[product_key]["manufacture_labour"], req.manufacture_labour)
    }

    # 2. 批量校验模型文件存在+格式
    for name, path in model_path_check.items():
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            raise HTTPException(status_code=404, detail=f"{name}模型文件不存在 → {abs_path}")
        if not abs_path.endswith(".json"):
            raise HTTPException(status_code=400, detail=f"{name}模型文件格式错误，仅支持.json → {path}")

    # 3. 校验数据文件存在
    data_file_path = os.path.abspath(req.file_path)
    if not os.path.exists(data_file_path):
        raise HTTPException(status_code=404, detail=f"预测数据文件不存在 → {data_file_path}")

    # 4. 返回和test完全一致的model_map（仅传文件名，非完整路径）
    model_map = {
        "total_cost": req.total_cost,
        "material": req.material,
        "manufacture_labour": req.manufacture_labour
    }
    return model_map


def get_async_loop():
    """✅ 兼容Python版本的异步循环（保持不变）"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


# ===================== 🔧 接口1：ZD单筒 预测接口（核心修改） =====================
@router.post("/zd-single", summary="【产品一】ZD单筒预测（专属接口）")
async def predict_zd_single(req: PredictRequest):
    try:
        # ✅ 步骤1：获取和test一致的model_map（文件名）
        model_map = assemble_model_paths("zd-single", req)
        data_file_path = os.path.abspath(req.file_path)

        # ✅ 步骤2：异步调用（指定参数名，匹配test的调用方式）
        loop = get_async_loop()
        call_func = partial(
            zd_run_prediction,
            file_path=data_file_path,  # 匹配test中的test_file_path参数
            model_map=model_map  # 匹配test中的model_map参数
        )
        pred_result = await loop.run_in_executor(None, call_func)

        # ✅ 步骤3：清洗inf/nan，解决JSON序列化报错
        cleaned_result = clean_inf_nan(pred_result)

        # ✅ 步骤4：返回清洗后的结果
        return {"code": 200, "msg": "ZD单筒预测成功", "data": cleaned_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ZD单筒预测失败：{str(e)}")


# ===================== 🔧 接口2：ZD双筒 预测接口（核心修改） =====================
@router.post("/zd-double", summary="【产品二】ZD双筒预测（专属接口）")
async def predict_zd_double(req: PredictRequest):
    try:
        model_map = assemble_model_paths("zd-double", req)
        data_file_path = os.path.abspath(req.file_path)

        loop = get_async_loop()
        call_func = partial(
            zd_run_prediction,
            file_path=data_file_path,
            model_map=model_map
        )
        pred_result = await loop.run_in_executor(None, call_func)

        cleaned_result = clean_inf_nan(pred_result)
        return {"code": 200, "msg": "ZD双筒预测成功", "data": cleaned_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ZD双筒预测失败：{str(e)}")


# ===================== 🔧 接口3：XD 预测接口（核心修改） =====================
@router.post("/xd", summary="【产品三】XD预测（专属接口）")
async def predict_xd(req: PredictRequest):
    try:
        model_map = assemble_model_paths("xd", req)
        data_file_path = os.path.abspath(req.file_path)

        loop = get_async_loop()
        call_func = partial(
            xd_run_prediction,
            file_path=data_file_path,
            model_map=model_map
        )
        pred_result = await loop.run_in_executor(None, call_func)

        cleaned_result = clean_inf_nan(pred_result)
        return {"code": 200, "msg": "XD预测成功", "data": cleaned_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"XD预测失败：{str(e)}")