import xgboost as xgb
from pathlib import Path
import pandas as pd
import json
import os

from Job01.XD产品预测模型code.XD_code.XD_data_input import ModelInput, Input_parameternames

# ===================== 全局配置（可直接修改） =====================
# # 默认模型映射（前端未传参时使用）
# DEFAULT_MODEL_MAP = {
#     'material': 'xd_material_202511301628.json',
#     'manufacture_labour': 'xd_manlab_202511301629.json',
#     'total_cost': 'xd_total_202511301626.json'
# }
# 要求的特征字段列表（校验数据用，与你的data_dict字段完全一致）
# REQUIRED_FIELDS = [
#     'JL', 'CD', 'WZSF', 'WZKG', 'LJBH', 'XCXW', 'JS', 'ZJ', 'CDB', 'JX',
#     'DCJR', '短时高温', '耐火要求', '炮振要求', '工作包线内表面温度要求',
#     '除冰温度要求', '防火和可燃性', 'DQY', 'WG', 'SR-温度下', 'SR-时间',
#     'YW-时间', 'YW-溶液pH值下界', 'YW-溶液pH值上界', 'PJZD', 'ZS'
# ]
# 支持的输入文件格式
SUPPORT_FILE_TYPES = ['.xlsx', '.json']


# ===================== 模型加载类（核心修改：路径适配app同级/output/XD_model） =====================
class ModelLoader:
    def __init__(self,model_map):
        # 1. 模型映射：优先传参，无则用默认
        self.model_map = model_map

        # ✅ 核心：精准定位【app同级】的 output/XD_model 绝对路径（稳定不失效）
        current_file = Path(__file__).resolve()  # 当前脚本绝对路径
        # 向上回溯找到「包含output文件夹」的项目根目录（app所在目录）
        project_root = current_file.parent
        while not (project_root / "output").exists():
            project_root = project_root.parent
            if project_root == project_root.parent:
                raise FileNotFoundError("❌ 未找到项目根目录下的output文件夹！请确认路径结构")

        # ✅ 最终模型存储路径：项目根目录 → output → XD_model
        self.model_root_dir = project_root / "output" / "xd_model"

        # ✅ 拼接3个模型完整路径
        self.path_material = self.model_root_dir / self.model_map["material"]
        self.path_manlab = self.model_root_dir / self.model_map["manufacture_labour"]
        self.path_total = self.model_root_dir / self.model_map["total_cost"]

        # 初始化模型对象
        self.model_material = None
        self.model_manlab = None
        self.model_total = None

    def load_all(self):
        # 校验模型目录+文件是否存在
        if not self.model_root_dir.exists():
            raise FileNotFoundError(f"❌ 模型目录不存在 → {self.model_root_dir}")
        for name, path in [
            ("直接材料模型", self.path_material),
            ("人工费用模型", self.path_manlab),
            ("总成本模型", self.path_total)
        ]:
            if not path.exists():
                raise FileNotFoundError(f"❌ {name}不存在 → {path}")

        # 加载XGBoost模型
        self.model_material = xgb.Booster()
        self.model_material.load_model(str(self.path_material))

        self.model_manlab = xgb.Booster()
        self.model_manlab.load_model(str(self.path_manlab))

        self.model_total = xgb.Booster()
        self.model_total.load_model(str(self.path_total))

        return self


# ===================== 预测类（原有逻辑完全不变） =====================
class Predictor:
    def __init__(self, loader: ModelLoader, X):
        if loader.model_material is None:
            raise ValueError("❌ 模型未加载，请先调用 loader.load_all()")
        self.loader = loader
        self.X = X

    def predict_all(self):
        return {
            "material": float(self.loader.model_material.predict(self.X)[0]),
            "manufacture_labour": float(self.loader.model_manlab.predict(self.X)[0]),
            "total_cost": float(self.loader.model_total.predict(self.X)[0])
        }


