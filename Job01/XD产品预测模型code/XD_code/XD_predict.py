import xgboost as xgb
from pathlib import Path
import pandas as pd
import json
import shap
import math

from Job01.XD产品预测模型code.XD_code.XD_data_input import ModelInput, Input_parameternames
from Job01.XD产品预测模型code.XD_code.XD_compare import SimilarProductFinder

# ===================== 全局配置（仅XD） =====================
SUPPORT_FILE_TYPES = ['.xlsx', '.json']
COST_TYPE_CN_MAP = {
    "material": "直接材料",
    "manufacture_labour": "直接人工+制造费用",
    "total_cost": "总成本"
}


# 工具函数：安全转换浮点数
def safe_float(value, default=0.0):
    """处理inf/nan，返回合法浮点数"""
    try:
        f_val = float(value)
        if math.isinf(f_val) or math.isnan(f_val):
            return default
        return f_val
    except (ValueError, TypeError):
        return default


# ===================== XD专属模型加载类 =====================
class XDModelLoader:
    def __init__(self, model_map):
        self.model_map = model_map
        current_file = Path(__file__).resolve()
        project_root = current_file.parent
        while not (project_root / "output").exists():
            project_root = project_root.parent
            if project_root == project_root.parent:
                raise FileNotFoundError("❌ 未找到项目根目录下的output文件夹！")
        self.model_root_dir = project_root / "output" / "xd_perm" / "xd_model"
        self.path_material = self.model_root_dir / self.model_map["material"]
        self.path_manlab = self.model_root_dir / self.model_map["manufacture_labour"]
        self.path_total = self.model_root_dir / self.model_map["total_cost"]
        self.model_material = None
        self.model_manlab = None
        self.model_total = None

    def load_all(self):
        if not self.model_root_dir.exists():
            raise FileNotFoundError(f"❌ XD模型目录不存在 → {self.model_root_dir}")
        for model_name, path in [
            ("直接材料模型", self.path_material),
            ("人工费用模型", self.path_manlab),
            ("总成本模型", self.path_total)
        ]:
            if not path.exists():
                raise FileNotFoundError(f"❌ {model_name}不存在 → {path}")
        self.model_material = xgb.Booster()
        self.model_material.load_model(str(self.path_material))
        self.model_manlab = xgb.Booster()
        self.model_manlab.load_model(str(self.path_manlab))
        self.model_total = xgb.Booster()
        self.model_total.load_model(str(self.path_total))
        return self


# ===================== XD专属预测类 =====================
class XDPredictor:
    def __init__(self, loader: XDModelLoader, X):
        if loader.model_material is None:
            raise ValueError("❌ XD模型未加载，请先调用 loader.load_all()")
        self.loader = loader
        self.X = X

    def predict_all(self):
        """预测结果增加非法值校验"""
        return {
            "material": safe_float(self.loader.model_material.predict(self.X)[0]),
            "manufacture_labour": safe_float(self.loader.model_manlab.predict(self.X)[0]),
            "total_cost": safe_float(self.loader.model_total.predict(self.X)[0])
        }


# ===================== XD专属SHAP分析函数 =====================
def generate_xd_shap_analysis(data_dict: dict, model_loader: XDModelLoader, save_dir="."):
    """SHAP结果增加非法值校验"""
    X_input = pd.DataFrame([{p: safe_float(data_dict.get(p, 0.0)) for p in Input_parameternames}])
    shap_results = {}
    for cost_key, model in [
        ("material", model_loader.model_material),
        ("manufacture_labour", model_loader.model_manlab),
        ("total_cost", model_loader.model_total)
    ]:
        dmatrix = xgb.DMatrix(X_input, feature_names=Input_parameternames)
        explainer = shap.Explainer(model)
        shap_values = explainer(dmatrix)

        # 处理SHAP值中的非法值
        shap_df = pd.DataFrame({
            "feature": Input_parameternames,
            "shap_value": [safe_float(v) for v in shap_values.values[0]]
        }).sort_values(by="shap_value", key=abs, ascending=False)

        excel_filename = f"XD_{COST_TYPE_CN_MAP[cost_key]}_SHAP.xlsx"
        excel_path = Path(save_dir) / excel_filename
        shap_df.to_excel(excel_path, index=False)
        shap_results[cost_key] = {
            "file_path": str(excel_path),
            "shap_data": shap_df.to_dict(orient="records")
        }
    return shap_results


