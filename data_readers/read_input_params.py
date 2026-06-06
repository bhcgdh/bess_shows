import sys
import pandas as pd
from pathlib import Path

# 动态添加项目根目录 , 可
def setup_path():
    current = Path(__file__).resolve()
    # 向上查找包含 bess_shows 目录的父目录
    for parent in current.parents:
        if (parent / "bess_shows").is_dir():
            root = parent
            break
    else:
        # 如果没找到，假设当前在 bess_shows 下两级
        root = current.parents[1]  # 向上两级到 bess_shows 的父目录
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
setup_path()
try:
    from .read_design_sheet_to_json import get_design_sheet_params

except:
    from read_design_sheet_to_json import get_design_sheet_params

"""

# 计算 》 根据基本参数计算 充电效率 eta_ch （相比放电，多一个电池参数）
def param_eta_ch(params):
    params['eta_ch'] = (params["DC Cable Efficiency [%]:"]*
                        params["PCS Efficiency [%]:"]*
                        params["LV Cable Efficiency [%]:"]*
                        params["MV Transformer Efficiency [%]:"]*
                        params["MV Cable Efficiency [%]:"]*
                        params["Battery Efficiency [%]:"]) # 每年不一样
    return params

# 计算 》 根据基本参数计算 放电效率 eta_dis
def param_eta_dis(params):
    params['eta_dis'] = (params["DC Cable Efficiency [%]:"]*
                        params["PCS Efficiency [%]:"]*
                        params["LV Cable Efficiency [%]:"]*
                        params["MV Transformer Efficiency [%]:"]*
                        params["MV Cable Efficiency [%]:"]
                         )
    return params

"""

# 读取所有的参数 》
def get_origh_params(params):
    all_params = get_design_sheet_params()
    params.update(all_params)
    return params

