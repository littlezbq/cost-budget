from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from pathlib import Path
from core.config import Template_PATH

router = APIRouter(tags=["文件操作-模板下载"])

# 核心配置 - 你的模板根路径（完全沿用你的配置，一行没改）
EXCEL_TEMPLATE_DIR = Path(Template_PATH).absolute()

# -------------------------- 接口1：下载【XD】专用Excel模板 --------------------------
@router.get("/download_xd_template", summary="下载XD专用上传模板【无参】",
            description="下载XD业务对应的Excel上传模板，仅适用于XD数据上传")
async def api_download_xd_template():
    try:
        template_name = "XD上传模板.xlsx"  # 你的XD模板文件名，可自定义修改
        template_path = os.path.join(EXCEL_TEMPLATE_DIR, template_name)
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"XD模板文件不存在，路径：{template_path}")
        if not os.path.isfile(template_path):
            raise ValueError(f"XD模板路径不是有效文件：{template_path}")

        return FileResponse(
            path=template_path,
            filename=template_name,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"❌ XD模板下载失败：{str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ XD模板下载异常：{str(e)}")

# -------------------------- 接口2：下载【ZD单筒】专用Excel模板 --------------------------
@router.get("/download_zd_single_template", summary="下载ZD单筒专用上传模板【无参】",
            description="下载ZD单筒业务对应的Excel上传模板，仅适用于ZD单筒数据上传")
async def api_download_zd_single_template():
    try:
        template_name = "ZD单筒上传模板.xlsx"  # 你的ZD单筒模板文件名，可自定义修改
        template_path = os.path.join(EXCEL_TEMPLATE_DIR, template_name)
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"ZD单筒模板文件不存在，路径：{template_path}")
        if not os.path.isfile(template_path):
            raise ValueError(f"ZD单筒模板路径不是有效文件：{template_path}")

        return FileResponse(
            path=template_path,
            filename=template_name,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"❌ ZD单筒模板下载失败：{str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ ZD单筒模板下载异常：{str(e)}")

# -------------------------- 接口3：下载【ZD双筒】专用Excel模板 --------------------------
@router.get("/download_zd_double_template", summary="下载ZD双筒专用上传模板【无参】",
            description="下载ZD双筒业务对应的Excel上传模板，仅适用于ZD双筒数据上传")
async def api_download_zd_double_template():
    try:
        template_name = "ZD双筒上传模板.xlsx"  # 你的ZD双筒模板文件名，可自定义修改
        template_path = os.path.join(EXCEL_TEMPLATE_DIR, template_name)
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"ZD双筒模板文件不存在，路径：{template_path}")
        if not os.path.isfile(template_path):
            raise ValueError(f"ZD双筒模板路径不是有效文件：{template_path}")

        return FileResponse(
            path=template_path,
            filename=template_name,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"❌ ZD双筒模板下载失败：{str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ ZD双筒模板下载异常：{str(e)}")