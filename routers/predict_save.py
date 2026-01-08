import os
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any
from pathlib import Path

# ===================== 全局配置 =====================
router = APIRouter(prefix="/model/predict/save", tags=["预测结果保存"])

# 预测结果保存根目录（自动创建，支持绝对路径/相对路径）
SAVE_ROOT_DIR = Path("predict_results").absolute()
# 按产品分类子目录 + 对应产品名称（用于生成文件名）
PRODUCT_CONFIG = {
    "zd-single": {"dir": SAVE_ROOT_DIR / "zd" / "single", "name": "zd单筒"},
    "zd-double": {"dir": SAVE_ROOT_DIR / "zd" / "double", "name": "zd双筒"},
    "xd": {"dir": SAVE_ROOT_DIR / "xd", "name": "xd"}
}

# 自动创建所有目录（递归创建，避免路径不存在）
for config in PRODUCT_CONFIG.values():
    config["dir"].mkdir(parents=True, exist_ok=True)


# ===================== 请求体模型（移除save_filename） =====================
class SavePredictResultRequest(BaseModel):
    """保存预测结果请求体：仅需传入预测结果，文件名自动生成"""
    predict_result: Dict[str, Any] = Field(..., description="预测接口返回的完整结果（原封不动传入）")


# ===================== 通用工具函数（优化文件名生成） =====================
def _save_predict_json(result: Dict[str, Any], save_dir: Path, product_name: str) -> dict:
    """
    通用JSON保存函数
    :param result: 预测结果字典
    :param save_dir: 保存目录（Path对象）
    :param product_name: 产品名称（如zd单筒/zd双筒/xd）
    :return: 保存结果字典（文件名、绝对路径、相对路径）
    """
    # 1. 生成文件名：产品名称 + 时间戳（格式：YYYYMMDDHHMM，如zd双筒_202501081728.json）
    timestamp = datetime.now().strftime("%Y%m%d%H%M")  # 精确到分钟，避免高频保存重复（如需毫秒可加%f[:-3]）
    filename = f"{product_name}_{timestamp}.json"

    # 2. 拼接完整路径
    save_path = save_dir / filename

    # 3. 写入JSON（保留中文、格式化缩进）
    try:
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(
                result,
                f,
                ensure_ascii=False,  # 保留中文（如产品名称）
                indent=2,  # 格式化缩进，方便阅读
                sort_keys=False  # 不排序key，保留原始顺序
            )
    except Exception as e:
        raise RuntimeError(f"写入JSON文件失败：{str(e)}")

    # 4. 返回标准化结果
    return {
        "save_filename": filename,
        "save_abs_path": str(save_path.absolute()),
        "save_relative_path": str(save_path.relative_to(Path.cwd())),  # 相对当前工作目录
        "note": "预测结果未做任何修改，完全保留原始格式"
    }


# ===================== 业务接口：ZD单筒 =====================
@router.post("/zd-single", summary="【ZD】单筒预测结果保存为JSON")
async def save_zd_single_predict_result(req: SavePredictResultRequest):
    try:
        # 1. 校验结果非空
        if not req.predict_result:
            raise HTTPException(status_code=400, detail="预测结果为空，无法保存")

        # 2. 调用通用保存函数
        save_info = _save_predict_json(
            result=req.predict_result,
            save_dir=PRODUCT_CONFIG["zd-single"]["dir"],
            product_name=PRODUCT_CONFIG["zd-single"]["name"]
        )

        # 3. 返回结果
        return {
            "code": 200,
            "msg": "ZD单筒预测结果已成功保存为JSON",
            "data": save_info
        }
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败：{str(e)}")


# ===================== 业务接口：ZD双筒 =====================
@router.post("/zd-double", summary="【ZD】双筒预测结果保存为JSON")
async def save_zd_double_predict_result(req: SavePredictResultRequest):
    try:
        if not req.predict_result:
            raise HTTPException(status_code=400, detail="预测结果为空，无法保存")

        save_info = _save_predict_json(
            result=req.predict_result,
            save_dir=PRODUCT_CONFIG["zd-double"]["dir"],
            product_name=PRODUCT_CONFIG["zd-double"]["name"]
        )

        return {
            "code": 200,
            "msg": "ZD双筒预测结果已成功保存为JSON",
            "data": save_info
        }
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败：{str(e)}")


# ===================== 业务接口：XD =====================
@router.post("/xd", summary="【XD】预测结果保存为JSON")
async def save_xd_predict_result(req: SavePredictResultRequest):
    try:
        if not req.predict_result:
            raise HTTPException(status_code=400, detail="预测结果为空，无法保存")

        save_info = _save_predict_json(
            result=req.predict_result,
            save_dir=PRODUCT_CONFIG["xd"]["dir"],
            product_name=PRODUCT_CONFIG["xd"]["name"]
        )

        return {
            "code": 200,
            "msg": "XD预测结果已成功保存为JSON",
            "data": save_info
        }
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败：{str(e)}")