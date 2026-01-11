import os
from pathlib import Path

# ========== 核心配置（全局唯一，所有地方都用这个配置）【修复核心位置】 ==========
# 你指定的路径存储文件目录+名称
PATH_MANAGE_DIR = Path("path_management")
# 自动创建目录
PATH_MANAGE_DIR.mkdir(parents=True, exist_ok=True)
# 关键修复：PATH_STORE_FILE 定义为【Path对象】而非字符串，才能调用.exists()方法
PATH_STORE_FILE = PATH_MANAGE_DIR / "path_management.txt"

# 编码格式
FILE_ENCODING = "utf-8"


class PathStore:
    """
    极简路径存储工具类 - 只维护最新的文件路径
    功能：1. 写入指定key的最新绝对路径 2. 读取指定key的最新绝对路径
    特性：覆盖式写入（永远只保留最新1条）、自动创建文件、异常友好
    """

    @staticmethod
    def write_path(key: str, abs_path: str) -> bool:
        """
        写入【键值对】到文本文件，覆盖原有同key的内容，永远只保留最新值
        :param key: 路径标识（如 zd_single_path / dfx_path / zd_double_path / xd_path）
        :param abs_path: 要保存的文件绝对路径
        :return: 写入成功返回True
        """
        # 校验路径合法性
        if not os.path.isfile(abs_path):
            raise FileNotFoundError(f"要保存的路径不是有效文件：{abs_path}")

        # 读取原有内容（字典格式）
        content_dict = PathStore.read_all()
        # 覆盖写入最新路径（核心：只保留最新）
        content_dict[key] = abs_path

        # 写入文本文件（键值对格式，一行一个，极简）
        with open(PATH_STORE_FILE, "w", encoding=FILE_ENCODING) as f:
            for k, v in content_dict.items():
                f.write(f"{k}={v}\n")
        return True

    @staticmethod
    def read_path(key: str) -> str:
        """
        读取指定key对应的最新绝对路径
        :param key: 路径标识（如 zd_single_path / dfx_path）
        :return: 对应的绝对路径字符串
        """
        content_dict = PathStore.read_all()
        if key not in content_dict:
            raise KeyError(f"未找到[{key}]对应的路径，请先执行对应计算生成结果！")

        abs_path = content_dict[key]
        # 校验路径是否存在（防止文件被删除）
        if not os.path.isfile(abs_path):
            raise FileNotFoundError(f"[{key}]对应的文件已被删除：{abs_path}")
        return abs_path

    @staticmethod
    def read_all() -> dict:
        """读取所有已保存的键值对，返回字典"""
        content_dict = {}
        # 文件不存在则自动创建空文件
        if not PATH_STORE_FILE.exists():
            with open(PATH_STORE_FILE, "w", encoding=FILE_ENCODING) as f:
                f.write("")
            return content_dict

        # 读取文件并解析键值对
        with open(PATH_STORE_FILE, "r", encoding=FILE_ENCODING) as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if line and "=" in line:
                    k, v = line.split("=", 1)  # 防止路径中包含=号
                    content_dict[k] = v.strip()
        return content_dict


# 全局实例，所有地方直接导入这个实例调用即可，不用重复创建
path_store = PathStore()