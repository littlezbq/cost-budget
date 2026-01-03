import argparse
import json
from ZD_predict import run_prediction

data = {
    'DW': 0,
    'XHFK-到位反馈': 0,
    'XHFK-位置反馈': 1,
    'XHFS-LVDT': 1,
    'XHFS-主机二配件': 0,
    'XHFS-电压': 0,
    'XHFS-接近开关': 0,
    'XHFS-行程开关': 0,
    'HZ': 0,
    'XHYD': 4,
    'YJGN': 0,
    'GNFZ-单向节流阀': 0,
    'GNFZ-节流阀': 0,
    'GNFZ-梭阀': 0,
    'JYYL': 28,
    'MF-内漏量': 300,
    'XC': 225,
    'SCL-伸出力/压载均值': 213392,
    'SCL-收回力/拉载均值': 213392,
    'ZL': 35.4,
    'SM-总寿命(FH)': 3000,
    'SM-总寿命(起落)': 0,
    'SM-总寿命(拦阻)': 0
}
#
# result = run_prediction(2, data)
# print(result)

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




# if __name__ == "__main__":
#     # 命令行参数配置
#     parser = argparse.ArgumentParser(description="XD产品成本预测")
#     parser.add_argument("--zd_type", type = str,help="单筒/双筒")
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
#     run_prediction(args.zd_type,data, model_map)


#
result = run_prediction(2,data, model_map=model_map)
print(result)
