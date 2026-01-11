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


# data_model.py 末尾新增
class EnterDataReq_DFX(BaseModel):
    """
    DFX计算页面手动录入请求模型（与前端表单1:1对应）
    ✅ 数值字段：输入的符合率（0-100 或 0-1，根据页面设计）
    ✅ 权重字段：带默认值，总和保证为1（100%）
    """
    # DFM（Design For Manufacture）可制造性设计
    工艺性符合率含装配_输入数值: float = Field(..., description="工艺性符合率（含装配）输入值")
    工艺性符合率含装配_指标权重: float = Field(default=0.111672, description="工艺性符合率权重")

    加工要求符合率_输入数值: float = Field(..., description="加工要求符合率输入值")
    加工要求符合率_指标权重: float = Field(default=0.074448, description="加工要求符合率指标权重")


    试验设备优选率_输入数值: float = Field(..., description="试验设备优选率输入值")
    试验设备优选率_指标权重: float = Field(default=0.040326, description="试验设备优选率指标权重")


    装配返工率_输入数值: float = Field(..., description="装配返工率输入值")
    装配返工率_指标权重: float = Field(default=0.055836, description="装配返工率指标权重")


    新增专用工装夹具_输入数值: float = Field(..., description="新增专用工装夹具输入值")
    新增专用工装夹具_指标权重: float = Field(default=0.027918, description="新增专用工装夹具指标权重")


    # DFP （Design For Procurement） 可采购性
    二配件成本占比_输入数值: float = Field(..., description="二配件成本占比输入值")
    二配件成本占比_指标权重: float = Field(default=0.055706, description="二配件成本占比指标权重")

    成件优选率_输入数值: float = Field(..., description="成件优选率输入值")
    成件优选率_指标权重: float = Field(default=0.042385, description="成件优选率指标权重")

    单一来源占比_不含协议和特殊规定_输入数值: float = Field(..., description="单一来源占比（不含协议和特殊规定）输入值")
    单一来源占比_不含协议和特殊规定_指标权重: float = Field(default=0.023009, description="试验设备优选率指标权重")


    # DFR （Design For Reusability） 可重用性设计
    自制件CBB复用率_输入数值: float = Field(..., description="自制件CBB复用率输入值")
    自制件CBB复用率_指标权重: float = Field(default=0.239085, description="自制件CBB复用率指标权重")

    标准化率_输入数值: float = Field(..., description="标准化率输入值")
    标准化率_指标权重: float = Field(default=0.13041, description="标准化率指标权重")

    材料优选率_输入数值: float = Field(..., description="材料优选率输入值")
    材料优选率_指标权重: float = Field(default=0.065205, description="材料优选率指标权重")

    # DFS （Design For Service） 可维修性
    有寿件成本占比_输入数值: float = Field(..., description="有寿件成本占比输入值")
    有寿件成本占比_指标权重: float = Field(default=0.04556, description="有寿件成本占比指标权重")

    二配有寿件成本占比_输入数值: float = Field(..., description="二配有寿件成本占比输入值")
    二配有寿件成本占比_指标权重: float = Field(default=0.03886, description="二配有寿件成本占比指标权重")

    非必换报废件成本占比_输入数值: float = Field(..., description="非必换报废件成本占比输入值")
    非必换报废件成本占比_指标权重: float = Field(default=0.01876, description="非必换报废件成本占比指标权重")

    维修返工_修_占比_输入数值: float = Field(..., description="维修返工（修）占比输入值")
    维修返工_修_占比_指标权重: float = Field(default=0.03082, description="维修返工（修）占比指标权重")



