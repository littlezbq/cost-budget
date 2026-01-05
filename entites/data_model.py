# data_model.py
from pydantic import BaseModel, Field
from typing import Literal


# 定义ZD的页面数据模板，需要考虑下拉的一对多的情况，最终返回的是和训练数据一致的一对一的键值对。
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



# 定义XD的页面数据模板，XD的模板相对简单，只有部分参数是有无的下拉框，无一对多的情况。


class EnterDataReq_XD(BaseModel):
    """
    页面手动录入请求模型（与前端表单1:1对应）
    ✅ 数值字段：保持原始类型，接收页面输入值
    """
    JL: YES_NO_OPTIONS
    CD: YES_NO_OPTIONS
    WZSF: YES_NO_OPTIONS
    WZKG: YES_NO_OPTIONS
    LJBH: YES_NO_OPTIONS
    XCXW: YES_NO_OPTIONS
    JS: float
    ZJ:float
    CBD:float
    JX:float
    DCJR:float
    短时高温:YES_NO_OPTIONS
    耐火要求: YES_NO_OPTIONS
    炮振要求: YES_NO_OPTIONS
    工作包线内表面温度要求: YES_NO_OPTIONS
    除冰温度要求: YES_NO_OPTIONS
    防火和可燃性: YES_NO_OPTIONS
    DQY: YES_NO_OPTIONS
    WG: YES_NO_OPTIONS
    SR_温度下: float=Field(alias="SR-温度下")
    SR_时间:float=Field(alias="SR-时间")
    YW_时间:float=Field(alias="YW-时间")
    YW_溶液pH值下界:float = Field(alias="YW-溶液pH值下界")
    YW_溶液pH值上界:float = Field(alias="YW-溶液pH值上界")
    PJZD:YES_NO_OPTIONS
    ZS:YES_NO_OPTIONS

