import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error, r2_score
from datetime import datetime
import os
import argparse
import shutil
from core.path_store import path_store
from core.config import TEMP_OUTPUT_PATH,PERM_OUTPUT_PATH
# ===================== 目录配置（核心修改：区分临时/永久） =====================

# 确保目录存在
os.makedirs(TEMP_OUTPUT_PATH, exist_ok=True)
os.makedirs(PERM_OUTPUT_PATH, exist_ok=True)




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
    """
    训练ZD模型并保存结果
    Args:
        file_path (str): Excel文件路径
        k (str): 目标变量（如'总成本'）
    """
    # 保存到临时目录
    save_dir = os.path.join(TEMP_OUTPUT_PATH)
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
    excel_path = save_results(
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
    print(f"临时模型已保存: {model_path}")
    print(f"R2: {r2:.4f}, MAPE: {mape:.6f}, RMSE: {rmse:.6f}")

    path_store.write_path(f"zd{dict_tong[zd_type]}_temp_model_path", os.path.abspath(model_path))
    path_store.write_path(f"zd{dict_tong[zd_type]}_temp_excel_path", os.path.abspath(excel_path))

    # 新增返回值
    return {
        "temp_model_path": os.path.abspath(model_path),  # 临时模型绝对路径
        "temp_excel_path": os.path.abspath(excel_path),  # 临时模型的系数保存路径
        "r2": round(r2, 4),  # 模型评估指标R2（保留4位小数）
        "mape": round(mape, 6),  # 模型评估指标MAPE（保留6位小数）
        "rmse": round(rmse, 4),  # 模型评估指标RMSE（保留4位小数）
        "target_var": k,  # 训练的目标变量（如：总成本、直接材料）
        "train_time": timestamp  # 训练时间戳（和模型文件名一致）
    }


# ===================== 新增函数：保存模型（复制临时文件到永久目录） =====================
def save_zd_model_permanent(temp_model_path, temp_excel_path,zd_type):
    """
    将临时目录的模型/结果文件复制到永久目录
    :param temp_model_path: 临时模型文件路径（训练返回的temp_model_path）
    :param temp_excel_path: 临时Excel结果路径
    :return: 永久目录的文件路径
    """
    # 1. 校验临时文件是否存在
    if not os.path.exists(temp_model_path):
        raise ValueError(f"临时模型文件不存在 → {temp_model_path}")
    if not os.path.exists(temp_excel_path):
        raise ValueError(f"临时Excel文件不存在 → {temp_excel_path}")

    # 2. 构建永久目录路径（按筒型/目标变量分类，便于管理）
    # 从临时文件名中解析筒型/目标变量（比如zd_dt_total_202601071234.json → dt/total）
    model_filename = os.path.basename(temp_model_path)
    perm_dir = os.path.join(PERM_OUTPUT_PATH)
    os.makedirs(perm_dir, exist_ok=True)

    # 3. 复制文件到永久目录（保留原文件名）
    perm_model_path = os.path.join(perm_dir, model_filename)
    perm_excel_path = os.path.join(perm_dir, os.path.basename(temp_excel_path))

    # 复制模型文件
    shutil.copy2(temp_model_path, perm_model_path)
    # 复制Excel结果文件
    shutil.copy2(temp_excel_path, perm_excel_path)

    print(f"✅ 模型已永久保存：{os.path.abspath(perm_model_path)}")
    print(f"✅ 结果Excel已永久保存：{os.path.abspath(perm_excel_path)}")

    path_store.write_path(f"zd{dict_tong[zd_type]}_perm_model_path", os.path.abspath(perm_model_path))
    path_store.write_path(f"zd{dict_tong[zd_type]}_perm_excel_path", os.path.abspath(perm_excel_path))


    return {
        "perm_model_path": os.path.abspath(perm_model_path),
        "perm_excel_path": os.path.abspath(perm_excel_path),
        "msg": "模型已从临时目录复制到永久目录"
    }


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
    return excel_path


