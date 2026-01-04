# data_model.py
from pydantic import BaseModel, Field, field_validator
from typing import Literal

# ========== 【核心】定义所有下拉框的可选值（与前端下拉选项完全一致） ==========
# 有无下拉：通用选项
YES_NO_OPTIONS = Literal["有", "无"]
# XHFK下拉可选值（对应拆解后2个字段）
XHFK_OPTIONS = Literal["到位反馈", "位置反馈", "无"]
# XHFS下拉可选值（对应拆解后5个字段）
XHFS_OPTIONS = Literal["LVDT", "主机二配件", "电压", "接近开关", "行程开关", "无"]
# GNFZ下拉可选值（对应拆解后3个字段）
GNFZ_OPTIONS = Literal["单向节流阀", "节流阀", "梭阀", "无"]

class EnterDataReq_ZD(BaseModel):
    """
    页面手动录入请求模型（与前端表单1:1对应）
    ✅ 下拉框字段：严格约束可选值，与前端下拉选项一致
    ✅ 数值字段：保持原始类型，接收页面输入值
    """
    DW: YES_NO_OPTIONS
    XHFK: XHFK_OPTIONS
    XHFS: XHFS_OPTIONS
    HZ: YES_NO_OPTIONS
    XHYD: float
    YJGN: YES_NO_OPTIONS
    GNFZ: GNFZ_OPTIONS
    JYYL: float
    MF_内漏量: float = Field(alias="MF-内漏量")
    XC: float
    SCL_伸出力_压载均值: float = Field(alias="SCL-伸出力/压载均值")
    SCL_收回力_拉载均值: float = Field(alias="SCL-收回力/拉载均值")
    ZL: float
    SM_总寿命_FH: float = Field(alias="SM-总寿命(FH)")
    SM_总寿命_起落: float = Field(alias="SM-总寿命(起落)")
    SM_总寿命_拦阻: float = Field(alias="SM-总寿命(拦阻)")

    # 可选校验：数值字段非负校验（防止前端传负数，按需开启）
    @field_validator('XHYD', 'JYYL', 'MF_内漏量', 'XC', 'ZL', 'SM_总寿命_FH')
    def validate_positive_num(cls, v):
        if v < 0:
            raise ValueError("数值字段不可为负数，请检查后重新输入")
        return v