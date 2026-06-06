from data_processors.process_aux_power import get_aux_power
from data_processors.process_daily_charge_plan import get_ComputeDailyChargePlan

def charge_pv_positive_with_soc_plan(pv=None,
                                     soc=None,
                                     capacity=None,
                                     temp=None,
                                     eta_ch=None,
                                     subAux=None,
                                     pvAuxDemand=None,
                                     maxPower=None,
                                     T_POINTS=None, OP_POINTS=None, IDLE_POINTS=None,params=None):


    """
    决定非放电时间段是否充电（基于 chargePlan 和光伏正出力）
    - 所有参数默认 None
    - 严格按照 VBA 顺序和字段顺序实现
    """
    # 判断是否需要充电
    aux_storage = get_aux_power(temp,'op',T_POINTS, OP_POINTS, IDLE_POINTS)
    aux_total = aux_storage + subAux + pvAuxDemand
    remCap = capacity - soc
    maxPin = min(maxPower, remCap / eta_ch)

    if pv >= aux_total:
        # 光伏充足
        Pin_ac = max(0, min(pv - aux_total, maxPin))  # 保证非负
        if Pin_ac > 0:
            # 充电成功
            state = "Charging"

            #  充电时， 新增，更改， 就按照55度 暂时不用
            # aux_storage = get_aux_power(temp, 'op', T_POINTS, OP_POINTS, IDLE_POINTS,charge=False)
            # aux_total = aux_storage + subAux + pvAuxDemand

            pv_to_storage = aux_storage
            pv_to_sub = subAux
            # ' 光伏给光伏辅助（pvAuxDemand 由光伏自身提供）
            pv_to_pv = pvAuxDemand

            bat_to_storage = bat_to_sub = bat_to_pv = 0
            grid_to_storage = grid_to_sub = grid_to_pv = 0
            grid_power = 0
            soc = soc + Pin_ac * eta_ch

            # if soc > params['capacity']:
            #     print(params['info_t'], '充电后：',soc , '充入的：',Pin_ac, eta_ch, ' 当年的容量 ：',params['capacity']) # 这个只是在2016年出现，但是单独跑数据，没有出现
            # soc = min(soc + Pin_ac * eta_ch, params['capacity']) # 和最大值进行对比

            pv2grid = pv - aux_total - Pin_ac

            pv_to_curtailed = pv- pv_to_storage - pv_to_sub - pv_to_pv - Pin_ac
            info = F" pv >= aux_total,   充电成功  光伏 {pv}  光伏给自己 {pv_to_pv}  光伏给储能 {pv_to_storage}  光伏给 {pv_to_sub}  光伏给放弃 {pv_to_curtailed}  "
            params['info'] = params['info'] + info


            storage2grid = 0
            Pin_dc = Pin_ac * eta_ch
            Pdis_ac = Pdis_dc = 0
        else:
            # ' 虽然光伏充足，但受限于功率或剩余容量，无法充电，视为空闲
            state = "Standby"
            pv_to_storage = aux_storage
            pv_to_sub = subAux
            pv_to_pv = pvAuxDemand

            bat_to_storage = bat_to_sub = bat_to_pv = 0
            grid_to_storage = grid_to_sub = grid_to_pv = 0
            grid_power = 0
            pv2grid = pv - aux_total

            pv_to_curtailed = pv - pv_to_storage - pv_to_sub - pv_to_pv  # 新增
            info = F" pv >= aux_total,   虽然光伏充足，但受限于功率或剩余容量，无法充电，视为空闲Standby   光伏 {pv}  光伏给自己 {pv_to_pv}  光伏给储能 {pv_to_storage}  光伏给 {pv_to_sub}  光伏给放弃 {pv_to_curtailed}  "
            params['info'] = params['info'] + info

            Pin_ac = Pin_dc = 0
            # storage2grid = 0 # vba没有这个
    else:
        # 光伏不足以覆盖辅助 无法充电，空闲
        # print('#  3 光伏不足以覆盖辅助 无法充电，空闲')
        state = "Standby"
        ratio = pv / aux_total if aux_total else 0
        pv_to_storage = aux_storage * ratio
        pv_to_sub = subAux * ratio
        pv_to_pv = pvAuxDemand * ratio


        bat_to_storage = bat_to_sub = bat_to_pv = 0
        grid_to_storage = aux_storage - pv_to_storage
        grid_to_sub = subAux - pv_to_sub
        grid_to_pv = pvAuxDemand - pv_to_pv
        grid_power = aux_total - pv
        pv2grid = 0

        pv_to_curtailed = pv - pv_to_storage - pv_to_sub - pv_to_pv  # 新增
        info = F" pv < aux_total,   光伏不足以覆盖辅助，视为空闲Standby   光伏 {pv}  光伏给自己 {pv_to_pv}  光伏给储能 {pv_to_storage}  光伏给 {pv_to_sub}  光伏给放弃 {pv_to_curtailed}  "
        params['info'] = params['info'] + info

        Pin_ac = Pin_dc = 0
        storage2grid = 0
    result = {
        "state": state,
        "soc": soc,
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