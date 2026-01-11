from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import os

from core.path_store import path_store
from core.config import MODEL_TYPE_MAP, PERM_OUTPUT_PATH, PATH_KEY_MAP, ORI_DB_PATH, PRODUCT_DIR_MAP,TEMP_PREDICT_PATH
from routers.predict_save import _save_predict_json
import re
import os
from pathlib import Path


import json
import math


os.makedirs(TEMP_PREDICT_PATH,exist_ok=True)
TEMP_PREDICT_PATH = Path(TEMP_PREDICT_PATH).absolute()


router = APIRouter(prefix="/predict", tags=["产品预测"])


# # 导入上面的XD预测函数
from Job01.XD产品预测模型code.XD_code.XD_predict import batch_run_xd_prediction
from Job01.ZD产品预测模型code.ZD_code.ZD_predict import batch_run_zd_prediction
#
# 全局JSON序列化钩子：处理inf/nan
class SafeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, float):
            if math.isinf(obj) or math.isnan(obj):
                return 0.0
        return super().default(obj)




# ========== 按优先级读取数据路径：手动录入 > 批量上传 ==========
def get_priority_data_path(product_type: str) -> str:
    path_keys = PATH_KEY_MAP[product_type]
    try:
        enter_path = path_store.read_path(path_keys["enter"])
        return enter_path
    except (KeyError, FileNotFoundError):
        upload_path = path_store.read_path(path_keys["upload"])
        return upload_path


# ========== 修复后的校验对比文件路径函数 (完美匹配你的调用传参) ==========
def check_ori_db_path(ori_db_root_path: str, product_type: str) -> str:
    """极简版：按产品类型匹配子目录，读取第一个Excel文件，兼容【ZD单筒/单筒/ZD双筒/双筒/xd/XD】"""
    # 直接用抽离的常量映射，不用在函数内重新定义，统一维护
    if product_type not in PRODUCT_DIR_MAP:
        raise ValueError(f"不支持的产品类型：{product_type}")
    # 拼接子目录
    target_dir = os.path.join(ori_db_root_path, PRODUCT_DIR_MAP[product_type])
    # 筛选目录下所有Excel文件
    excel_files = [
        os.path.join(target_dir, f) for f in os.listdir(target_dir)
        if os.path.isfile(os.path.join(target_dir, f))
        and Path(f).suffix.lower() in [".xlsx", ".xls"]
    ]
    if not excel_files:
        raise FileNotFoundError(f"{target_dir} 目录下无Excel文件")
    return excel_files[0]

