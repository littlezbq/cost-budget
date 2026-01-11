import os
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any
from pathlib import Path
from core.path_store import path_store
import shutil
from core.config import TEMP_PREDICT_PATH,PERM_PREDICT_PATH,FIXED_PREDICT_PATH


def save_result_permanent(temp_path,perm_dir):
    """
    将临时目录的模型/结果文件复制到永久目录
    :param temp_model_path: 临时模型文件路径（训练返回的temp_model_path）
    :param temp_excel_path: 临时Excel结果路径
    :return: 永久目录的文件路径
    """
    # 1. 校验临时文件是否存在
    if not os.path.exists(temp_path):
        raise ValueError(f"临时文件不存在 → {temp_path}")


    # 2. 构建永久目录路径（按筒型/目标变量分类，便于管理）
    # 从临时文件名中解析筒型/目标变量（比如zd_dt_total_202601071234.json → dt/total）
    model_filename = os.path.basename(temp_path)
    perm_dir = Path(perm_dir).absolute()
    os.makedirs(perm_dir, exist_ok=True)

    # 3. 复制文件到永久目录（保留原文件名）
    perm_path = os.path.join(perm_dir, model_filename)
    # 复制模型文件
    shutil.copy2(temp_path, perm_path)
    print(f"✅ 结果已永久保存：{os.path.abspath(perm_path)}")
    return os.path.abspath(perm_path)





# ===================== 全局配置 =====================
router = APIRouter(prefix="/model/predict/save", tags=["预测结果保存"])


# ===================== 请求体模型（移除save_filename） =====================
# class SavePredictResultRequest(BaseModel):
#     """保存预测结果请求体：仅需传入预测结果，文件名自动生成"""
#     predict_result: Dict[str, Any] = Field(..., description="预测接口返回的完整结果（原封不动传入）")


# ===================== 通用工具函数（优化文件名生成） =====================
def _save_predict_json(result: Dict[str, Any], save_dir: Path, product_name: str):
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
    return save_path.absolute()


@router.post("/zddt_save_predict_perm", summary="ZD单筒预测结果永久保存【无参】→自动读取预测或修正后的预测结果，无需传参")
async def api_save_zddt_predict_perm_auto():
    try:
        # 核心逻辑：优先级读取 → 先读修正结果路径 → 读不到则读临时预测路径
        save_model_path = None

        # 第一步：尝试读取修正后结果路径 (优先级高)
        try:
            save_model_path = path_store.read_path("zddt_cost_correction_path")
        except KeyError:
            # 无修正结果路径，不报错，继续尝试读临时路径
            pass

        # 第二步：如果没读到修正路径，尝试读取临时预测路径
        if not save_model_path:
            try:
                save_model_path = path_store.read_path("zddt_temp_predict_path")
            except KeyError as e:
                # 临时路径也读不到，抛出明确异常，提示必须先执行预测
                raise HTTPException(status_code=400, detail=f"❌ 请先执行ZD单筒模型预测！未生成任何预测结果文件，{str(e)}")

        # 关键校验：路径不能为空/None
        if not save_model_path or len(str(save_model_path).strip()) == 0:
            raise ValueError("读取到的预测结果路径为空，无法执行永久保存")

        # 执行永久保存逻辑
        save_result = save_result_permanent(save_model_path, PERM_PREDICT_PATH)

        # 根据读取的路径类型，写入对应的永久路径key，保证路径存储的一致性
        if "zddt_cost_correction_path" in locals():
            path_store.write_path("zddt_fixed_predict_path", save_result)
        else:
            path_store.write_path("zddt_perm_predict_path", save_result)

        return {"code": 200, "msg": "预测结果永久保存成功", "path": save_result}

    except ValueError as e:
        # 路径为空的业务异常
        raise HTTPException(status_code=400, detail=f"❌ 永久保存失败：{str(e)}")
    except OSError as e:
        # 文件操作异常（权限不足/路径不存在/文件被占用）
        raise HTTPException(status_code=500, detail=f"❌ 文件操作失败，保存预测结果失败：{str(e)}")
    except Exception as e:
        # 兜底所有未捕获的异常
        raise HTTPException(status_code=500, detail=f"❌ ZD预测结果永久保存异常：{str(e)}")



