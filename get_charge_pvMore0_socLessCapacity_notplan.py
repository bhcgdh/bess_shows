from data_processors.process_aux_power import get_aux_power
from data_processors.process_daily_charge_plan import get_ComputeDailyChargePlan

# 非充电计划时（Standby）光伏与辅助功率分配
def charge_pv_positive_with_soc_notplan(pv=None, temp=None,
                                        subAux=None, pvAuxDemand=None,
                 T_POINTS=None, OP_POINTS=None, IDLE_POINTS=None,params=None):
    state = "Standby"
    # 获取辅助功率（空闲模式）
    # print(f" charge_pv_positive_with_soc_notplan ", 'idle')
    aux_storage = get_aux_power(temp, 'idle', T_POINTS, OP_POINTS, IDLE_POINTS)

    aux_total = aux_storage + subAux + pvAuxDemand

    # 光伏是否充足覆盖所有辅助
    if pv >= aux_total:
        pv_to_storage = aux_storage
        pv_to_sub = subAux
        pv_to_pv = pvAuxDemand

        bat_to_storage = bat_to_sub = bat_to_pv = 0
        grid_to_storage = grid_to_sub = grid_to_pv = 0
        grid_power = 0
        pv2grid = pv - aux_total

        pv_to_curtailed = pv - aux_total # 光伏以覆盖，
        info = (F" 非充电计划时（Standby）光伏与辅助功率分配,  光伏充足，光伏 {pv}  光伏给自己 {pv_to_pv}  光伏给储能 {pv_to_storage}  光伏给 {pv_to_sub}  光伏给放弃 {pv_to_curtailed}  ")
        params['info'] = params['info'] + info
    else:
        pv_to_storage = aux_storage * (pv / aux_total)
        pv_to_sub = subAux * (pv / aux_total)
        pv_to_pv = pvAuxDemand * (pv / aux_total)
        pv_to_curtailed = 0 # 光伏不足覆盖，

        info = (F" 非充电计划时（Standby）光伏与辅助功率分配,  光伏是不足覆盖所有辅助，光伏 {pv}  光伏给自己 {pv_to_pv}  光伏给储能 {pv_to_storage}  光伏给 {pv_to_sub}  光伏给放弃 {pv_to_curtailed}  ")
        params['info'] = params['info'] + info

        bat_to_storage = bat_to_sub = bat_to_pv = 0
        grid_to_storage = aux_storage - pv_to_storage
        grid_to_sub = subAux - pv_to_sub
        grid_to_pv = pvAuxDemand - pv_to_pv
        grid_power = aux_total - pv
        pv2grid = 0


    storage2grid = 0
    Pin_ac = Pdis_ac = Pin_dc = Pdis_dc = 0

    result = {
        "state": state,
        "pv_to_storage": pv_to_storage,
        "aux_storage": aux_storage,
        "pv_to_sub": pv_to_sub,
        "pv_to_pv": pv_to_pv,
        "pv_to_curtailed": pv_to_curtailed,  # 新增 光伏弃用
        "bat_to_storage": bat_to_storage,
        "bat_to_sub": bat_to_sub,
        "bat_to_pv": bat_to_pv,
        "grid_to_storage": grid_to_storage,
        "grid_to_sub": grid_to_sub,
        "grid_to_pv": grid_to_pv,
        "grid_power": grid_power,
        "pv2grid": pv2grid,
        "storage2grid": storage2grid,
        "Pin_ac": Pin_ac,
        "Pdis_ac": Pdis_ac,
        "Pin_dc": Pin_dc,
        "Pdis_dc": Pdis_dc
    }
    return result
