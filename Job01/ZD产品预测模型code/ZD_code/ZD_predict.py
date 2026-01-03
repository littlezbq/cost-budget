import xgboost as xgb
from pathlib import Path
from ZD产品预测模型code.ZD_code.ZD_data_input import Input_parameternames, ModelInput

# model_map = {
#     1: {
#         'material': 'zddt_material_202511021713.json',
#         'manufacture_labour': 'zddt_manlab_202511021715.json',
#         'total_cost': 'zddt_total_202511021716.json'
#     },        # 1代表作动单筒
#     2: {
#         'material': 'zdst_material_202511021711.json',
#         'manufacture_labour': 'zdst_manlab_202511021709.json',
#         'total_cost': 'zdst_total_202511021707.json'
#     }        # 2代表作动双筒
# }

class ModelLoader:
    def __init__(self, product_type: int,model_map=None):
        if model_map is None: # 默认值
            model_map = {
                1: {
                    'material': 'zddt_material_202511021713.json',
                    'manufacture_labour': 'zddt_manlab_202511021715.json',
                    'total_cost': 'zddt_total_202511021716.json'
                },  # 1代表作动单筒
                2: {
                    'material': 'zdst_material_202511021711.json',
                    'manufacture_labour': 'zdst_manlab_202511021709.json',
                    'total_cost': 'zdst_total_202511021707.json'
                }  # 2代表作动双筒
            }
        if product_type not in model_map:
            raise ValueError('product_type must be in model_map')
        project_root = Path(__file__).resolve().parent.parent
        model_dir = project_root / 'ZD_model'
        paths = model_map[product_type]

        self.path_material = model_dir / paths["material"]
        self.path_manlab = model_dir / paths["manufacture_labour"]
        self.path_total = model_dir / paths["total_cost"]

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

def run_prediction(product_type: int, data_dict: dict,model_map=None):
    mi = ModelInput(data_dict)
    X = xgb.DMatrix(
        [mi.to_list()],
        feature_names=Input_parameternames
    )

    loader = ModelLoader(product_type,model_map).load_all()

    predictor = Predictor(loader, X)
    return predictor.predict_all()