# ===================== 核心函数1：单条预测（原有逻辑完全保留，兼容历史调用） =====================
def run_prediction(data_dict: dict, model_map=None):
    """
    单条数据预测（原有函数，完全不变）
    :param data_dict: 单条数据字典（与你要求的格式完全一致）
    :param model_map: 模型映射字典
    :return: 单条预测结果
    """
    # 校验数据字段完整性
    _check_data_fields(data_dict)

    # 数据转模型输入格式
    mi = ModelInput(data_dict)
    X = xgb.DMatrix([mi.to_list()], feature_names=Input_parameternames)

    # 加载模型+预测
    loader = ModelLoader(model_map).load_all()
    predictor = Predictor(loader, X)
    return predictor.predict_all()


# ===================== 核心函数2：文件批量预测（新增！适配Excel/JSON，自动循环调用） =====================
def batch_run_prediction(file_path, model_map=None):
    """
    ✅ 新增：文件批量预测（接口直接调用这个函数）
    支持：JSON单条数据 / Excel多行数据 → 自动转换格式 → 循环调用run_prediction
    :param file_path: 数据文件绝对路径（Excel/JSON）
    :param model_map: 模型映射字典（前端下拉框选中的模型文件名）
    :return: 结构化批量预测结果（含成功/失败统计、每条结果）
    """
    # 1. 校验文件格式+存在性
    file_path = Path(file_path).absolute()
    if not file_path.exists():
        raise FileNotFoundError(f"❌ 数据文件不存在 → {file_path}")

    file_suffix = file_path.suffix.lower()
    if file_suffix not in SUPPORT_FILE_TYPES:
        raise ValueError(f"❌ 仅支持{SUPPORT_FILE_TYPES}格式，当前为{file_suffix}")

    # 2. 读取文件 → 统一转换为【data_dict列表】格式
    data_list = []
    if file_suffix == ".json":
        # JSON文件 → 单条数据，转列表
        with open(file_path, 'r', encoding='utf-8') as f:
            single_data = json.load(f)
        _check_data_fields(single_data)  # 校验字段
        data_list.append(single_data)

    elif file_suffix == ".xlsx":
        # Excel文件 → 多行数据，逐行转dict
        df = pd.read_excel(file_path)
        # 统一列名（去除空格/换行，确保与REQUIRED_FIELDS一致）
        df.columns = [col.strip() for col in df.columns]
        # 校验Excel列名是否匹配要求
        missing_cols = [f for f in Input_parameternames if f not in df.columns]
        if missing_cols:
            raise ValueError(f"❌ Excel列名缺失字段 → {missing_cols}")
        # 逐行转换为data_dict
        data_list = df[Input_parameternames].to_dict(orient='records')

    # 3. 循环调用单条预测 → 批量执行
    total_count = len(data_list)
    success_count = 0
    fail_count = 0
    predict_results = []

    for row_idx, data_dict in enumerate(data_list, start=1):
        try:
            # 调用原有单条预测函数
            single_result = run_prediction(data_dict, model_map)
            predict_results.append({
                "row_idx": row_idx,  # 行号（Excel对应行，JSON固定为1）
                "input_data": data_dict,  # 输入数据
                "predict_result": single_result,  # 预测结果
                "status": "success"  # 状态
            })
            success_count += 1
        except Exception as e:
            predict_results.append({
                "row_idx": row_idx,
                "input_data": data_dict,
                "predict_result": None,
                "status": "failed",
                "error_msg": str(e)  # 失败原因
            })
            fail_count += 1

    # 4. 返回结构化批量结果（前端/接口直接解析）
    return {
        "total_count": total_count,
        "success_count": success_count,
        "fail_count": fail_count,
        "predict_details": predict_results
    }


# ===================== 工具函数：数据字段校验 =====================
def _check_data_fields(data_dict: dict):
    """校验数据字典是否包含所有必填字段"""
    missing_fields = [f for f in Input_parameternames if f not in data_dict]
    if missing_fields:
        raise ValueError(f"❌ 数据缺失必填字段 → {missing_fields}")


