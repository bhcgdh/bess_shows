from data_processors.process_aux_power import get_aux_power

def charge_pv_positive_with_soc_full(pv=None,soc=None,capacity=None,temp=None,subAux=None,
                                     pvAuxDemand=None,
                                     T_POINTS=None, OP_POINTS=None, IDLE_POINTS=None,params=None):
    """
    光伏有正出力，储能已满时的功率分配逻辑（空闲状态 Standby）：
    - 如果光伏大于辅助总功率，光伏剩余上网
    - 否则，不足部分由电网提供
    - 储能不充电，所有储能相关功率为0
    返回字典：
        state: 状态
        pv_to_storage, pv_to_sub, pv_to_pv: 光伏分配到储能/变电站/负荷
        bat_to_storage, bat_to_sub, bat_to_pv: 储能输出功率，已满为0
        grid_to_storage, grid_to_sub, grid_to_pv: 电网补充功率
        grid_power: 电网总功率
        pv2grid: 光伏上网功率
        storage2grid: 储能上网功率，已满为0
        Pin_ac, Pdis_ac, Pin_dc, Pdis_dc: AC/DC充放电功率，已满为0
    """
    # 状态为空闲 储能已满，不充电，空闲
    state = "Standby"

    # 获取当前小时辅助功率（idle 状态）
    # print(f" charge_pv_positive_with_soc_full ", 'idle')
    aux_storage = get_aux_power(temp,'idle',T_POINTS, OP_POINTS, IDLE_POINTS,charge=True)
    aux_total = aux_storage + subAux + pvAuxDemand

    # 光伏足够覆盖辅助
    if pv >= aux_total:
        pv_to_storage = aux_storage #
        pv_to_sub = subAux
        pv_to_pv = pvAuxDemand

        bat_to_storage = bat_to_sub = bat_to_pv = 0
        grid_to_storage = grid_to_sub = grid_to_pv = 0
        grid_power = 0
        pv2grid = pv - aux_total

        pv_to_curtailed = pv - pv_to_storage - pv_to_sub - pv_to_pv  # 新增
        info = (
            F" 光伏有正出力，储能已满时,  光伏足够覆盖辅助，光伏 {pv}  光伏给自己 {pv_to_pv}  光伏给储能 {pv_to_storage}  光伏给 {pv_to_sub}  光伏给放弃 {pv_to_curtailed}  ")
        params['info'] = params['info'] + info

    else:
        # 光伏不足，由电网补充
        ratio = pv / aux_total if aux_total else 0
        pv_to_storage = aux_storage * ratio
        pv_to_sub = subAux * ratio
        pv_to_pv = pvAuxDemand * ratio

        pv_to_curtailed = 0
        info = (
            F" 充电时间，储能满的，光伏不足，由电网补充，光伏 {pv}  光伏给自己 {pv_to_pv}  光伏给储能 {pv_to_storage}  光伏给 {pv_to_sub}  光伏给放弃 {pv_to_curtailed}  ")
        params['info'] = params['info'] + info


        bat_to_storage = bat_to_sub = bat_to_pv = 0

        grid_to_storage = aux_storage - pv_to_storage
        grid_to_sub = subAux - pv_to_sub
        grid_to_pv = pvAuxDemand - pv_to_pv
        grid_power = aux_total - pv
        pv2grid = 0

    Pin_ac = Pdis_ac = Pin_dc = Pdis_dc = 0
    storage2grid = 0
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