# ===================== 【产品一】ZD单筒 专属预测接口分组 (全部无参) =====================
@router.post("/zddt/select/material", summary="【ZD单筒-下拉框1】直接材料成本预测模型 (无参)")
async def zddt_select_material():
    """ZD单筒专属：下拉框1，仅加载 zddt_material_ 开头的所有模型"""
    try:
        product_key = "zddt"
        model_key = MODEL_TYPE_MAP["直接材料成本预测模型"]
        model_dir = Path(PERM_OUTPUT_PATH)
        print(model_dir)
        if not model_dir.exists():
            raise FileNotFoundError(f"模型目录不存在：{model_dir}")
        model_files = []
        pattern = re.compile(f"^{product_key}_{model_key}_.*\.(pkl|json)$", re.I)
        for file in model_dir.iterdir():
            if file.is_file() and pattern.match(file.name):
                model_files.append({"model_name": file.name, "model_abs_path": str(file.absolute())})
        return {"code": 200, "msg": "ZD单筒-直接材料模型加载成功", "data": model_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ZD单筒-直接材料模型加载失败：{str(e)}")

@router.post("/zddt/select/labour", summary="【ZD单筒-下拉框2】直接人工和制造费用成本预测模型 (无参)")
async def zddt_select_labour():
    """ZD单筒专属：下拉框2，仅加载 zddt_manlab_ 开头的所有模型"""
    try:
        product_key = "zddt"
        model_key = MODEL_TYPE_MAP["直接人工和制造费用成本预测模型"]
        model_dir = Path(PERM_OUTPUT_PATH)
        if not model_dir.exists():
            raise FileNotFoundError(f"模型目录不存在：{model_dir}")
        model_files = []
        pattern = re.compile(f"^{product_key}_{model_key}_.*\.(pkl|json)$", re.I)
        for file in model_dir.iterdir():
            if file.is_file() and pattern.match(file.name):
                model_files.append({"model_name": file.name, "model_abs_path": str(file.absolute())})
        return {"code": 200, "msg": "ZD单筒-直接人工模型加载成功", "data": model_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ZD单筒-直接人工模型加载失败：{str(e)}")

@router.post("/zddt/select/total", summary="【ZD单筒-下拉框3】总成本预测模型 (无参)")
async def zddt_select_total():
    """ZD单筒专属：下拉框3，仅加载 zddt_total_ 开头的所有模型"""
    try:
        product_key = "zddt"
        model_key = MODEL_TYPE_MAP["总成本预测模型"]
        model_dir = Path(PERM_OUTPUT_PATH)
        if not model_dir.exists():
            raise FileNotFoundError(f"模型目录不存在：{model_dir}")
        model_files = []
        pattern = re.compile(f"^{product_key}_{model_key}_.*\.(pkl|json)$", re.I)
        for file in model_dir.iterdir():
            if file.is_file() and pattern.match(file.name):
                model_files.append({"model_name": file.name, "model_abs_path": str(file.absolute())})
        return {"code": 200, "msg": "ZD单筒-总成本模型加载成功", "data": model_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ZD单筒-总成本模型加载失败：{str(e)}")

# ZD单筒预测请求体（仅传3个模型路径，无其他参数）
class ZDDTPredictRequest(BaseModel):
    material_model_path: str = Field(..., description="下拉框1选中的直接材料模型路径")
    labour_model_path: str = Field(..., description="下拉框2选中的直接人工模型路径")
    total_model_path: str = Field(..., description="下拉框3选中的总成本模型路径")

@router.post("/zddt/run", summary="【产品一核心】ZD单筒 专属预测接口 (仅传3个模型路径)")
async def zddt_predict(request: ZDDTPredictRequest):
    try:
        # 1. ZD单筒专属：按优先级读取数据路径
        data_path = get_priority_data_path("ZD单筒")
        # 2. 校验写死的对比路径 ✅修复：传ZD单筒能正确匹配zddt目录
        ori_db_path = check_ori_db_path(ORI_DB_PATH, "ZD单筒")
        # 4. 调用预测函数
        from Job01.ZD产品预测模型code.ZD_code.ZD_predict import batch_run_zd_prediction
        model_map = {
            "material": request.material_model_path,
            "manufacture_labour": request.labour_model_path,
            "total_cost": request.total_model_path
        }
        print(model_map)
        predict_result = batch_run_zd_prediction(
            file_path=data_path,
            model_map=model_map,
            ori_db_path=ori_db_path,
            type = "单筒"
        )
        # 5. 手动序列化结果，确保无非法值
        safe_result = json.loads(json.dumps(predict_result, cls=SafeJSONEncoder))

        temp_predict_path = _save_predict_json(
            result=safe_result,
            save_dir=TEMP_PREDICT_PATH,
            product_name="zddt_pred"
        )
        path_store.write_path("zddt_temp_predict_path", temp_predict_path)




        # 6. 返回结果 ✅修复：异常文案从双筒改为单筒
        return {
            "code": 200,
            "msg": "ZD单筒预测完成",
            "data": safe_result,
            "temp_predict_path":temp_predict_path
        }
    except (KeyError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=f"ZD单筒预测前置异常：{str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ZD单筒预测失败：{str(e)}")





# ===================== 【产品二】ZD双筒 专属预测接口分组 (全部无参) =====================
@router.post("/zdst/select/material", summary="【ZD双筒-下拉框1】直接材料成本预测模型 (无参)")
async def zdst_select_material():
    """ZD单筒专属：下拉框1，仅加载 zdst_material_ 开头的所有模型"""
    try:
        product_key = "zdst"
        model_key = MODEL_TYPE_MAP["直接材料成本预测模型"]
        model_dir = Path(PERM_OUTPUT_PATH)
        print(model_dir)
        if not model_dir.exists():
            raise FileNotFoundError(f"模型目录不存在：{model_dir}")
        model_files = []
        pattern = re.compile(f"^{product_key}_{model_key}_.*\.(pkl|json)$", re.I)
        for file in model_dir.iterdir():
            if file.is_file() and pattern.match(file.name):
                model_files.append({"model_name": file.name, "model_abs_path": str(file.absolute())})
        return {"code": 200, "msg": "ZD双筒-直接材料模型加载成功", "data": model_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ZD双筒-直接材料模型加载失败：{str(e)}")

@router.post("/zdst/select/labour", summary="【ZD双筒-下拉框2】直接人工和制造费用成本预测模型 (无参)")
async def zdst_select_labour():
    """ZD双筒专属：下拉框2，仅加载 zdst_manlab_ 开头的所有模型"""
    try:
        product_key = "zdst"
        model_key = MODEL_TYPE_MAP["直接人工和制造费用成本预测模型"]
        model_dir = Path(PERM_OUTPUT_PATH)
        if not model_dir.exists():
            raise FileNotFoundError(f"模型目录不存在：{model_dir}")
        model_files = []
        pattern = re.compile(f"^{product_key}_{model_key}_.*\.(pkl|json)$", re.I)
        for file in model_dir.iterdir():
            if file.is_file() and pattern.match(file.name):
                model_files.append({"model_name": file.name, "model_abs_path": str(file.absolute())})
        return {"code": 200, "msg": "ZD双筒-直接人工模型加载成功", "data": model_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ZD双筒-直接人工模型加载失败：{str(e)}")

@router.post("/zdst/select/total", summary="【ZD双筒-下拉框3】总成本预测模型 (无参)")
async def zdst_select_total():
    """ZD双筒专属：下拉框3，仅加载 zdst_total 开头的所有模型"""
    try:
        product_key = "zdst"
        model_key = MODEL_TYPE_MAP["总成本预测模型"]
        model_dir = Path(PERM_OUTPUT_PATH)
        if not model_dir.exists():
            raise FileNotFoundError(f"模型目录不存在：{model_dir}")
        model_files = []
        pattern = re.compile(f"^{product_key}_{model_key}_.*\.(pkl|json)$", re.I)
        for file in model_dir.iterdir():
            if file.is_file() and pattern.match(file.name):
                model_files.append({"model_name": file.name, "model_abs_path": str(file.absolute())})
        return {"code": 200, "msg": "ZD双筒-总成本模型加载成功", "data": model_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ZD双筒-总成本模型加载失败：{str(e)}")

# ZD单筒预测请求体（仅传3个模型路径，无其他参数）
class ZDSTPredictRequest(BaseModel):
    material_model_path: str = Field(..., description="下拉框1选中的直接材料模型路径")
    labour_model_path: str = Field(..., description="下拉框2选中的直接人工模型路径")
    total_model_path: str = Field(..., description="下拉框3选中的总成本模型路径")

@router.post("/zdst/run", summary="【产品一核心】ZD双筒 专属预测接口 (仅传3个模型路径)")
async def zdst_predict(request: ZDSTPredictRequest):
    try:
        # 1. ZD单筒专属：按优先级读取数据路径
        data_path = get_priority_data_path("ZD双筒")
        # 2. 校验写死的对比路径 ✅修复：传ZD单筒能正确匹配zddt目录
        ori_db_path = check_ori_db_path(ORI_DB_PATH, "ZD双筒")
        # 4. 调用预测函数
        from Job01.ZD产品预测模型code.ZD_code.ZD_predict import batch_run_zd_prediction
        model_map = {
            "material": request.material_model_path,
            "manufacture_labour": request.labour_model_path,
            "total_cost": request.total_model_path
        }
        print(model_map)
        predict_result = batch_run_zd_prediction(
            file_path=data_path,
            model_map=model_map,
            ori_db_path=ori_db_path,
            type = "双筒"
        )
        # 5. 手动序列化结果，确保无非法值
        safe_result = json.loads(json.dumps(predict_result, cls=SafeJSONEncoder))

        # 保存到临时目录
        temp_predict_path = _save_predict_json(
            result=safe_result,
            save_dir=TEMP_PREDICT_PATH,
            product_name="zdst"
        )
        path_store.write_path("zdst_pred_temp_predict_path", temp_predict_path)



        # 6. 返回结果 ✅修复：异常文案从双筒改为单筒
        return {
            "code": 200,
            "msg": "ZD双筒预测完成",
            "data": safe_result
        }
    except (KeyError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=f"ZD双筒预测前置异常：{str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ZD双筒预测失败：{str(e)}")



# ===================== 【产品三】XD 专属预测接口分组 (全部无参) =====================
@router.post("/xd/select/material", summary="【XD-下拉框1】直接材料成本预测模型 (无参)")
async def xd_select_material():
    """XD专属：下拉框1，仅加载 xd_material_开头的所有模型"""
    try:
        product_key = "xd"
        model_key = MODEL_TYPE_MAP["直接材料成本预测模型"]
        model_dir = Path(PERM_OUTPUT_PATH)
        print(model_dir)
        if not model_dir.exists():
            raise FileNotFoundError(f"模型目录不存在：{model_dir}")
        model_files = []
        pattern = re.compile(f"^{product_key}_{model_key}_.*\.(pkl|json)$", re.I)
        for file in model_dir.iterdir():
            if file.is_file() and pattern.match(file.name):
                model_files.append({"model_name": file.name, "model_abs_path": str(file.absolute())})
        return {"code": 200, "msg": "XD-直接材料模型加载成功", "data": model_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"XD-直接材料模型加载失败：{str(e)}")

@router.post("/xd/select/labour", summary="【XD-下拉框2】直接人工和制造费用成本预测模型 (无参)")
async def xd_select_labour():
    """ZD双筒专属：下拉框2，仅加载 xd_manlab_ 开头的所有模型"""
    try:
        product_key = "xd"
        model_key = MODEL_TYPE_MAP["直接人工和制造费用成本预测模型"]
        model_dir = Path(PERM_OUTPUT_PATH)
        if not model_dir.exists():
            raise FileNotFoundError(f"模型目录不存在：{model_dir}")
        model_files = []
        pattern = re.compile(f"^{product_key}_{model_key}_.*\.(pkl|json)$", re.I)
        for file in model_dir.iterdir():
            if file.is_file() and pattern.match(file.name):
                model_files.append({"model_name": file.name, "model_abs_path": str(file.absolute())})
        return {"code": 200, "msg": "ZD双筒-直接人工模型加载成功", "data": model_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"XD-直接人工模型加载失败：{str(e)}")

@router.post("/xd/select/total", summary="【XD-下拉框3】总成本预测模型 (无参)")
async def xd_select_total():
    """XD专属：下拉框3，仅加载 xd_total_ 开头的所有模型"""
    try:
        product_key = "xd"
        model_key = MODEL_TYPE_MAP["总成本预测模型"]
        model_dir = Path(PERM_OUTPUT_PATH)
        if not model_dir.exists():
            raise FileNotFoundError(f"模型目录不存在：{model_dir}")
        model_files = []
        pattern = re.compile(f"^{product_key}_{model_key}_.*\.(pkl|json)$", re.I)
        for file in model_dir.iterdir():
            if file.is_file() and pattern.match(file.name):
                model_files.append({"model_name": file.name, "model_abs_path": str(file.absolute())})
        return {"code": 200, "msg": "XD-总成本模型加载成功", "data": model_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"XD-总成本模型加载失败：{str(e)}")

# XD预测请求体（仅传3个模型路径，无其他参数）
class XDPredictRequest(BaseModel):
    material_model_path: str = Field(..., description="下拉框1选中的直接材料模型路径")
    labour_model_path: str = Field(..., description="下拉框2选中的直接人工模型路径")
    total_model_path: str = Field(..., description="下拉框3选中的总成本模型路径")

@router.post("/xd/run", summary="【产品一核心】XD专属预测接口 (仅传3个模型路径)")
async def xd_predict(request: XDPredictRequest):
    try:
        # 1. XD专属：按优先级读取数据路径
        data_path = get_priority_data_path("XD")
        # 2. 校验写死的对比路径 ✅修复：传XD能正确匹配XD目录
        ori_db_path = check_ori_db_path(ORI_DB_PATH, "XD")
        # 4. 调用预测函数
        from Job01.XD产品预测模型code.XD_code.XD_predict import batch_run_xd_prediction
        model_map = {
            "material": request.material_model_path,
            "manufacture_labour": request.labour_model_path,
            "total_cost": request.total_model_path
        }
        print(model_map)
        predict_result = batch_run_xd_prediction(
            file_path=data_path,
            model_map=model_map,
            ori_db_path=ori_db_path
        )
        # 5. 手动序列化结果，确保无非法值
        safe_result = json.loads(json.dumps(predict_result, cls=SafeJSONEncoder))

        # 保存到临时目录
        temp_predict_path = _save_predict_json(
            result=safe_result,
            save_dir=TEMP_PREDICT_PATH,
            product_name="xd_pred"
        )
        path_store.write_path("xd_temp_predict_path", temp_predict_path)



        # 6. 返回结果
        return {
            "code": 200,
            "msg": "XD预测完成",
            "data": safe_result
        }
    except (KeyError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=f"XD预测前置异常：{str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"XD预测失败：{str(e)}")