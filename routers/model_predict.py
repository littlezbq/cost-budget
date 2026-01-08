from fastapi import APIRouter, HTTPException, Body
import json
import math
# 导入上面的XD预测函数
from Job01.XD产品预测模型code.XD_code.XD_predict import batch_run_xd_prediction
from Job01.ZD产品预测模型code.ZD_code.ZD_predict import batch_run_zd_prediction

# 全局JSON序列化钩子：处理inf/nan
class SafeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, float):
            if math.isinf(obj) or math.isnan(obj):
                return 0.0
        return super().default(obj)


router = APIRouter(prefix="/predict", tags=["产品预测"])



@router.post("/zd-single", summary="ZD单筒预测（支持JSON/Excel上传）")
async def zd_single_predict_api(
        # 修复1：example → examples，且值为列表格式
        file: str = Body(...,
                         examples=[r"E:\Work\cost\cost-budget\store_files\04b77b3b-f588-4ad3-8025-488864ac1d2a.xlsx"]),
        model_map: dict = Body(..., examples=[{
            "material": "zddt_material_202601071437.json",
            "manufacture_labour": "zddt_manlab_202601071439.json",
            "total_cost": "zddt_total_202601071413.json"
        }]),
        ori_db_path: str = Body(..., examples=[r"E:\Work\cost\cost-budget\Job01\inputdata\ZD数据表.xlsx"])
):
    """
    ZD单筒预测接口：
    1. 上传JSON/Excel文件
    2. 自动预测成本
    3. 对比数据库Excel找Top5相似产品
    4. 生成SHAP分析文件
    """
    try:
        # 1. 调用批量预测函数
        predict_result = batch_run_zd_prediction(
            file_path=file,
            model_map=model_map,
            ori_db_path=ori_db_path,
            type = "单筒"
        )

        # 2. 手动序列化结果，确保无非法值（关键修复）
        safe_result = json.loads(json.dumps(predict_result, cls=SafeJSONEncoder))

        # 3. 返回结果
        return {
            "code": 200,
            "msg": "ZD单筒预测完成",
            "data": safe_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ZD单筒预测失败：{str(e)}")


@router.post("/zd-double", summary="ZD单筒预测（支持JSON/Excel上传）")
async def zd_double_predict_api(
        # 修复1：example → examples，且值为列表格式
        file: str = Body(...,
                         examples=[r"E:\Work\cost\cost-budget\store_files\04b77b3b-f588-4ad3-8025-488864ac1d2a.xlsx"]),
        model_map: dict = Body(..., examples=[{
            "material": "zdst_material_202511021711.json",
            "manufacture_labour": "zdst_manlab_202511021709.json",
            "total_cost": "zdst_total_202511021707.json"
        }]),
        ori_db_path: str = Body(..., examples=[r"E:\Work\cost\cost-budget\Job01\inputdata\ZD数据表.xlsx"])
):
    """
    ZD双筒预测接口：
    1. 上传JSON/Excel文件
    2. 自动预测成本
    3. 对比数据库Excel找Top5相似产品
    4. 生成SHAP分析文件
    """
    try:
        # 1. 调用预测函数
        predict_result = batch_run_zd_prediction(
            file_path=file,
            model_map=model_map,
            ori_db_path=ori_db_path,
            type="双筒"
        )

        # 2. 手动序列化结果，确保无非法值（关键修复）
        safe_result = json.loads(json.dumps(predict_result, cls=SafeJSONEncoder))

        # 3. 返回结果
        return {
            "code": 200,
            "msg": "ZD双筒预测完成",
            "data": safe_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ZD双筒预测失败：{str(e)}")


@router.post("/xd", summary="XD批量预测（支持JSON/Excel上传）")
async def xd_predict_api(
        # 修复1：example → examples，且值为列表格式
        file: str = Body(...,
                         examples=[r"E:\Work\cost\cost-budget\store_files\a859e926-7555-4ec9-bed6-f490e5e72cd7.xlsx"]),
        model_map: dict = Body(..., examples=[{
            "material": "xd_material_202511301628.json",
            "manufacture_labour": "xd_manlab_202511301629.json",
            "total_cost": "xd_total_202511301626.json"
        }]),
        ori_db_path: str = Body(..., examples=[r"E:\Work\cost\cost-budget\Job01\inputdata\XD数据表.xlsx"])
):
    """
    XD批量预测接口：
    1. 上传JSON/Excel文件
    2. 自动预测成本
    3. 对比数据库Excel找Top5相似产品
    4. 生成SHAP分析文件
    """
    try:
        # 1. 调用批量预测函数
        predict_result = batch_run_xd_prediction(
            file_path=file,
            model_map=model_map,
            ori_db_path=ori_db_path
        )

        # 2. 手动序列化结果，确保无非法值（关键修复）
        safe_result = json.loads(json.dumps(predict_result, cls=SafeJSONEncoder))

        # 3. 返回结果
        return {
            "code": 200,
            "msg": "XD批量预测完成",
            "data": safe_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"XD预测失败：{str(e)}")