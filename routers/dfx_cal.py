# dfx_cal.py
import os
import uuid
import json
from pathlib import Path
from typing import Tuple, List, Optional

import aiofiles
from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from core.verify_files import verify_data_dfx
from entites.data_model import EnterDataReq_DFX

from core.config import DFX_CAL_PATH
from core.path_store import path_store

# 定义路由（和common.py保持一致的前缀/标签风格）
router = APIRouter(prefix="/dfx", tags=['DFX计算模块'])

# ========== 1. 定义DFX分值-系数区间映射规则（与表格严格对齐） ==========
# 格式：[(分值区间下限, 分值区间上限, 系数下限, 系数上限), ...]
# 注意：
# - 区间左闭右开 [a,b)，特殊值 ≤0.4 单独处理
# - 分值区间和系数区间严格对应表格
DFX_INTERVAL_RULES: Tuple[Tuple[float, float, float, float, bool], ...] = (
    (0.9, 1.0, 0.80, 0.85, True),   # 闭区间 [0.9, 1.0]
    (0.8, 0.9, 0.85, 0.90, False),  # 左闭右开 [0.8, 0.9)
    (0.7, 0.8, 0.90, 0.95, False),
    (0.6, 0.7, 0.95, 1.00, False),
    (0.5, 0.6, 1.00, 1.10, False),
    (0.4, 0.5, 1.10, 1.20, False),
    (0.0, 0.4, 1.20, 1.20, False),  # 特殊区间：系数固定1.20
)

# ========== 2. 区间匹配 + 系数计算核心函数 ==========
def get_dfx_coefficient(dfx_score: float) -> float:
    """
    根据DFX分值计算对应系数：
    1. 匹配分值所在区间 → 获取系数上下限
    2. 按公式计算：系数 = [(d-c)/(a-b)] × (score - a) + d
    3. 处理边界值和特殊区间（≤0.4）
    """
    # 1. 校验分值范围（合理范围0-1）
    if not (0.0 <= dfx_score <= 1.0):
        raise ValueError(f"DFX分值必须在0-1之间（当前值：{dfx_score}）")

    # 2. 匹配对应的系数区间（消除硬编码，通过规则的「是否闭区间」字段判断）
    matched_rule: Optional[Tuple[float, float, float, float, bool]] = None
    for rule in DFX_INTERVAL_RULES:
        a, b, c, d, is_closed = rule
        # 判断是否命中区间：区分闭区间/左闭右开
        if is_closed:
            if a <= dfx_score <= b:
                matched_rule = rule
                break
        else:
            if a <= dfx_score < b:
                matched_rule = rule
                break

    if not matched_rule:
        raise ValueError(f"未找到DFX分值{dfx_score}对应的系数区间")

    # 3. 解析匹配到的规则
    a, b, c, d, is_closed = matched_rule  # a=分值下限, b=分值上限, c=系数下限, d=系数上限

    # 4. 特殊处理：分值≤0.4时，系数固定1.20（也可通过规则直接识别，更通用）
    if a == 0.0 and b == 0.4:
        return 1.20

    # 5. 按公式计算系数：[(d-c)/(a-b)] × (score - a) + d
    denominator = a - b
    if denominator == 0:
        raise ValueError(f"分值区间[{a},{b}]的分母为0，无法计算（区间长度不能为0）")

    coefficient = ((d - c) / denominator) * (dfx_score - a) + d
    # 保留4位小数（避免浮点精度问题）
    return round(coefficient, 4)


# ========== 3. DFX加权平均计算函数（整合系数计算） ==========
def calculate_dfx_weighted_average(input_dict: dict) -> dict:
    """
    DFX核心计算逻辑：
    1. 加权平均 = Σ(符合率数值 × 对应权重) → 转换为0-1区间的分值（若输入是百分比则/100）
    2. 根据加权平均分值计算DFX系数（按区间公式）
    """
    # 1. 提取所有数值和权重对（按字段名规则匹配：xxx_数值 / xxx_权重）
    numeric_keys = [k for k in input_dict.keys() if k.endswith("_输入数值")]
    weight_keys = [k.replace("_输入数值", "_指标权重") for k in numeric_keys]

    # 2. 计算加权和（若输入是百分比，需转换为0-1区间，这里假设输入是0-100的百分比）
    weighted_sum = 0.0
    calculate_details = {}
    for num_key, weight_key in zip(numeric_keys, weight_keys):
        num_val = input_dict.get(num_key, 0.0)
        weight_val = input_dict.get(weight_key, 0.0)

        # 转换为小数（0-1）参与计算 页面输入的百分比（如80 → 80%）
        num_val_normalized = num_val / 100
        product = num_val_normalized * weight_val
        weighted_sum += product

        # 记录计算明细
        calculate_details[num_key] = {
            "原始输入值(%)": num_val,
            "归一化后值(0-1)": num_val_normalized,
            "权重": weight_val,
            "乘积": product
        }

    # 3. 计算DFX系数（加权和即为DFX分值）
    dfx_score = weighted_sum
    dfx_coefficient = get_dfx_coefficient(dfx_score)

    # 返回计算结果（包含明细、分值、系数）
    return {
        "DFX加权平均分值(0-1)": round(dfx_score, 6),
        "DFX系数": dfx_coefficient,
        "计算明细": calculate_details
    }


# ========== 4. DFX计算接口（和原有风格一致） ==========
@router.post("/calculate", status_code=status.HTTP_200_OK, summary="【DFX计算】提交数据并执行加权平均计算")
async def dfx_calculate(input_data: EnterDataReq_DFX = Depends(verify_data_dfx)):
    """
    DFX计算接口【最终版】
    ✅ 接收页面输入数据 → 计算加权平均分值 → 按区间公式计算DFX系数
    ✅ 保存计算结果到JSON文件（和ZD/XD保持一致的存储逻辑）
    """
    # 1. Pydantic模型转字典（解析别名、排除None）
    input_dict = input_data.model_dump(by_alias=True, exclude_none=False)

    # 2. 执行核心计算
    try:
        cal_result = calculate_dfx_weighted_average(input_dict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"DFX计算失败：{str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DFX计算异常：{str(e)}")

    # 3. 保存计算结果到JSON文件（和ZD/XD一样，便于追溯）
    dfx_store_path = DFX_CAL_PATH
    os.makedirs(dfx_store_path, exist_ok=True)
    json_file_id = uuid.uuid4()
    json_store_path = Path(os.path.join(dfx_store_path, f"dfx_cal_{json_file_id}.json")).absolute()

    # 组装保存的数据（输入+计算结果）
    save_data = {
        "输入参数": input_dict,
        "计算结果": cal_result
    }
    async with aiofiles.open(json_store_path, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(save_data, ensure_ascii=False, indent=4))

    path_store.write_path("dfx_cal_path",json_store_path)

    # 4. 返回结果（包含计算结果+文件路径，和common.py格式统一）
    return {
        "code": 200,
        "msg": "DFX计算完成",
        "data": {
            "计算结果": cal_result,
            "结果文件路径": os.path.abspath(json_store_path)
        }
    }