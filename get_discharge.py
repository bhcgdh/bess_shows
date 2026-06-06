from data_processors.process_aux_power import get_aux_power

# 放电时间段的处理
def discharge(temp=None,pv=None,soc=None,pvAuxDemand=None,

                            eta_dis=None,eta_trafo=None,eta_cable=None,
                            target_hv_power=None,maxPower=None,eta_ch=None,subAux=None,
                            T_POINTS=None,OP_POINTS=None,IDLE_POINTS=None,params=None
                            ):

    # 目标中压功率 = 高压侧目标放电功率 (MW)/(高压变压器效率 * 高压电缆效率 )
    target_grid_ac = target_hv_power / (eta_trafo * eta_cable)

    # 总辅助功率  不同温度下的 运行和静止时候的功率
    # print(f" discharge ", 'op')
    aux_storage = get_aux_power(temp, "op", T_POINTS, OP_POINTS, IDLE_POINTS)

    # pvAuxDemand 是小于0的数据，获取abs值
    aux_total = aux_storage + subAux + pvAuxDemand

    # 所需放电功率 = 目标中压功率 + 不同温度下 运行时消耗的功率 + 变电站辅助功率常数（单位：MW）+ 小于0的数据
    required_discharge = target_grid_ac + aux_total

    info = f"这个小时，需要放电量：{required_discharge}"
    params['info'] = params['info'] + info


    # 电池放电能力受限 min(需要放电功率，min( 储能最大充放电功率（单位：MW）,soc * 放电效率)）
    max_discharge_ac = min(maxPower, soc * eta_dis)
    Pdis_ac = min(required_discharge, max_discharge_ac)
    ts = params['mark_day_time']
    info1 = f"时间{ts}, 正在放电计算 ，目标中压功率 {target_grid_ac},  需要的电量{required_discharge},进行对比的电量 最小的 Pdic_ac：，[{maxPower}, {soc * eta_dis},  {required_discharge}]"
    info2 = ''
    info3 = ''

    #
    # print( f"最多可以放的电量 ,max_discharge_ac {max_discharge_ac}, "
    #        f"maxPower {maxPower},"
    #        f" required_discharge  {required_discharge},"
    #        f" target_grid_ac  {target_grid_ac},"
    #        f" Pdis_ac  {Pdis_ac} ,"
    #        f" aux_total {aux_total}, 最终的 {Pdis_ac - aux_total},")

    if Pdis_ac >= aux_total:
        # print('正常放电 ',Pdis_ac , aux_total)
        # 正常放电
        state = "Discharge"
        bat_to_storage = aux_storage  # 不同温度下的 运行和静止时候的功率  电池对储能系统的功率
        bat_to_sub = subAux           # 电池放电给负荷/变电站的功率
        bat_to_pv = pvAuxDemand      # 光伏负数的abs，其他为0 ，电池放电给光伏侧
        pv_to_storage = 0
        pv_to_sub = 0
        pv_to_curtailed = 0    # 放电时间段，光伏不进行放电，没有电量，
        grid_to_storage = 0
        grid_to_sub = 0  # 电网直接供给负荷/变电站的功率
        grid_to_pv = 0   # 电网向光伏侧送电
        grid_power = 0
        # 更新SOC
        soc_new = soc - Pdis_ac / eta_dis
        storage2grid = Pdis_ac - aux_total
        pv2grid = max(0, pv)
        Pin_ac = 0
        Pin_dc = 0
        Pdis_dc = Pdis_ac / eta_dis
        info2 = f" 现在 Discharge 放电充足，温度辅助{aux_storage}， soc 更新为 {soc_new}, 储能电池放电{storage2grid} , 直流放电功率{Pdis_dc}"


    else:
        # 放电不足，转为Standby
        # print('放电不足 ',  Pdis_ac , aux_total)
        state = "Standby"
        aux_storage = get_aux_power(temp,'idle',T_POINTS, OP_POINTS, IDLE_POINTS)
        aux_total = aux_storage + subAux + pvAuxDemand
        bat_to_storage = 0
        bat_to_sub = 0
        bat_to_pv = 0
        pv_to_storage = 0
        pv_to_sub = 0
        pv_to_curtailed = 0    # 放电时间段，光伏不进行放电，没有电量，
        grid_to_storage = aux_storage
        grid_to_sub = subAux
        grid_to_pv = pvAuxDemand
        grid_power = aux_total
        Pdis_ac = 0
        storage2grid = 0
        pv2grid = max(0, pv)
        Pin_ac = 0
        Pin_dc = 0
        Pdis_dc = 0
        soc_new = soc
        info3 = f" 现在 Standby 放电不足 ，soc没有变化 温度辅助{aux_storage}， soc 更新为 {soc_new}, 储能电池放电{storage2grid} , 直流放电功率{Pdis_dc}"
    # if params['mark_day'] in ["1990-04-25", '1990-04-26'] and params['mark_year']==2:
    #     print(info1)
    #     print(info2)
    #     print(info3)
    #     print("  \n ")

    result =  {
        "state": state,
        "soc": soc_new,
        "Pdis_ac": Pdis_ac,
        "Pdis_dc": Pdis_dc,
        "aux_storage": aux_storage,
        "aux_total": aux_total,
        "bat_to_storage": bat_to_storage,
        "bat_to_sub": bat_to_sub,
        "bat_to_pv": bat_to_pv,
        "pv_to_storage": pv_to_storage,
        "pv_to_sub": pv_to_sub,
        "pv_to_curtailed" : pv_to_curtailed,  # 新增 放电时间段，光伏不进行放电，没有电量，
        "grid_to_storage": grid_to_storage,
        "grid_to_sub": grid_to_sub,
        "grid_to_pv": grid_to_pv,
        "grid_power": grid_power,
        "storage2grid": storage2grid,
        "pv2grid": pv2grid,
        "Pin_ac": Pin_ac,
        "Pin_dc": Pin_dc
    }
    return result