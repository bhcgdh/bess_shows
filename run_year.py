import json
import os
import os.path
from lib2to3.btm_utils import reduce_tree
import numpy as np
import time
from get_discharge import discharge
from get_charge import charge
# 从文件data_readers 下面的读取数据方法 get_data_pv_phaseA 获取 get_data_pv_phaseA 代码
from data_processors.process import get_data_ifcharge_hour, get_data_pv_rate,get_data_pv_to_curtailed
from data_processors.process_daily_charge_plan import get_ComputeDailyChargePlan

from data_readers.read_pv_data import get_data_pv_phaseA # 读取数据
from data_outputs.output_pv_save import save_data_phaseA # 保存结果
from  data_calculators.calculate_GWh import cal_pv_GWh  # 计算光伏的总计的容量 phaseC

def run_data_year(input_folder,output_folder,file_name,params,
                  T_POINTS_charge,OP_POINTS_charge,IDLE_POINTS_charge,
                  T_POINTS_discharge,OP_POINTS_discharge,IDLE_POINTS_discharge,
                  hour_charge,hour_discharge,
                  init_param,
                  save_year_output=True,
                  ):
    """
    :param input_folder:  文件所在的路径
    :param output_folder:  文件保存在的路径
    :param file_name:  文件名称
    :param params: 输入参数
    :param init_param: 初始值
    :return:
    """

    file_path = os.path.join(input_folder, file_name)    # 文件所在的位置 全路径
    output_path = os.path.join(output_folder, file_name) # 重新保存的文件 全路径

    # 1 光伏的负荷和时间数据， 光伏 pv, 温度temp,
    dfv = get_data_pv_phaseA(file_path) # 获取光伏数据 》 根据日扩充到1小时，缺失的使用0填充，


    # 2 增加 "ifcharge" ,根据时间判断 值为charge是充电，discharge 放电
    dfv = get_data_ifcharge_hour(dfv, hour_charge=hour_charge , hour_discharge=hour_discharge)

    # dfv = dfv.head(24*3)

    # 光伏效率优化计算 正数 * 效率，非正保留原值
    dfv.loc[dfv['pv']>0,'pv'] = dfv.loc[dfv['pv']>0,'pv']  * params['pv_rate']

    dfv['needNewPlan'] = False
    dfv.loc[dfv.hour.isin([0, 1, 2]), 'needNewPlan'] = True

    # 4 增加 pvAuxDemand 光伏夜间辅助需求（光伏负值表示消耗）， 保留负数，正的为0
    dfv['pvAuxDemand'] = [np.maximum(-i, 0) for i in dfv['pv']]

    # 开始遍历数据 光伏，温度，日，小时，是否计划当天，pv负数的abs,是否充放小时内，
    # 初始化空字典，每个字段对应一个 listread
    all_vals = {
        'soc|capacity': [],
        'aux_storage': [],
        'subAux': [],
        'pv2grid': [],
        'storage2grid': [],
        'state': [],
        'Pin_ac': [],
        'Pdis_ac': [],
        'pv_to_storage': [],
        'pv_to_sub': [],
        'Pin_dc': [],
        'Pdis_dc': [],
        'bat_to_storage': [],
        'bat_to_sub': [],
        'grid_power': [],
        'bat_to_pv': [],
        'soc': [],
        'hv_power': [],
        'pv_to_curtailed': [], # 新增一行
    }

    result = init_param.copy()
    prev_day = None
    needNewPlan = True # 每天2点计算当天的计划
    chargePlan = None

    dayPV = None
    col = [ 't', 'pv', 'temp', 'day', 'hour','needNewPlan','pvAuxDemand','ifcharge']
    for ids, val in enumerate(dfv[col].values):
        soc = result['soc']
        t, pv, temp, day, hour, needNewPlan, pvAuxDemand, ifcharge = val

        # 这，减少计算时间和次数，之前每个小时都进行计算
        if prev_day is None or day != prev_day:
            needNewPlan = True
            prev_day = day
            dayPV = dfv[dfv['day'] == day][['t', 'pv', 'temp', 'hour']].reset_index(drop=True)


        # 历史计算 soc need： 一天的soc 最多充入的量，soc max 4月24之前：使用当天充满（需要计算第二天第一个小时的数据）
        # capacity_need = dfv_need[dfv_need['day'] == day]['soc_need_cap'] # 一天的需要的电量
        # params['capacity_need'] = capacity_need.values[0] #

        #  新增更改- 4月24  使用储能的容量 数据
        #  PhaseA：1690；PhaseB：3656；PhaseC：3656
        params['capacity_need'] = min( params['capacity'], params['phase_soc_max'])

        params['mark_day'] = str(day)[0:10]
        params['mark_day_time'] = str(t)


        # params['info'] = f'\n {t} 光伏 {pv} 充放电模式 {ifcharge}，今天需要的电量 晚上19到第二天0点 {capacity_need}, '
        params['info_t'] = str(t)[0:18]


        # print(f"{t} {ifcharge}")
        if ifcharge =='discharge':
            T_POINTS = T_POINTS_discharge
            OP_POINTS = OP_POINTS_discharge
            IDLE_POINTS = IDLE_POINTS_discharge
            result_new = discharge(
                temp=temp,
                pv=pv,
                soc=soc,
                pvAuxDemand=pvAuxDemand,
                eta_dis=params['eta_dis'],
                eta_trafo=params["eta_trafo"],
                eta_cable=params["eta_cable"],
                target_hv_power=params['target_hv_power'],
                maxPower=params['maxPower'],
                eta_ch=params['eta_ch'],
                subAux=params['subAux'],
                T_POINTS=T_POINTS,
                OP_POINTS=OP_POINTS,
                IDLE_POINTS=IDLE_POINTS,
                params = params
            )
        else:
            # capacity = params['capacity'] 之前设置的
            capacity = params['capacity_need']
            T_POINTS = T_POINTS_charge
            OP_POINTS = OP_POINTS_charge
            IDLE_POINTS = IDLE_POINTS_charge

            # 如果要重新进行用电计划，则重新进行计算 一个是要过0点，2点之后，才会生成新的计划，
            if needNewPlan and hour >= 2:
                # 是一个充放电计划的plan , 24 个点，判断是否进行充放

                chargePlan = get_ComputeDailyChargePlan(df_day=dayPV,
                                                        start_soc=soc,
                                                        capacity=capacity, maxPower=params['maxPower'],
                                                        eta_ch=params['eta_ch'], subaux=params['subAux'],
                                                        T_POINTS=T_POINTS,OP_POINTS=OP_POINTS, IDLE_POINTS=IDLE_POINTS,
                                                        )
                needNewPlan = False
            result_new = charge(
                currHour=hour,
                needNewPlan=needNewPlan,
                chargePlan=chargePlan,
                dayPV=dayPV,
                soc=soc,
                pv=pv,
                temp=temp,
                pvAuxDemand=pvAuxDemand,
                capacity=capacity,
                maxPower=params['maxPower'],
                eta_ch=params['eta_ch'],
                subAux=params['subAux'],
                T_POINTS=T_POINTS,
                OP_POINTS=OP_POINTS,
                IDLE_POINTS=IDLE_POINTS,
                params=params
            )
        result.update(result_new)
        hv_power = (result['pv2grid'] + result['storage2grid']) * params['eta_trafo'] * params['eta_cable']
        val= params['info']

        # 保存到 json --- 暂时不保存 
        # with open("params.json", "w", encoding="utf-8") as f:
        #     json.dump(params, f, ensure_ascii=False, indent=2)

        if hv_power < 0:
            hv_power = 0
        result['hv_power'] = hv_power

        # if params['mark_day'] in ["1990-04-25", '1990-04-26'] and params['mark_year'] == 2:
        #     print(f" 开始 {t},进行保存的 result['soc']  ",result['soc'])
        result['soc|capacity'] = (result['soc'] / params['capacity'])
        # check_result_keys(result, hour=t)
        all_vals['soc|capacity'].append(result['soc'] / params['capacity'])  # soc%占比
        all_vals['aux_storage'].append(result['aux_storage'])   # 储能辅助设备（冷却、BMS等）消耗的功率 - BESS Auxiliary Power [MW]
        all_vals['subAux'].append(result['subAux'])  # 变电站辅助功率常数 -  "Common Infrastructure Aux Power[MW]"
        all_vals['pv2grid'].append(result['pv2grid']) # 光伏发电直接输送到电网的功率 - PV Power To Plant Substation BCP [MW]"
        all_vals['storage2grid'].append(result['storage2grid']) # 储能电池放电送到电网的功率 - BESS Power To Plant Substation BCP [MW]"
        all_vals['state'].append(result['state'])    # 充放电状态，三个值，静止，充电，放电  - "Mode"
        all_vals['Pin_ac'].append(result['Pin_ac'])  # 中压侧（交流并网点）的充电功率（从电网取电）  - - "PV Power to BESS Plant BCP  [MW]"
        all_vals['Pdis_ac'].append(result['Pdis_ac'])  # 中压侧（交流并网点）的放电功率（向电网馈电） - - "DisCharge Power BCP [MW]"
        all_vals['pv_to_storage'].append(result['pv_to_storage'])  # 光伏发电存入储能电池的功率 - - "PV Power To BESS plant aux consumuer [MW]"
        all_vals['pv_to_sub'].append(result['pv_to_sub'])  # 光伏供给用户侧（变电站/负荷）的功率 - - "PV Power To Common Infrastructure Power [MW] "
        all_vals['Pin_dc'].append(result['Pin_dc'])  # 直流侧（电池侧）的充电功率 - - "Charge Power [DC]"
        all_vals['Pdis_dc'].append(result['Pdis_dc'])  # 直流侧（电池侧）的放电功率 - - "Discharge Power [DC]"
        all_vals['bat_to_storage'].append(result['bat_to_storage'])  # 电池对储能系统的功率（可能为冗余变量） - - "BESS Power To BESS plant aux consumuer [MW]"
        all_vals['bat_to_sub'].append(result['bat_to_sub'])  # 电池放电给负荷/变电站的功率 - - "BESS plant Power To Common Infrastructure Power [MW]"
        all_vals['grid_power'].append(result['grid_power'])  # 并网点最终交换的净功率（正负表示流向） - - "Imported Power [MW]"
        all_vals['bat_to_pv'].append(result['bat_to_pv'])  # 电池放电给光伏侧（直流耦合系统反向） - - "BESS Power To PV Plant [MW]"
        all_vals['soc'].append(result['soc'])  # - - "Energy [DC]"
        all_vals['hv_power'].append(result['hv_power'])  # 高压侧功率（若存在升压变压器） - - "Exported Power [MW]"
        # 新增一列  光伏弃光量
        all_vals['pv_to_curtailed'].append(result['pv_to_curtailed'])  #  光伏提供所有后，剩下的

    # 更新数据，字典结果，保存到dataframe表格中，
    for k,v in all_vals.items():
        dfv[k] = v

    # 光伏弃用光伏的量
    dfv = get_data_pv_to_curtailed(dfv,params)

    # print("dfv['pv2grid'].min()   ",dfv['pv2grid'].min())


    # 统计 phaseC值 一年总共的发电值等
    dfv_gwh = cal_pv_GWh(dfv, params) # 统计phaseC值

    # 数据保存到指定文件夹中，名字改为指定的命名方式 （ 保存后，更改表头格式，新增了容量的计算列 ）
    if save_year_output:
        save_data_phaseA(
            df=dfv,
            sheet_name_df='Sheet1',
            df_gwh=dfv_gwh,
            sheet_name_df_gwh='Sheet1',
            output_path=output_path,
            params=params
        )

    # 每次结果进行保存
    # append_year_df_to_output_workbook(
    #     df=df_new,
    #     output_file=params['finally_folder'],
    #     year_index=params['mark_year'],
    #     sheet_prefix="Y",
    #     params=params,
    #     save_each_time=True,
    # )


    # print("保存到 ", output_path)
    last_soc = dfv['soc'].values[-1]
    print('最后的soc',last_soc)
    return last_soc, dfv.copy()
