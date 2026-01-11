import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Body
from core.config import FIXED_PREDICT_PATH
# from core.config import DFX_CAL_PATH
from core.path_store import path_store



# 修正结果保存目录
CORRECTION_SAVE_DIR = Path(FIXED_PREDICT_PATH)
CORRECTION_SAVE_DIR.mkdir(parents=True, exist_ok=True)


# 定义路由
router = APIRouter(prefix="/cost_correct", tags=["成本修正（DFX系数）"])





# ===================== 核心工具函数 =====================
def extract_dfx_coefficient(dfx_result: Dict[str, Any]) -> float:
    """
    从DFX完整返回结果中自动提取DFX系数
    :param dfx_result: DFX计算接口返回的完整结果（如你提供的JSON）
    :return: 提取到的DFX系数（如0.9985）
    :raise ValueError: 字段缺失/格式错误时抛出明确异常
    """
    try:
        # 按层级提取：data → 计算结果 → DFX系数
        dfx_coeff = dfx_result["计算结果"]["DFX系数"]
        # 校验系数有效性
        if not isinstance(dfx_coeff, (int, float)) or dfx_coeff <= 0:
            raise ValueError(f"DFX系数无效（必须为正数）：{dfx_coeff}")
        return dfx_coeff
    except KeyError as e:
        raise ValueError(f"DFX结果格式错误，缺失关键字段：{str(e)} → 请检查是否包含 计算结果.DFX系数")
    except Exception as e:
        raise ValueError(f"提取DFX系数失败：{str(e)}")


def correct_cost_by_dfx(
        predict_result: dict,  # ZD/XD的预测结果（完整返回体，顶级字典）
        dfx_coefficient: float  # 提取后的DFX系数
) -> dict:
    """
    核心函数：用DFX系数修正ZD/XD的成本预测结果
    :param predict_result: ZD单筒/双筒/XD的完整预测返回体（顶级字典，含predict_details）
    :param dfx_coefficient: 提取到的DFX系数
    :return: 包含原始结果+修正后结果的完整数据，不破坏原有结构
    """
    # ============ 修复：正确的字段校验逻辑 ============
    # 校验1：顶级字典必须包含 predict_details 字段
    if "predict_details" not in predict_result:
        raise ValueError("预测结果格式错误：顶级字典中缺少 predict_details 字段")
    # 校验2：predict_details 必须是列表类型
    predict_details = predict_result.get("predict_details", [])
    if not isinstance(predict_details, list):
        raise ValueError("预测结果格式错误：predict_details 必须是列表类型")

    # 遍历每个预测明细，计算修正后结果
    corrected_details = []
    for detail in predict_details:
        # 跳过状态非成功/无预测结果的项，保留原始数据+标记修正失败
        if detail.get("status") != "success" or "predict_result" not in detail:
            corrected_details.append({
                **detail,
                "corrected_predict_result": None,  # 标记修正失败
                "dfx_coefficient": dfx_coefficient
            })
            continue

        # 提取原始成本值，并做健壮性校验
        raw_result = detail["predict_result"]
        cost_keys = ["material", "manufacture_labour", "total_cost"]
        # 校验是否包含全部必要的成本字段
        if not all(key in raw_result for key in cost_keys):
            corrected_details.append({
                **detail,
                "corrected_predict_result": None,  # 字段缺失，标记修正失败
                "dfx_coefficient": dfx_coefficient,
                "correction_error": "predict_result缺少必要的成本字段(material/manufacture_labour/total_cost)"
            })
            continue

        # 计算修正后值（保留6位小数，与原始结果精度一致）
        corrected_result = {
            "material": round(raw_result["material"] * dfx_coefficient, 6),
            "manufacture_labour": round(raw_result["manufacture_labour"] * dfx_coefficient, 6),
            "total_cost": round(raw_result["total_cost"] * dfx_coefficient, 6)
        }

        # 拼接原始结果+修正结果（不破坏原有数据结构）
        corrected_detail = {
            **detail,
            "corrected_predict_result": corrected_result,  # 新增：修正后的成本结果
            "dfx_coefficient": dfx_coefficient             # 新增：记录本次使用的DFX系数
        }
        corrected_details.append(corrected_detail)

    # ============ 修复：正确的结果组装逻辑（无data嵌套层） ============
    final_result = {
        **predict_result,  # 保留原始所有字段
        "predict_details": corrected_details,  # 替换为修正后的明细列表
        "dfx_correction_note": f"所有成本值已乘以DFX系数修正：{dfx_coefficient}"  # 新增备注
    }
    return final_result


# ===================== 接口1：自动提取DFX系数（推荐） =====================

