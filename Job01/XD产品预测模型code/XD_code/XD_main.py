import json
import argparse
from XD_predict import run_prediction

data = {
    'JL': 1,
    'CD': 1,
    'WZSF': 1,
    'WZKG': 0,
    'LJBH': 0,
    'XCXW': 0,
    'JS': 4,
    'ZJ': 66,
    'CDB': 101.19617,
    'JX': 0.15,
    'DCJR': 1,
    '短时高温': 0,
    '耐火要求': 0,
    '炮振要求': 0,
    '工作包线内表面温度要求': 0,
    '除冰温度要求': 0,
    '防火和可燃性': 0,
    'DQY': 1,
    'WG': 1,
    'SR-温度下': 30,
    'SR-时间': 10,
    'YW-时间': 96,
    'YW-溶液pH值下界': 0,
    'YW-溶液pH值上界': 0,
    'PJZD': 0,
    'ZS': 0
}


model_map = {
    'material': 'xd_material_202511301628.json',
    'manufacture_labour': 'xd_manlab_202511301629.json',
    'total_cost': 'xd_total_202511301626.json'
    }



# if __name__ == "__main__":
#     # 命令行参数配置
#     parser = argparse.ArgumentParser(description="XD产品成本预测")
#
#     parser.add_argument("--data", help="输入的参数字典（JSON 格式）")
#     parser.add_argument("--model_map", help="模型路径字典（JSON 格式，仅预测需要）")
#
#     # 2. 解析命令行参数
#     args = parser.parse_args()
#
#     # 3. 转换 JSON 字符串为 Python 字典
#     data = json.loads(args.data) if args.data else None
#     model_map = json.loads(args.model_map) if args.model_map else None
#
#     # 调用主函数
#     run_prediction(data, model_map)




print(run_prediction(data,model_map))
