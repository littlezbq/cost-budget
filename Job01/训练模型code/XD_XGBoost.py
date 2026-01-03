import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error, r2_score
from datetime import datetime
import os
import argparse

# 定义特征列名称
column_names = ['JL', 'CD', 'WZSF', 'WZKG', 'LJBH', 'XCXW', 'JS', 'ZJ', 'CDB', 'JX', 'DCJR', '短时高温', '耐火要求',
                '炮振要求',
                '工作包线内表面温度要求', '除冰温度要求', '防火和可燃性', 'DQY', 'WG', 'SR-温度下', 'SR-时间',
                'YW-时间',
                'YW-溶液pH值下界', 'YW-溶液pH值上界', 'PJZD', 'ZS']

# 目标中英对照
dict_col = {
    '直接材料': 'material',
    '直接人工+制造费用': 'manlab',
    '总成本': 'total'
    }

def train_and_save_xd_model(file_path, k):
    """训练模型并保存结果

    Args:
        file_path (str): Excel文件路径
        k (str): 模型名称/目标变量
    """
    # 创建输出目录
    input_abs_path = os.path.dirname(os.path.abspath(file_path))
    input_dir = os.path.dirname(input_abs_path)  # 获取Job01目录
    save_dir = os.path.join(input_dir, 'output', 'xd', f'xd_{dict_col[k]}')
    os.makedirs(save_dir, exist_ok=True)

    # 读取数据
    data = pd.read_excel(file_path, sheet_name='Sheet1')
    X = data[column_names]
    y = data[k]
    X.fillna(0, inplace=True)

    dtrain = xgb.DMatrix(X, label=y)

    # 分位数回归参数
    params = {
        "objective": "reg:quantileerror",
        "eval_metric": "quantile",
        "quantile_alpha": 0.6,
        "eta": 0.05,
        "max_depth": 20,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "seed": 42
    }

    # 训练模型
    watchlist = [(dtrain, "train")]
    bst = xgb.train(params=params, dtrain=dtrain, num_boost_round=500, evals=watchlist, verbose_eval=50)

    # 预测并计算指标
    y_pred = bst.predict(dtrain)
    r2 = r2_score(y, y_pred)
    mape = mean_absolute_percentage_error(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))

    # timestamp = datetime.now().strftime('%Y.%m.%d_%H.%M.%S')

    # 新的时间戳格式（不带分隔符）
    timestamp = datetime.now().strftime('%Y%m%d%H%M')

    # 保存模型
    model_path = os.path.join(save_dir, f"xd_{dict_col[k]}_{timestamp}.json")
    bst.save_model(model_path)

    # 保存结果
    save_results(
        y_true=y.values,
        y_pred=y_pred,
        r2=r2,
        mape=mape,
        rmse=rmse,
        save_dir=save_dir,
        k=k,
        timestamp=timestamp
    )

    # 输出结果
    print(f"模型已保存: {model_path}")
    print(f"R2: {r2:.4f}, MAPE: {mape:.6f}, RMSE: {rmse:.6f}")


def save_results(y_true, y_pred, r2, mape, rmse, save_dir, k, timestamp):
    """保存预测结果和评估指标"""
    df_result = pd.DataFrame({
        "真实值": y_true,
        "预测值": y_pred,
        "误差(%)": np.abs(y_true - y_pred) / np.where(y_true == 0, 1, y_true) * 100
    })

    df_metrics = pd.DataFrame({
        "模型": [f'xd_{dict_col[k]}_{timestamp}'],
        "时间": [timestamp],
        "R2": [r2],
        "MAPE": [mape],
        "RMSE": [rmse],
        "特征列": [column_names]
    })

    excel_path = os.path.join(save_dir, f"xd_{dict_col[k]}_{timestamp}..xlsx")
    sheet_name_result = f"xd_{dict_col[k]}_{timestamp}"[:31]  # Excel工作表名最大31字符

    if os.path.exists(excel_path):
        with pd.ExcelWriter(excel_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df_result.to_excel(writer, sheet_name=sheet_name_result, index=False)
            df_metrics.to_excel(writer, sheet_name=f"xd_{dict_col[k]}_metrics", index=False)
    else:
        with pd.ExcelWriter(excel_path, engine="openpyxl", mode="w") as writer:
            df_result.to_excel(writer, sheet_name=sheet_name_result, index=False)
            df_metrics.to_excel(writer, sheet_name=f"xd_{dict_col[k]}_metrics", index=False)


if __name__ == "__main__":
    # 设置命令行参数解析器
    parser = argparse.ArgumentParser(description="XD产品训练")
    parser.add_argument('--file_path', type=str,
                        help='Excel文件路径', default=r'E:\Work\algorithms\Job01\inputdata\XD数据表.xlsx')
    parser.add_argument('--k', type=str,
                        help='模型名称/目标变量，例如: 直接人工+制造费用', default='直接人工+制造费用')
    args = parser.parse_args()

    # 调用主函数
    train_and_save_xd_model(args.file_path, args.k)
