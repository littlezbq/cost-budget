
Input_parameternames =[
    'JL','CD','WZSF','WZKG','LJBH','XCXW','JS','ZJ','CDB','JX','DCJR','短时高温','耐火要求',
    '炮振要求','工作包线内表面温度要求','除冰温度要求','防火和可燃性','DQY','WG','SR-温度下','SR-时间',
    'YW-时间','YW-溶液pH值下界','YW-溶液pH值上界','PJZD','ZS'
]

class ModelInput:
    def __init__(self,data_dict: dict, default_value=0.0):
        self.data = {}
        missing_items = []

        for parameter_name in Input_parameternames:
            if parameter_name in data_dict:
                self.data[parameter_name] = float(data_dict[parameter_name])
            else:
                self.data[parameter_name] = default_value
                missing_items.append(parameter_name)

        if missing_items:
            print(f'[Warning] 以下参数未提供，已使用默认值 {default_value} ：\n{missing_items}')

    def to_list(self):
        return[self.data[parameter_name] for parameter_name in Input_parameternames]