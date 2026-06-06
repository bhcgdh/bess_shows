import yaml
import numpy as np
import pandas as pd
import os



# 文件夹是否存在，不存在则创建
def utils_ensure_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"文件夹已创建: {folder_path}")
    else:
        print(f"文件夹已存在: {folder_path}")

# 检测数据是否完整，符合需要的数据 - 未使用
def utils_check_result_keys(result, field_names=None, hour=None):
    """
    检查每小时 result 字典是否包含所有需要的字段。
    如果缺失字段，会打印警告。

    参数：
        result : dict
            每小时计算得到的 result 字典
        field_names : list[str], 可选
            需要检查的字段名列表
        hour : int, 可选
            当前小时，用于打印
    """
    # 默认常用字段
    if field_names is None:
        field_names = ['soc|capacity', 'aux_storage', 'subAux', 'pv2grid', 'storage2grid',
                       'state', 'Pin_ac', 'Pdis_ac', 'pv_to_storage', 'pv_to_sub',
                       'Pin_dc', 'Pdis_dc', 'bat_to_storage', 'bat_to_sub', 'grid_power',
                       'bat_to_pv', 'soc', 'hv_power']

    for key in field_names:
        if key not in result:
            print(f"时间: {hour} ⚠️ 缺少 key: '{key}'，")

# 字典数据保存到yaml中
def utils_save_params_to_yaml(params, file_path):
    """
    保存 params 字典为 YAML，列表保持在同一行，末尾带逗号。
    """
    def convert(obj):
        
        # numpy 数组转列表
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        return obj

    # 转换数据
    params_clean = {k: convert(v) for k, v in params.items()}

    # 自定义 representer 让列表保持 inline
    def repr_list(dumper, data):
        
        # 添加列表末尾逗号
        text = "[" + ", ".join(str(i) for i in data) + ",]"
        return dumper.represent_scalar('tag:yaml.org,2002:str', text)

    yaml.add_representer(list, repr_list)

    with open(file_path, 'w') as f:
        yaml.dump(params_clean, f, sort_keys=False)

# 结果数据和统计数据进行拼接
def utils_insert_df_into_df_GWh(df, df2, distance_from_end=1):
    """
    将 df2 插入到 df 的指定列位置，并可保存到文件

    参数:
    df : pd.DataFrame
        原始大 DataFrame
    df2 : pd.DataFrame
        要插入的小 DataFrame
    insert_pos : int or None
        插入位置索引，如果为 None，使用 distance_from_end 计算位置
    distance_from_end : int
        当 insert_pos=None 时，从最后列往hou的偏移距离
    save_path : str or None
        保存路径，例如 "output.xlsx" 或 "output.csv"
    save_type : str
        保存类型 "excel" 或 "csv"

    返回:
    pd.DataFrame
        合并后的 DataFrame
    """
    # ---------- Step 1: 补齐行数 ----------
    if df2.shape[0] < df.shape[0]:
        filler = pd.DataFrame(np.nan, index=range(df.shape[0] - df2.shape[0]), columns=df2.columns)
        df2_full = pd.concat([df2, filler], ignore_index=True)
    else:
        df2_full = df2.copy()

    # ---------- Step 2: 计算插入位置 ----------
    insert_pos = df.shape[1] + distance_from_end
    df_left = df.iloc[:, :insert_pos]
    df_right = df.iloc[:, insert_pos:]

    # ---------- Step 3: 拼接 ----------
    df_new = pd.concat([df_left, df2_full, df_right], axis=1)
    return df_new

