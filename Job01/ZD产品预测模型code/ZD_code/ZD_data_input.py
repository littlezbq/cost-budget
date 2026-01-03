
Input_parameternames =[
    'DW','XHFK-到位反馈','XHFK-位置反馈','XHFS-LVDT','XHFS-主机二配件','XHFS-电压','XHFS-接近开关','XHFS-行程开关',
    'HZ','XHYD','YJGN','GNFZ-单向节流阀','GNFZ-节流阀','GNFZ-梭阀','JYYL','MF-内漏量','XC','SCL-伸出力/压载均值',
    'SCL-收回力/拉载均值','ZL','SM-总寿命(FH)','SM-总寿命(起落)','SM-总寿命(拦阻)'
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