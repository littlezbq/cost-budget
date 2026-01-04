import uuid
import os
import json
from pathlib import Path

import aiofiles
import pandas as pd
from fastapi import APIRouter, UploadFile, Depends, HTTPException
from starlette import status

from core.verify_files import verify_file, verify_data
from entites.data_model import EnterDataReq_ZD

router = APIRouter(prefix="/api/common", tags=['common'])

# 特征列名称（upload列名校验 + enter_data入参校验 共用）
column_names_zd = ['DW', 'XHFK-到位反馈', 'XHFK-位置反馈', 'XHFS-LVDT', 'XHFS-主机二配件', 'XHFS-电压', 'XHFS-接近开关',
                'XHFS-行程开关', 'HZ', 'XHYD', 'YJGN', 'GNFZ-单向节流阀', 'GNFZ-节流阀', 'GNFZ-梭阀', 'JYYL',
                'MF-内漏量', 'XC', 'SCL-伸出力/压载均值', 'SCL-收回力/拉载均值', 'ZL', 'SM-总寿命(FH)',
                'SM-总寿命(起落)', 'SM-总寿命(拦阻)']

# 文件存储根目录（Excel和JSON统一存放，便于管理）
STORE_PATH = "store_files"
# 确保目录存在
os.makedirs(STORE_PATH, exist_ok=True)


@router.post("/upload_zd", status_code=status.HTTP_200_OK)
async def upload_zd(file: UploadFile = Depends(verify_file)):
    """
    Excel批量上传接口【最终版】
    ✅ 3项校验：Excel格式 + 存在「单筒」sheet + 特征列匹配column_names
    ✅ 仅保存文件，无入库，返回Excel绝对路径
    """
    # 校验1：是否为Excel格式
    file_suffix = Path(file.filename).suffix.lower()
    if file_suffix not in ['.xlsx', '.xls']:
        raise HTTPException(status_code=400, detail="文件格式错误，仅支持.xlsx/.xls格式Excel文件")

    # 保存Excel文件
    file_id = uuid.uuid4()
    store_file_path = os.path.join(STORE_PATH, f"{file_id}{file_suffix}")
    async with aiofiles.open(store_file_path, "wb") as f:
        await f.write(await file.read())

    # 校验2：是否存在「单筒」sheet
    try:
        excel_sheet_names = pd.ExcelFile(store_file_path).sheet_names
        if "单筒" not in excel_sheet_names:
            raise HTTPException(status_code=400, detail="Excel文件中未找到【单筒】sheet，请核对sheet名称！")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取Excel Sheet失败：{str(e)}")

    # 校验3：特征列一致性校验
    data = pd.read_excel(store_file_path, sheet_name="单筒")
    excel_cols = list(data.columns)
    missing_cols = [col for col in column_names_zd if col not in excel_cols]
    if missing_cols:
        raise HTTPException(
            status_code=400,
            detail=f"【单筒】sheet缺失必填特征列：{','.join(missing_cols)}，请严格对照特征列配置！"
        )

    # 返回Excel绝对路径
    excel_abs_path = os.path.abspath(store_file_path)
    return {
        "code": 200,
        "msg": "Excel文件校验通过，保存成功",
        "data": excel_abs_path
    }


# ========== 【核心】定义训练特征列完整列表（与训练JSON的key完全一致） ==========
TRAIN_COLUMNS_ZD = [
    'DW', 'XHFK-到位反馈', 'XHFK-位置反馈', 'XHFS-LVDT', 'XHFS-主机二配件',
    'XHFS-电压', 'XHFS-接近开关', 'XHFS-行程开关', 'HZ', 'XHYD', 'YJGN',
    'GNFZ-单向节流阀', 'GNFZ-节流阀', 'GNFZ-梭阀', 'JYYL', 'MF-内漏量', 'XC',
    'SCL-伸出力/压载均值', 'SCL-收回力/拉载均值', 'ZL', 'SM-总寿命(FH)',
    'SM-总寿命(起落)', 'SM-总寿命(拦阻)'
]


# ========== 有无下拉 转换规则==========
def yes_no2num(val: str) -> int:
    """通用转换：下拉「有」→1，「无」→0"""
    return 1 if val == "有" else 0

# ========== 【核心】下拉框值 → 训练字段映射关系表 ==========
# XHFK下拉值 → 对应训练字段的映射
XHFK_MAP = {
    "到位反馈": {"XHFK-到位反馈": 1, "XHFK-位置反馈": 0},
    "位置反馈": {"XHFK-到位反馈": 0, "XHFK-位置反馈": 1},
    "无": {"XHFK-到位反馈": 0, "XHFK-位置反馈": 0}
}