# ===================== 工具函数：XD数据字段校验 =====================
def _check_xd_data_fields(data_dict: dict):
    missing_fields = [f for f in Input_parameternames if f not in data_dict]
    if missing_fields:
        raise ValueError(f"❌ XD数据缺失必填字段 → {missing_fields}")


# ===================== 核心函数1：XD单条预测 =====================
def run_xd_prediction(data_dict: dict, model_map=None, ori_db_path=None, with_analysis=True):
    _check_xd_data_fields(data_dict)
    mi = ModelInput(data_dict)
    X = xgb.DMatrix([mi.to_list()], feature_names=Input_parameternames)
    loader = XDModelLoader(model_map).load_all()
    predictor = XDPredictor(loader, X)
    predict_result = predictor.predict_all()

    analysis_result = {}
    if with_analysis and ori_db_path:
        finder = SimilarProductFinder(ori_db_path)
        cost_similar = finder.closest_cost_products_by_type(predict_result, top_n=5)
        perf_similar = finder.closest_perf_products(top_n=5)
        analysis_result["cost_similar_products"] = cost_similar
        analysis_result["perf_similar_products"] = perf_similar
        shap_result = generate_xd_shap_analysis(data_dict, loader)
        analysis_result["shap_analysis"] = shap_result

    return {
        "predict_result": predict_result,
        "analysis_result": analysis_result
    }


# ===================== 核心函数2：XD批量预测 =====================
def batch_run_xd_prediction(file_path, model_map, ori_db_path):
    file_path = Path(file_path).absolute()
    if not file_path.exists():
        raise FileNotFoundError(f"❌ XD输入文件不存在 → {file_path}")
    file_suffix = file_path.suffix.lower()
    if file_suffix not in SUPPORT_FILE_TYPES:
        raise ValueError(f"❌ XD仅支持{SUPPORT_FILE_TYPES}格式，当前为{file_suffix}")

    data_list = []
    if file_suffix == ".json":
        with open(file_path, 'r', encoding='utf-8') as f:
            single_data = json.load(f)
        _check_xd_data_fields(single_data)
        data_list.append(single_data)
    elif file_suffix == ".xlsx":
        df = pd.read_excel(file_path)
        df.columns = [col.strip() for col in df.columns]
        missing_cols = [f for f in Input_parameternames if f not in df.columns]
        if missing_cols:
            raise ValueError(f"❌ XD Excel缺失字段 → {missing_cols}")
        # 处理Excel中的非法值
        df[Input_parameternames] = df[Input_parameternames].applymap(safe_float)
        data_list = df[Input_parameternames].to_dict(orient='records')

    total_count = len(data_list)
    success_count = 0
    fail_count = 0
    predict_details = []

    for row_idx, data_dict in enumerate(data_list, start=1):
        try:
            single_result = run_xd_prediction(
                data_dict=data_dict,
                model_map=model_map,
                ori_db_path=ori_db_path,
                with_analysis=True
            )
            predict_details.append({
                "row_idx": row_idx,
                "input_data": data_dict,
                "predict_result": single_result["predict_result"],
                "analysis_result": single_result["analysis_result"],
                "status": "success"
            })
            success_count += 1
        except Exception as e:
            predict_details.append({
                "row_idx": row_idx,
                "input_data": data_dict,
                "predict_result": None,
                "analysis_result": None,
                "status": "failed",
                "error_msg": str(e)
            })
            fail_count += 1

    return {
        "total_count": total_count,
        "success_count": success_count,
        "fail_count": fail_count,
        "predict_details": predict_details
    }