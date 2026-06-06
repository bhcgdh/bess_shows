from data_processors.process_aux_power import get_aux_power
from data_processors.process_daily_charge_plan import get_ComputeDailyChargePlan

# 非放电时间段的处理 》 光伏 <= 0   光伏无出力或为负：空闲，辅助由电网提供
def charge_pv_negative(pv=None,temp=None,subAux=None,
                                    T_POINTS=None, OP_POINTS=None, IDLE_POINTS=None,params=None):
    # 光伏无出力或为负，辅助由电网提供
    state = "Standby"
    # 计算不同温度下返回的功率
    # print(f" charge_pv_negative ", 'idle')
    aux_storage = get_aux_power(temp, 'idle', T_POINTS, OP_POINTS, IDLE_POINTS)
    pvAuxDemand = max(-pv, 0)
    aux_total = aux_storage + subAux + pvAuxDemand

    # 电池不放电，光伏不向储能或变电站
    bat_to_storage = 0
    bat_to_sub = 0
    bat_to_pv = 0
    pv_to_storage = 0
    pv_to_sub = 0

    info = F" 非放电时间段的处理,  光伏 <= 0"
    params['info'] = params['info'] + info

    # 电网提供辅助功率
    grid_to_storage = aux_storage
    grid_to_sub = subAux
    grid_to_pv = pvAuxDemand
    grid_power = aux_total

    # 其他功率流向
    Pdis_ac = 0
    storage2grid = 0
    pv2grid = max(0, pv)
    Pin_ac = 0
    Pin_dc = 0
    Pdis_dc = 0

    pv_to_curtailed = pv - pv_to_storage - pv_to_sub
    pv_to_curtailed = 0 # 光伏弃用

    info = (
        F" 非放电时间段的处理,  光伏 <= 0光伏 {pv}    光伏给储能 {pv_to_storage}  光伏给 {pv_to_sub}  光伏给放弃 {pv_to_curtailed}  ")
    params['info'] = params['info'] + info

    return {
        "state": state,
        "pvAuxDemand": pvAuxDemand,
        "aux_storage": aux_storage,
        "aux_total": aux_total,
        "bat_to_storage": bat_to_storage,
        "bat_to_sub": bat_to_sub,
        "bat_to_pv": bat_to_pv,
        "pv_to_storage": pv_to_storage,
        "pv_to_sub": pv_to_sub,
        "pv_to_curtailed":pv_to_curtailed,# 新增 光伏弃用
        "grid_to_storage": grid_to_storage,
        "grid_to_sub": grid_to_sub,
        "grid_to_pv": grid_to_pv,
        "grid_power": grid_power,
        "Pdis_ac": Pdis_ac,
        "storage2grid": storage2grid,
        "pv2grid": pv2grid,
        "Pin_ac": Pin_ac,
        "Pin_dc": Pin_dc,
        "Pdis_dc": Pdis_dc,
    }
