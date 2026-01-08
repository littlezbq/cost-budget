import pandas as pd
import math


# 复用安全浮点数函数
def safe_float(value, default=0.0):
    try:
        f_val = float(value)
        if math.isinf(f_val) or math.isnan(f_val):
            return default
        return f_val
    except (ValueError, TypeError):
        return default


class SimilarProductFinder:
    """ZD专用：从数据库Excel中找最相似的产品"""

    def __init__(self, db_path: str):
        self.df = pd.read_excel(db_path)
        # 初始化时清理所有数值列的非法值
        numeric_cols = self.df.select_dtypes(include=['float64', 'int64']).columns
        self.df[numeric_cols] = self.df[numeric_cols].applymap(safe_float)

        self.product_name_col = "产品名称"
        self.cost_cols_map = {
            "material": "直接材料",
            "manufacture_labour": "直接人工+制造费用",
            "total_cost": "总成本"
        }
        self.perf_exclude_cols = [self.product_name_col] + list(self.cost_cols_map.values())

    @property
    def perf_cols(self):
        return [col for col in self.df.columns if col not in self.perf_exclude_cols]

    def closest_cost_products_by_type(self, target_costs: dict, top_n: int = 5):
        cost_similar_results = {}
        for cost_key, excel_col in self.cost_cols_map.items():
            if excel_col not in self.df.columns:
                raise ValueError(f"❌ ZD数据库Excel缺失列：{excel_col}")

            df_copy = self.df[[self.product_name_col, excel_col]].copy()
            # 处理目标值的非法值
            target_val = safe_float(target_costs.get(cost_key, 0))
            # 计算距离时确保数值合法
            df_copy["distance"] = (df_copy[excel_col].apply(safe_float) - target_val) ** 2

            top5_indices = df_copy["distance"].nsmallest(top_n).index
            top5_products = self.df.loc[top5_indices, [self.product_name_col, excel_col]]
            # 转换结果时再次校验
            top5_products[excel_col] = top5_products[excel_col].apply(safe_float)
            cost_similar_results[cost_key] = top5_products.to_dict(orient="records")
        return cost_similar_results

    def closest_perf_products(self, top_n: int = 5):
        df_perf = self.df[self.perf_cols].copy()
        df_perf = df_perf.apply(pd.to_numeric, errors='coerce').fillna(0)
        # 清理性能列非法值
        df_perf = df_perf.applymap(safe_float)

        target_vector = pd.Series([0] * len(self.perf_cols), index=self.perf_cols)
        df_perf["distance"] = ((df_perf - target_vector) ** 2).sum(axis=1) ** 0.5
        # 处理距离值的非法值
        df_perf["distance"] = df_perf["distance"].apply(safe_float)

        top5_indices = df_perf["distance"].nsmallest(top_n).index
        top5_products = self.df.loc[top5_indices, [self.product_name_col]]
        return top5_products.to_dict(orient="records")