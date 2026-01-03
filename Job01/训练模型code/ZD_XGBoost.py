import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error, r2_score
from datetime import datetime
import os
import argparse

# 定义特征列名称（与ZD数据表一致）
column_names = ['DW','XHFK-到位反馈','XHFK-位置反馈','XHFS-LVDT','XHFS-主机二配件','XHFS-电压','XHFS-接近开关','XHFS-行程开关',
                'HZ','XHYD','YJGN','GNFZ-单向节流阀','GNFZ-节流阀','GNFZ-梭阀','JYYL','MF-内漏量','XC','SCL-伸出力/压载均值','SCL-收回力/拉载均值',
                'ZL','SM-总寿命(FH)','SM-总寿命(起落)','SM-总寿命(拦阻)']

# 目标变量中英对照（可选）
dict_col = {
    '总成本': 'total',
    '直接材料': 'material',
    '直接人工+制造费用': 'manlab'
}

dict_tong = {
    '单筒': 'dt',
    '双筒': 'st'
}

def train_and_save_zd_model(file_path, k, zd_type):
    """训练ZD模型并保存结果

    Args:
        file_path (str): Excel文件路径
        k (str): 目标变量（如'总成本'）
        zd_type (str): ZD类型（如'单筒'/'双筒'）
    """
    # 创建输出目录
    # input_dir = os.path.dirname(os.path.abspath(file_path))
    # save_dir = os.path.join(input_dir, 'output', 'ZD', f'ZD_{zd_type}', f'ZD_{zd_type}_{k}')
    # os.makedirs(save_dir, exist_ok=True)



    # 创建输出目录
    input_abs_path = os.path.dirname(os.path.abspath(file_path))
    input_dir = os.path.dirname(input_abs_path)  # 获取Job01目录
    save_dir = os.path.join(input_dir, 'output', 'zd', f'zd_{dict_col[k]}',f'{dict_tong[zd_type]}')
    os.makedirs(save_dir, exist_ok=True)


    # 读取数据（根据zd_type选择sheet）
    data = pd.read_excel(file_path, sheet_name=zd_type)
    X = data[column_names]
    y = data[k]
    X.fillna(0, inplace=True)

    # 准备DMatrix
    dtrain = xgb.DMatrix(X, label=y)

    # 分位数回归参数
    params = {
        "objective": "reg:quantileerror",
        "eval_metric": "quantile",
        "quantile_alpha": 0.7,  # 可调 0.8~0.95 控制偏高预测
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

    timestamp = datetime.now().strftime('%Y%m%d%H%M')

    # 保存模型
    model_path = os.path.join(save_dir, f"zd{dict_tong[zd_type]}_{dict_col[k]}_{timestamp}.json")
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
        zd_type=zd_type,
        timestamp=timestamp
    )

    # 输出结果
    print(f"模型已保存: {model_path}")
    print(f"R2: {r2:.4f}, MAPE: {mape:.6f}, RMSE: {rmse:.6f}")

def save_results(y_true, y_pred, r2, mape, rmse, save_dir, k, zd_type, timestamp):
    """保存预测结果和评估指标"""
    df_result = pd.DataFrame({
        "真实值": y_true,
        "预测值": y_pred,
        "误差(%)": np.abs(y_true - y_pred) / np.where(y_true == 0, 1, y_true) * 100
    })

    df_metrics = pd.DataFrame({
        "模型": [f'zd_{zd_type}_{dict_col.get(k, k)}_{timestamp}'],
        "时间": [timestamp],
        "R2": [r2],
        "MAPE": [mape],
        "RMSE": [rmse],
        "特征列": [column_names]
    })

    excel_path = os.path.join(save_dir, f"zd{dict_tong[zd_type]}_{dict_col.get(k, k)}_{timestamp}.xlsx")
    sheet_name_result = f"zd_{zd_type}_{k}_{timestamp}"[:31]  # Excel工作表名最大31字符

    if os.path.exists(excel_path):
        with pd.ExcelWriter(excel_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df_result.to_excel(writer, sheet_name=sheet_name_result, index=False)
            df_metrics.to_excel(writer, sheet_name=f"zd_{zd_type}_metrics", index=False)
    else:
        with pd.ExcelWriter(excel_path, engine="openpyxl", mode="w") as writer:
            df_result.to_excel(writer, sheet_name=sheet_name_result, index=False)
            df_metrics.to_excel(writer, sheet_name=f"zd_{zd_type}_metrics", index=False)

if __name__ == "__main__":
    # 命令行参数配置
    parser = argparse.ArgumentParser(description="ZD产品成本预测模型训练")
    parser.add_argument('--file_path', type=str,
                       help='Excel文件路径', default=r'E:\Work\algorithms\Job01\inputdata\ZD数据表.xlsx')
    parser.add_argument('--k', type=str,
                       help='目标变量（如"总成本"）', default='总成本')
    parser.add_argument('--type', type=str,
                       help='ZD类型（如"单筒"/"双筒"）', default='单筒')
    args = parser.parse_args()

    # 调用主函数
    train_and_save_zd_model(args.file_path, args.k, args.type)
