da📁 文件夹:
    - run_all_data.py  程序总的入口，直接执行这个代码，
    - run_year.py.    对每一年的数据进行处理和保存
    - get_charge.py   充电时间内 》 充电过程的处理，根据不同条件，选择如下不同逻辑计算
        - get_charge_pvLess0.py                          充电时间 》 光伏 <= 0
        - get_charge_pvMore0_socMoreCapacity.py          充电时间 》 光伏 > 0 , 储能已经充满
        - get_charge_pvMore0_socLessCapacity_notplan.py  充电时间 》 光伏 > 0 , 储能未充满， 不充电计划中
        - get_charge_pvMore0_socLessCapacity_plan.py     充电时间 》 光伏 > 0 , 储能未充满， 在充电计划中
    - get_discharge.py   放电时间内 》放电过程的处理
    - 字段说明.xls  是把一些用到的字段梳理到表格 
    - 所有参数.txt  读取参数过程中，保存的所有参数和值
    - 所有字段说明.txt 已经 复制到本readme.md文件中了。

📁 文件夹: data_calculators   对一些结果的计算方法
    - calculate_GWh.py    统计功率总和值，

📁 文件夹: data_outputs   数据输出保存格式处理
    - output_excel_config.py     excel 宽度、颜色的处理
    - output_pv_save.py          数据结果的保存 按照需要的字段进行排序，

📁 文件夹: data_processors
    - process.py                      一些处理过程中需要的计算
    - process_aux_power.py           根据温度，计算功率的波动变化
    - process_daily_charge_plan.py   计算当天的充电计划（根据容量充满的小时）

📁 文件夹: data_readers   读取数据的处理过程
    - read_input_params.py   读取基本的输入参数，如一些表格中提供的参数，效率等信息，可以更改里面的文件
    - read_pv_data.py        读取光伏数据，被 run_year调用，
    - read_update_params.py  对每年的参数进行更新，更新容量、效率等

📁 文件夹: utils
    - utils_excel.py    excel相关的处理，如查找字段，信息
    - utils_file.py     一些文件的处理，如文件的创建、字典的保存等。

## 🔹 字段说明
| 原始名称 | 中文描述 | 英文/统一名称 |
|---|---|---|
| soc / capacity | SOC / 容量 | SOC/% |
| aux_storage | 储能辅助设备（冷却、BMS等）消耗的功率 | BESS Auxiliary Power [MW] |
| subAux | 子系统辅助功率（原描述未给，可自定义） | Common Infrastructure Aux Power[MW] |
| pv2grid | 光伏发电直接输送到电网的功率 | PV Power To Plant Substation BCP [MW] |
| storage2grid | 储能电池放电送到电网的功率 | BESS Power To Plant Substation BCP [MW] |
| state | 当前小时的运行状态（如充电、放电、待机） | Mode |
| Pin_ac | 中压侧（交流并网点）的充电功率（从电网取电） | PV Power to BESS Plant BCP [MW] |
| Pdis_ac | 中压侧（交流并网点）的放电功率（向电网馈电） | DisCharge Power BCP [MW] |
| pv_to_storage | 光伏发电存入储能电池的功率 | PV Power To BESS plant aux consumuer [MW] |
| pv_to_sub | 光伏供给用户侧（变电站/负荷）的功率 | PV Power To Common Infrastructure Power [MW] |
| Pin_dc | 直流侧（电池侧）的充电功率 | Charge Power [DC] |
| Pdis_dc | 直流侧（电池侧）的放电功率 | Discharge Power [DC] |
| bat_to_storage | 电池对储能系统的功率（可能为冗余变量） | BESS Power To BESS plant aux consumuer [MW] |
| bat_to_sub | 电池放电给负荷/变电站的功率 | BESS plant Power To Common Infrastructure Power [MW] |
| grid_power | 并网点最终交换的净功率（正负表示流向） | Imported Power [MW] |
| bat_to_pv | 电池放电给光伏侧（直流耦合系统反向） | BESS Power To PV Plant [MW] |
| soc | SOC（当前状态，可区别 soc/capacity） | Energy [DC] |
| hv_power | 高压侧功率（若存在升压变压器） | Exported Power [MW] |
| T_POINTS | 温度列 | Temperature℃ |
| OP_POINTS | 储能系统正常工作时的辅助功率消耗 | Aux power operation MW |
| IDLE_POINTS | 储能系统空闲待机时的辅助功率消耗 | Aux power idle MW |
| DC Cable Efficiency [%] | 直流电缆效率 - 99.9% |  |
| PCS Efficiency [%] | 电力转换系统效率 - 98.7% |  |
| LV Cable Efficiency [%] | 低压交流电缆效率 - 99.8% |  |
| MV Transformer Efficiency [%] | 中压变压器效率 - 99.2% |  |
| MV Cable Efficiency [%] | 中压交流电缆效率 - 99.8% |  |
| Battery Efficiency [%] | 电池效率 - 95.68% |  |
| MV/HV Transformer Efficiency[%] | 中压/高压变压器效率-99.50% |  |
| HV Losses up to DP[%] | 高压至配电点损耗率-99.5% |  |
| hour_charge | 充电时间 |  |
| hour_discharge | 放电时间段 判断是否为放电时段（19:00-01:00） |  |
| eta_ch | 充电效率 变动的 0.9325 |  |
| eta_dis | 放电效率 0.9747 |  |
| target_hv_power | 高压侧目标放电功率 MW 260 |  |
| eta_trafo | 高压变压器效率 0.995 |  |
| eta_cable | 高压电缆效率 0.99 |  |
| capacity | 储能容量 MW 是每年都在变化 - 1687 | DC Functional Capacity[MWh] |
| maxPower | 最大充放电功率 MW - 338 | PCS Capacity (MVA) |
| subAux | 储能厂及光伏子站辅助负荷（MW） | ESF and IPP Substation Consumption [Mwac]: |
| grid_to_storage | 从电网取电给电池充电的功率 |  |
| grid_to_sub | 电网直接供给负荷/变电站的功率 |  |
| grid_to_pv | 电网向光伏侧送电（维持逆变器等） |  |
| aux_total | 系统总辅助功耗 |  |