# ===================== 业务接口：ZD双筒 =====================
@router.post("/zdst_save_predict_perm", summary="ZD双筒预测结果永久保存【无参】→自动读取预测或修正后的预测结果，无需传参")
async def api_save_zdst_predict_perm_auto():
    try:
        # 核心逻辑：优先级读取 → 先读修正结果路径 → 读不到则读临时预测路径
        save_model_path = None

        # 第一步：尝试读取修正后结果路径 (优先级高)
        try:
            save_model_path = path_store.read_path("zdst_cost_correction_path")
        except KeyError:
            # 无修正结果路径，不报错，继续尝试读临时路径
            pass

        # 第二步：如果没读到修正路径，尝试读取临时预测路径
        if not save_model_path:
            try:
                save_model_path = path_store.read_path("zdst_temp_predict_path")
            except KeyError as e:
                # 临时路径也读不到，抛出明确异常，提示必须先执行预测
                raise HTTPException(status_code=400, detail=f"❌ 请先执行ZD双筒模型预测！未生成任何预测结果文件，{str(e)}")

        # 关键校验：路径不能为空/None
        if not save_model_path or len(str(save_model_path).strip()) == 0:
            raise ValueError("读取到的预测结果路径为空，无法执行永久保存")

        # 执行永久保存逻辑
        save_result = save_result_permanent(save_model_path, PERM_PREDICT_PATH)

        # 根据读取的路径类型，写入对应的永久路径key，保证路径存储的一致性
        if "zddt_cost_correction_path" in locals():
            path_store.write_path("zdst_fixed_predict_path", save_result)
        else:
            path_store.write_path("zdst_perm_predict_path", save_result)

        return {"code": 200, "msg": "预测结果永久保存成功", "path": save_result}

    except ValueError as e:
        # 路径为空的业务异常
        raise HTTPException(status_code=400, detail=f"❌ 永久保存失败：{str(e)}")
    except OSError as e:
        # 文件操作异常（权限不足/路径不存在/文件被占用）
        raise HTTPException(status_code=500, detail=f"❌ 文件操作失败，保存预测结果失败：{str(e)}")
    except Exception as e:
        # 兜底所有未捕获的异常
        raise HTTPException(status_code=500, detail=f"❌ ZD双筒预测结果永久保存异常：{str(e)}")

@router.post("/xd_save_predict_perm", summary="xd预测结果永久保存【无参】→自动读取预测或修正后的预测结果，无需传参")
async def api_save_xd_predict_perm_auto():
    try:
        # 核心逻辑：优先级读取 → 先读修正结果路径 → 读不到则读临时预测路径
        save_model_path = None

        # 第一步：尝试读取修正后结果路径 (优先级高)
        try:
            save_model_path = path_store.read_path("xd_cost_correction_path")
        except KeyError:
            # 无修正结果路径，不报错，继续尝试读临时路径
            pass

        # 第二步：如果没读到修正路径，尝试读取临时预测路径
        if not save_model_path:
            try:
                save_model_path = path_store.read_path("xd_temp_predict_path")
            except KeyError as e:
                # 临时路径也读不到，抛出明确异常，提示必须先执行预测
                raise HTTPException(status_code=400, detail=f"❌ 请先执行ZD单筒模型预测！未生成任何预测结果文件，{str(e)}")

        # 关键校验：路径不能为空/None
        if not save_model_path or len(str(save_model_path).strip()) == 0:
            raise ValueError("读取到的预测结果路径为空，无法执行永久保存")

        # 执行永久保存逻辑
        save_result = save_result_permanent(save_model_path, PERM_PREDICT_PATH)

        # 根据读取的路径类型，写入对应的永久路径key，保证路径存储的一致性
        if "xd_cost_correction_path" in locals():
            path_store.write_path("xd_fixed_predict_path", save_result)
        else:
            path_store.write_path("xd_perm_predict_path", save_result)

        return {"code": 200, "msg": "预测结果永久保存成功", "path": save_result}

    except ValueError as e:
        # 路径为空的业务异常
        raise HTTPException(status_code=400, detail=f"❌ 永久保存失败：{str(e)}")
    except OSError as e:
        # 文件操作异常（权限不足/路径不存在/文件被占用）
        raise HTTPException(status_code=500, detail=f"❌ 文件操作失败，保存预测结果失败：{str(e)}")
    except Exception as e:
        # 兜底所有未捕获的异常
        raise HTTPException(status_code=500, detail=f"❌ XD预测结果永久保存异常：{str(e)}")