@router.post("/zddt-auto-dfx", summary="【推荐】自动提取DFX系数并修正ZDDT成本")
async def zddt_correct_cost_auto_dfx():
    """
    核心优势：无需手动输入DFX系数，自动从DFX结果中提取，减少人工错误
    """
    try:
        # ========== 修复第1行 ==========
        dfx_path = path_store.read_path("dfx_cal_path")
        with open(dfx_path, "r", encoding="utf-8") as f:
            dfx_result = json.load(f)

        # 1. 自动提取DFX系数
        dfx_coeff = extract_dfx_coefficient(dfx_result)

        # ========== 修复第2行 ==========
        predict_path = path_store.read_path("zddt_perm_predict_path")
        with open(predict_path, "r", encoding="utf-8") as f:
            predict_result = json.load(f)

        # 2. 执行成本修正
        corrected_result = correct_cost_by_dfx(predict_result, dfx_coeff)
        # 3. 保存修正结果到文件
        file_name = f"zddt_cost_correction_{uuid.uuid4()}.json"
        save_path = CORRECTION_SAVE_DIR / file_name
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(corrected_result, f, ensure_ascii=False, indent=2)
        # 4. 返回结果
        path_store.write_path("zddt_cost_correction_path", save_path.absolute())

        return {
            "code": 200,
            "msg": f"ZD单筒成本修正完成,已自动保存至{save_path.absolute()}",
            "data": {
                "extracted_dfx_coefficient": dfx_coeff,  # 展示提取到的系数
                "corrected_result": corrected_result,
                "save_path": str(save_path.absolute()),
                "dfx_correction_note": f"使用DFX系数 {dfx_coeff} 修正所有成本值"
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"参数错误：{str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"修正失败：{str(e)}")


@router.post("/zdst-auto-dfx", summary="【推荐】自动提取DFX系数并修正ZDST成本")
async def zdst_correct_cost_auto_dfx():
    """
    核心优势：无需手动输入DFX系数，自动从DFX结果中提取，减少人工错误
    """
    try:
        # ========== 修复第1行 ==========
        dfx_path = path_store.read_path("dfx_cal_path")
        with open(dfx_path, "r", encoding="utf-8") as f:
            dfx_result = json.load(f)

        # 1. 自动提取DFX系数
        dfx_coeff = extract_dfx_coefficient(dfx_result)

        predict_path = path_store.read_path("zdst_perm_predict_path")
        with open(predict_path, "r", encoding="utf-8") as f:
            predict_result = json.load(f)


        # 2. 执行成本修正
        corrected_result = correct_cost_by_dfx(predict_result, dfx_coeff)
        # 3. 保存修正结果到文件
        file_name = f"zdst_cost_correction_{uuid.uuid4()}.json"
        save_path = CORRECTION_SAVE_DIR / file_name
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(corrected_result, f, ensure_ascii=False, indent=2)
        # 4. 返回结果
        path_store.write_path("zdst_cost_correction_path", save_path.absolute())

        return {
            "code": 200,
            "msg": f"ZD双筒成本修正完成,已自动保存至{save_path.absolute()}",
            "data": {
                "extracted_dfx_coefficient": dfx_coeff,  # 展示提取到的系数
                "corrected_result": corrected_result,
                "save_path": str(save_path.absolute()),
                "dfx_correction_note": f"使用DFX系数 {dfx_coeff} 修正所有成本值"
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"参数错误：{str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"修正失败：{str(e)}")



@router.post("/xd-auto-dfx", summary="【推荐】自动提取DFX系数并修正XD成本")
async def xd_correct_cost_auto_dfx():
    """
    核心优势：无需手动输入DFX系数，自动从DFX结果中提取，减少人工错误
    """
    try:
        # ========== 修复第1行 ==========
        dfx_path = path_store.read_path("dfx_cal_path")
        with open(dfx_path, "r", encoding="utf-8") as f:
            dfx_result = json.load(f)

        # 1. 自动提取DFX系数
        dfx_coeff = extract_dfx_coefficient(dfx_result)

        # ========== 修复第2行 ==========
        predict_path = path_store.read_path("xd_perm_predict_path")
        with open(predict_path, "r", encoding="utf-8") as f:
            predict_result = json.load(f)


        # 2. 执行成本修正
        corrected_result = correct_cost_by_dfx(predict_result, dfx_coeff)
        # 3. 保存修正结果到文件
        file_name = f"cost_correction_auto_{uuid.uuid4()}.json"
        save_path = CORRECTION_SAVE_DIR / file_name
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(corrected_result, f, ensure_ascii=False, indent=2)
        # 4. 返回结果
        path_store.write_path("xd_cost_correction_path", save_path.absolute())

        return {
            "code": 200,
            "msg": f"XD成本修正完成,已自动保存至{save_path.absolute()}",
            "data": {
                "extracted_dfx_coefficient": dfx_coeff,  # 展示提取到的系数
                "corrected_result": corrected_result,
                "save_path": str(save_path.absolute()),
                "dfx_correction_note": f"使用DFX系数 {dfx_coeff} 修正所有成本值"
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"参数错误：{str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"修正失败：{str(e)}")