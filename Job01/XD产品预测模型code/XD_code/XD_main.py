import pandas as pd
import shap
import xgboost as xgb
from XD_predict import ModelLoader,batch_run_prediction
from XD_compare import SimilarProductFinder

filepath = r"E:\Work\cost\cost-budget\store_files\a859e926-7555-4ec9-bed6-f490e5e72cd7.xlsx"       # 数据库路径
ori_db_path = r"E:\Work\cost\cost-budget\Job01\inputdata\XD数据表.xlsx"


# data = {
#     'JL': 1,
#     'CD': 1,
#     'WZSF': 1,
#     'WZKG': 0,
#     'LJBH': 0,
#     'XCXW': 0,
#     'JS': 4,
#     'ZJ': 66,
#     'CDB': 101.19617,
#     'JX': 0.15,
#     'DCJR': 1,
#     '短时高温': 0,
#     '耐火要求': 0,
#     '炮振要求': 0,
#     '工作包线内表面温度要求': 0,
#     '除冰温度要求': 0,
#     '防火和可燃性': 0,
#     'DQY': 1,
#     'WG': 1,
#     'SR-温度下': 30,
#     'SR-时间': 10,
#     'YW-时间': 96,
#     'YW-溶液pH值下界': 0,
#     'YW-溶液pH值上界': 0,
#     'PJZD': 0,
#     'ZS': 0
# }


model_map = {
    'material': 'xd_material_202511301628.json',
    'manufacture_labour': 'xd_manlab_202511301629.json',
    'total_cost': 'xd_total_202511301626.json'
    }


cost_result = batch_run_prediction(filepath,model_map,ori_db_path)
# print('XD成本预测结果:')
# print(cost_result)
#
# finder = SimilarProductFinder(ori_path)
#
# # 成本最相近
# cost_similar_dict = finder.closest_cost_products_by_type(cost_result, top_n=5)
# cost_type_map = {
#     "material": "直接材料",
#     "manufacture_labour": "直接人工+制造费用",
#     "total_cost": "总成本"
# }
# for cost_type, df in cost_similar_dict.items():
#     print(f"\n[{cost_type_map[cost_type]}] 最相近的 5 个产品:")
#     print(df)
#
# # 性能最相近
# perf_similar = finder.closest_perf_products(top_n=5)
# print("\n性能最相近的 5 个产品:")
# print(perf_similar)
#
# loader = ModelLoader().load_all()
#
# model_paths = {
#     "material": loader.path_material,
#     "manufacture_labour": loader.path_manlab,
#     "total_cost": loader.path_total
# }
#
# X_input = pd.DataFrame([data])
#
# for cost_type, model_path in model_paths.items():
#     print(f"\n======== [{cost_type_map[cost_type]} SHAP] ========")
#
#     model = xgb.Booster()
#     model.load_model(str(model_path))
#     print("[信息] XGBoost Booster 模型加载成功")
#
#     dmatrix = xgb.DMatrix(X_input, feature_names=list(X_input.columns))
#
#     explainer = shap.Explainer(model)
#     shap_values = explainer(dmatrix)
#
#     shap_df = pd.DataFrame({
#         "feature": X_input.columns,
#         "shap_value": shap_values.values[0]
#     }).sort_values(by="shap_value", key=abs, ascending=False)
#
#     excel_path = f'XD{cost_type_map[cost_type]} SHAP.xlsx'
#     shap_df.to_excel(excel_path, index=False)
#     print(f"[信息] SHAP数据已保存: {excel_path}")
#
#     # print("\n每个特征对预测的贡献 (SHAP值):")
    # print(shap_df)
