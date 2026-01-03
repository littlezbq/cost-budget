# pydantic数据类
from pydantic import BaseModel, Field


class EnterDataReq(BaseModel):
    DW: float
    XHFK: str
    XHFS: str
    HZ: float
    XHYD: float
    YJGN: float
    GNFZ: str
    JYYL: float
    MF_内漏量: float = Field(alias="MF-内漏量")
    XC: float
    SCL_伸出力_压载均值: float = Field(alias="SCL-伸出力/压载均值")
    SCL_收回力_拉载均值: float = Field(alias="SCL-收回力/拉载均值")
    ZL: float
    SM_总寿命_FH: float = Field(alias="SM-总寿命(FH)")
    SM_总寿命_起落: float = Field(alias="SM-总寿命(起落)")
    SM_总寿命_拦阻: float = Field(alias="SM-总寿命(拦阻)")
