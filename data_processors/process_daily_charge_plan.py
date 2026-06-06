import numpy as np
from data_processors.process_aux_power import get_aux_power

#  计算充放电时间，是否进行充电和放电
def get_data_ifcharge_hour(df, hour_charge=None, hour_discharge=None):
    if hour_discharge is None:
        hour_discharge = [0, 19, 20, 21, 22, 23]  # 放电时间段
    if hour_charge is None:
        hour_charge = []  # 充电时间段
    df['ifcharge'] = ''
    df.loc[df['hour'].isin(hour_charge), 'ifcharge'] = 'charge'
    df.loc[df['hour'].isin(hour_discharge), 'ifcharge'] = 'discharge'
    return df



# 计算计划进行充电的 plan字段
def get_make_plan(df, remaining, max_power, eta_ch):
    df = df.copy()

    # 每小时最多可贡献的充电量
    df["charge_energy"] = np.minimum(df["net_pv"].clip(lower=0), max_power) * eta_ch

    # 按 pv 降序
    dfs = df.sort_values("net_pv", ascending=False).reset_index(drop=True)

    charged = 0.0
    selected_hours = []

    for _, row in dfs.iterrows():
        if charged >= remaining - 0.001:
            break

        if row["net_pv"] > 0:
            charge_energy = row["charge_energy"]

            if charged + charge_energy >= remaining:
                charged = remaining
            else:
                charged += charge_energy

            selected_hours.append(row["hour"])

    # 只输出 plan
    df["plan"] = df["hour"].isin(selected_hours)
    del df['charge_energy']
    return df
"""
'-------------------------------------------------------------------------
' 计算当天充电计划：基于净光伏（光伏 - op辅助 - 变电站辅助）
' 输入：dayPV - 当天24小时光伏数组，dayTemp - 当天24小时温度数组，
'       startSOC - 当天起始SOC，capacity - 容量，maxPower - 最大功率，
'       eta_ch - 充电效率，subAux - 变电站辅助
'-------------------------------------------------------------------------
"""
def get_ComputeDailyChargePlan(df_day=None,
                               start_soc=None,
                               capacity=None,
                               maxPower=None,
                               eta_ch=None,
                               subaux=None,
                               T_POINTS=None, OP_POINTS=None, IDLE_POINTS=None):
    """
    参数：
    - df_day pv: list or np.array, 当天每小时光伏发电功率 [0..23] = df['pv']
    - df_day temp: list or np.array, 每小时温度/辅助参数，用于计算运行辅助功率 = df['temp']
    - start_soc: float, 起始SOC (MWh)
    - capacity: float, 储能总容量 (MWh)
    - max_power: float, 储能充电最大功率 (MW)
    - eta_ch: float, 充电效率 (0~1)
    - subaux: float, 变电站固定辅助功率 (MW)

    返回：
    - plan: np.array(bool), 每小时是否充电 (24)
    """
    df_day['plan'] = 0 # 计划默认为0

    # -------------------------------
    # 计算净光伏 每天的数据    # 注意，这个mode vba 默认值是op
    # -------------------------------
    df_day["aux_op"] = df_day["temp"].apply(
        lambda x: get_aux_power(x, "op", T_POINTS, OP_POINTS, IDLE_POINTS))
    # 小于 0 的值全部截断成 0。
    df_day["net_pv"] = (df_day["pv"] - df_day["aux_op"] - subaux).clip(lower=0)

    # 剩余可充电容量 = 常见容量 - 初始容量
    remaining = capacity - start_soc
    # print(f"计算充电计划: 起始SOC={start_soc:.2f}, 剩余容量={remaining:.2f}")

    if remaining <= 0:
        return 0, df_day   # 不需要充电，全False
    # -------------------------------
    # 按净光伏降序排序  根据值，进行排序，选择光伏最多的，进行计算 ，累计到充满的 ，其余时间是可以充电，有问题
    # -------------------------------
    df_day.sort_values(by='net_pv', inplace=True, ascending=False)
    df_day = get_make_plan(df_day, remaining, maxPower, eta_ch)
    CountTrue = df_day['plan'].sum() # 可以 进行充电的时间段的个数
    df_day.sort_values(by='hour', inplace=True)
    df_day.reset_index(drop=True, inplace=True)
    return list(df_day['plan'])