# XHFS下拉值 → 对应训练字段的映射
XHFS_MAP = {
    "LVDT": {"XHFS-LVDT": 1, "XHFS-主机二配件": 0, "XHFS-电压": 0, "XHFS-接近开关": 0, "XHFS-行程开关": 0},
    "主机二配件": {"XHFS-LVDT": 0, "XHFS-主机二配件": 1, "XHFS-电压": 0, "XHFS-接近开关": 0, "XHFS-行程开关": 0},
    "电压": {"XHFS-LVDT": 0, "XHFS-主机二配件": 0, "XHFS-电压": 1, "XHFS-接近开关": 0, "XHFS-行程开关": 0},
    "接近开关": {"XHFS-LVDT": 0, "XHFS-主机二配件": 0, "XHFS-电压": 0, "XHFS-接近开关": 1, "XHFS-行程开关": 0},
    "行程开关": {"XHFS-LVDT": 0, "XHFS-主机二配件": 0, "XHFS-电压": 0, "XHFS-接近开关": 0, "XHFS-行程开关": 1},
    "无": {"XHFS-LVDT": 0, "XHFS-主机二配件": 0, "XHFS-电压": 0, "XHFS-接近开关": 0, "XHFS-行程开关": 0}
}

# GNFZ下拉值 → 对应训练字段的映射
GNFZ_MAP = {
    "单向节流阀": {"GNFZ-单向节流阀": 1, "GNFZ-节流阀": 0, "GNFZ-梭阀": 0},
    "节流阀": {"GNFZ-单向节流阀": 0, "GNFZ-节流阀": 1, "GNFZ-梭阀": 0},
    "梭阀": {"GNFZ-单向节流阀": 0, "GNFZ-节流阀": 0, "GNFZ-梭阀": 1},
    "无": {"GNFZ-单向节流阀": 0, "GNFZ-节流阀": 0, "GNFZ-梭阀": 0}
}


def convert_to_train_format_zd(input_dict: dict) -> dict:
    # 1. 初始化训练字典：所有字段默认0，保证完整性
    train_data = {col: 0 for col in TRAIN_COLUMNS_ZD}

    # 2. ✅ 转换「有无」下拉字段：DW/HZ/YJGN → 1/0
    train_data['DW'] = yes_no2num(input_dict.get('DW', '无'))
    train_data['HZ'] = yes_no2num(input_dict.get('HZ', '无'))
    train_data['YJGN'] = yes_no2num(input_dict.get('YJGN', '无'))

    # 3. 转换XHFK/XHFS/GNFZ下拉字段（原有逻辑，无改动）
    train_data.update(XHFK_MAP[input_dict.get('XHFK', '无')])
    train_data.update(XHFS_MAP[input_dict.get('XHFS', '无')])
    train_data.update(GNFZ_MAP[input_dict.get('GNFZ', '无')])

    # 4. 赋值纯数值字段（原样透传，无改动）
    train_data['XHYD'] = input_dict.get('XHYD', 0)
    train_data['JYYL'] = input_dict.get('JYYL', 0)
    train_data['MF-内漏量'] = input_dict.get('MF-内漏量', 0)
    train_data['XC'] = input_dict.get('XC', 0)
    train_data['SCL-伸出力/压载均值'] = input_dict.get('SCL-伸出力/压载均值', 0)
    train_data['SCL-收回力/拉载均值'] = input_dict.get('SCL-收回力/拉载均值', 0)
    train_data['ZL'] = input_dict.get('ZL', 0)
    train_data['SM-总寿命(FH)'] = input_dict.get('SM-总寿命(FH)', 0)
    train_data['SM-总寿命(起落)'] = input_dict.get('SM-总寿命(起落)', 0)
    train_data['SM-总寿命(拦阻)'] = input_dict.get('SM-总寿命(拦阻)', 0)

    return train_data


@router.post("/enter_data_zd", status_code=status.HTTP_200_OK)
async def enter_data_zd(input_data: EnterDataReq_ZD = Depends(verify_data)):
    """
    单条手动录入接口【最终版】
    ✅ 接收页面下拉框聚合参数 → 自动转换为训练标准JSON格式
    ✅ 保存JSON文件到本地 → 返回JSON文件绝对路径
    ✅ 生成的JSON与训练用的格式完全一致
    """
    # 1. Pydantic模型转原始字典（自动解析alias别名，匹配训练key）
    input_dict = input_data.model_dump(by_alias=True, exclude_none=False)

    # 2. 核心转换：页面数据 → 训练标准数据
    train_json_data = convert_to_train_format_zd(input_dict)

    # 3. 生成唯一JSON文件名，拼接存储路径
    json_file_id = uuid.uuid4()
    json_store_path = os.path.join(STORE_PATH, f"{json_file_id}.json")

    # 4. 异步保存JSON文件（格式化、支持中文、与训练格式一致）
    async with aiofiles.open(json_store_path, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(train_json_data, ensure_ascii=False, indent=4))

    # 5. 返回JSON文件绝对路径（与upload接口格式统一）
    json_abs_path = os.path.abspath(json_store_path)
    return {
        "code": 200,
        "msg": "手动录入数据已转换并保存为训练标准JSON文件",
        "data": json_abs_path
    }