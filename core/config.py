# core/config.py
from typing import Literal


# 模板位置
Template_PATH = "Template"

# 临时目录：训练自动保存，可能堆积
TEMP_OUTPUT_PATH = "output/temp"
# 永久目录：仅用户点击保存后才复制过来
PERM_OUTPUT_PATH = "output/perm"

# 临时目录：预测自动保存，可能堆积
TEMP_PREDICT_PATH = "predict_results/temp"
# 永久目录：仅用户点击保存后才复制过来
PERM_PREDICT_PATH = "predict_results/perm"
# dfx修改后的目录：仅用户点击保存后才复制过来
FIXED_PREDICT_PATH = "predict_results/fixed"

DFX_CAL_PATH = "dfx_cal_result"



# ========== 全局公共常量 (所有模块统一从这里导入) ==========
# 模型类型枚举（和你的三个下拉框一一对应，固定值）
ModelType = Literal["直接材料成本预测模型", "直接人工和制造费用成本预测模型", "总成本预测模型"]

# 模型类型映射（前端展示名 → 后端文件过滤关键字，和命名规范对应）
MODEL_TYPE_MAP = {
    "直接材料成本预测模型": "material",
    "直接人工和制造费用成本预测模型": "manlab",
    "总成本预测模型": "total"
}

# 数据读取优先级：手动录入(json) > 批量上传(excel)
PATH_KEY_MAP = {
    "ZD单筒": {"enter": "enter_data_zddt_path", "upload": "upload_zddt_path"},
    "ZD双筒": {"enter": "enter_data_zdst_path", "upload": "upload_zdst_path"},
    "XD": {"enter": "enter_data_xd_path", "upload": "upload_xd_path"}
}


# 对比文件根路径
ORI_DB_PATH = "DB"

# 产品类型 -> 子目录映射 (check_ori_db_path专用)
PRODUCT_DIR_MAP = {
    "单筒": "zddt",
    "ZD单筒": "zddt",
    "双筒": "zdst",
    "ZD双筒": "zdst",
    "xd": "xd",
    "XD": "xd"
}