import numpy as np
import pandas as pd

def cal_pv_GWh(df, params):
    # round是用来取得小数点后留个位置的 # sheet2: 统计值，无列名，第一列第二行为 Phase C
    exported_energy = df['hv_power'].sum() / 1000

    # MV/HV Transformer Efficiency （中压/高压变压器效率-99.50% ）
    # HV Losses up to DP[%]: （ 高压至配电点损耗率-99.5%）
    tmp = params["MV/HV Transformer Efficiency[%]:"] * params["HV Losses up to DP[%]:"]
    exported_bess = tmp * df['storage2grid'].sum() / 1000

    imported_energy = df['grid_power'].sum() / 1000

    # 小数点后6位
    exported_energy = round(exported_energy, 6)
    exported_bess = round(exported_bess, 6)
    imported_energy = round(imported_energy, 6)

    # 判断有多少个数据，在 target_hv_power 高压侧目标放电功率 MW 的左右，直接使用=等号，会出现数据偏移，即500变成499.99999，等号不成立，
    count_target = np.isclose(df['hv_power'], params['target_hv_power']).sum()
    discharge_rate = round(count_target / (365 * 6), 6)

    stats_data = [
        ["Phase A", "Exported Energy [GWh]", exported_energy],
        [None, "Energy from BESS[GWh]", exported_bess],
        [None, "Imported Energy[GWh]", imported_energy],
        [None, "Discharge satisfaction rate", discharge_rate]
    ]
    stats_df = pd.DataFrame(stats_data)
    return stats_df