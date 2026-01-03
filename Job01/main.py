"""

这个先不管，我还没想是训练和预测分开放还是怎么弄
"""

import argparse
import warnings
import json

warnings.filterwarnings('ignore')


def run(type, data=None, model_map=None):
    """统一调用 XD/ZD 预测和训练
    Args:
        type (str): "1"(XD预测), "2"(ZD预测), "3"(XD训练), "4"(ZD训练)
        data (dict): 预测时传入的参数
        model_map (dict): 预测时使用的模型路径
    """
    if type == "1":
        # XD产品预测
        from XD产品预测模型code.XD_code.XD_predict import run_prediction
        if data is None:
            raise ValueError("XD预测需要传入 data!")
        result = run_prediction(data_dict=data, model_map=model_map)
        print("XD预测结果:", result)
    elif type == "2":
        pass
        # ZD产品预测
        # from ZD产品预测模型code.ZD_code.ZD_predict import run_prediction
        # if data is None:
        #     raise ValueError("ZD预测需要传入 data!")
        # result = run_prediction(data_dict=data)  # ZD可能有自己的model_map逻辑
        # print("ZD预测结果:", result)
    elif type == "3":
        # XD模型训练
        from 训练模型code.XD_XGBoost import main as train_xd
        pass
    elif type == "4":
        # ZD模型训练
        from 训练模型code.ZD_XGBoost import main as train_zd
        pass
    else:
        raise ValueError("type 必须是 1/2/3/4!")


#
# # 示例调用
# if __name__ == "__main__":
#     # 示例数据（可动态传入）
#
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
#
#     # XD模型路径（可动态传入）
#     model_map = {
#         'material': 'xd_material_202511301628.json',
#         'manufacture_labour': 'xd_manlab_202511301629.json',
#         'total_cost': 'xd_total_202511301626.json'
#     }
#     # 调用方式
#     run(type="1", data=data, model_map=model_map)  # XD预测
if __name__ == "__main__":
    # 1. 设置命令行参数解析器
    parser = argparse.ArgumentParser(description="XD/ZD 产品预测和训练")
    parser.add_argument("--type", required=True, help="功能类型: 1(XD预测)/2(ZD预测)/3(XD训练)/4(ZD训练)")
    parser.add_argument("--data", help="输入的参数字典（JSON 格式）")
    parser.add_argument("--model_map", help="模型路径字典（JSON 格式，仅预测需要）")

    # 2. 解析命令行参数
    args = parser.parse_args()

    # 3. 转换 JSON 字符串为 Python 字典
    data = json.loads(args.data) if args.data else None
    model_map = json.loads(args.model_map) if args.model_map else None

    # 4. 调用主函数
    run(type=args.type, data=data, model_map=model_map)
