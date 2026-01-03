# 通用接口
import json
import uuid
from pathlib import Path

import aiofiles
import pandas as pd
from fastapi import APIRouter, UploadFile, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from core.deps import get_session
from core.verify_files import verify_file, verify_data
from entites.data_model import EnterDataReq
from entites.db_model import EnterData

router = APIRouter(prefix="/api/common", tags=['common'])

STORE_PATH = "store_files"

if not Path(STORE_PATH).exists():
    Path(STORE_PATH).mkdir()

# 所需要的字段与数据表对应关系
need_fileds_dict = {
    "DW": "dw",
    "XHFK": "xhfk",
    "XHFS": "xhfs",
    "HZ": "hz",
    "XHYD": "xhyd",
    "YJGN": "yjgn",
    "GNFZ": "gnfz",
    "JYYL": "jyyl",
    "MF-内漏量": "mf_nll",
    "XC": "xc",
    "SCL-伸出力/压载均值": "scl_scl",
    "SCL-收回力/拉载均值": "scl_shl",
    "ZL": "zl",
    "SM-总寿命(FH)": "sm_zsm_fh",
    "SM-总寿命(起落)": "sm_zsm_ql",
    "SM-总寿命(拦阻)": "sm_zsm_lz"

}


@router.post("/upload", status_code=status.HTTP_200_OK)
async def upload(file: UploadFile = Depends(verify_file), session: AsyncSession = Depends(get_session)):
    """
    上传数据
    :param file:
    :return:
    """
    suffix = Path(file.filename).suffix
    file_id = uuid.uuid4()
    store_file_path = f"{STORE_PATH}/{file_id}{suffix}"

    # 保存本地文件
    async with aiofiles.open(store_file_path, "wb") as f:
        await f.write(await file.read())

    # 读取文件并保存到数据库中
    df = pd.read_excel(store_file_path)

    # 解析每一条数据并批量新增
    datas = []
    for idx, item in df.iterrows():
        data = item.to_dict()
        data_need = {need_fileds_dict[k]: data[k] for k in data.keys() if k in need_fileds_dict.keys()}
        each_data_obj = EnterData(**data_need)
        datas.append(each_data_obj)

    session.add_all(datas)
    await session.commit()

    return datas


@router.post("/enter_data", status_code=status.HTTP_200_OK)
async def enter_data(input_data: EnterDataReq = Depends(verify_data),
                     session: AsyncSession = Depends(get_session)):
    """
    输入数据
    :param session:
    :param input_data:
    :return:
    """
    # 存入数据表中
    input_dict = input_data.model_dump(by_alias=True)

    need_data = {need_fileds_dict[k]: input_dict[k] for k in input_dict.keys() if k in need_fileds_dict.keys()}

    input_data_obj = EnterData(**need_data)

    session.add(input_data_obj)
    await session.commit()
    await session.refresh(input_data_obj)

    return input_data_obj
