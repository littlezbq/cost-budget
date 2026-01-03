import xgboost as xgb
from pathlib import Path

from Job01.XD产品预测模型code.XD_code.XD_data_input import ModelInput, Input_parameternames

model_map = {
    'material': 'xd_material_202511301628.json',
    'manufacture_labour': 'xd_manlab_202511301629.json',
    'total_cost': 'xd_total_202511301626.json'
}


class ModelLoader:
    def __init__(self, model_map=None):
        if model_map is None:  # 默认值
            model_map = {
                'material': 'xd_material_202511301628.json',
                'manufacture_labour': 'xd_manlab_202511301629.json',
                'total_cost': 'xd_total_202511301626.json'
            }
        project_root = Path(__file__).resolve().parent.parent
        model_dir = project_root / 'XD_model'

        self.path_material = model_dir / model_map["material"]
        self.path_manlab = model_dir / model_map["manufacture_labour"]
        self.path_total = model_dir / model_map["total_cost"]

        self.model_material = None
        self.model_manlab = None
        self.model_total = None

    def load_all(self):
        self.model_material = xgb.Booster()
        self.model_material.load_model(str(self.path_material))

        self.model_manlab = xgb.Booster()
        self.model_manlab.load_model(str(self.path_manlab))

        self.model_total = xgb.Booster()
        self.model_total.load_model(str(self.path_total))

        return self


class Predictor:
    def __init__(self, loader: ModelLoader, X):
        if loader.model_material is None:
            raise ValueError("模型未加载，请先调用 loader.load_all()")
        self.loader = loader
        self.X = X

    def predict_all(self):
        return {
            "material": float(self.loader.model_material.predict(self.X)[0]),
            "manufacture_labour": float(self.loader.model_manlab.predict(self.X)[0]),
            "total_cost": float(self.loader.model_total.predict(self.X)[0])
        }


def run_prediction(data_dict: dict, model_map=None):
    mi = ModelInput(data_dict)
    X = xgb.DMatrix(
        [mi.to_list()],
        feature_names=Input_parameternames
    )

    loader = ModelLoader(model_map).load_all()

    predictor = Predictor(loader, X)
    return predictor.predict_all()
