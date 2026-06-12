def cal_standardize_columns(df, params=None):
    output_columns = cal_ouput_columns()
    ds = pd.DataFrame(index=df.index, columns=output_columns)

    # Excel列 A 1 时间列
    ds[('Time', 'Time Step')] = df.index

    time_values = pd.to_datetime(df['Time'], format='%H:%M:%S')
    date_values = pd.to_datetime(df['Date'])

    # Excel列 B
    ds[('Time', 'Hour')] = time_values.dt.hour
    # Excel列 C
    ds[('Time', 'Day')] = date_values.dt.day
    # Excel列 D
    ds[('Time', 'Month')] = date_values.dt.month

    # Excel列 E PV列
    ds[('PV', 'AC MV Power Available')] = df['E_out']  # E
    # Excel列 F 新增 - E-G-R, E 是负数则为0
    ds[('PV', 'AC MV Surplus')] = 0  # 光伏盈余 看 F

    # Excel列 G | 字段: pv_to_sub
    ds[('PV', 'AC MV Power to Infra')] = df['PV Power To Common Infrastructure Power [MW]']  # G

    # Excel列 H | 字段: pv_to_storage 新增 Excel列 H | 字段: pv_to_storage 充电时 H = K + R
    ds[('PV', 'AC MV Power to BESS')] = df['PV Power To BESS plant aux consumuer [MW]']  # H

    # Excel列 I | 字段: pv2grid  新增2 列的值不能<0,他不从电网取电
    ds[('PV', 'AC MV Power to HV')] = df['PV Power To Plant Substation BCP [MW]']  # I

    # Excel列 J J | 字段: pv2grid - 660   df['PV Power To Plant Substation BCP [MW]'] * params["eta_trafo"] * params['eta_cable'] # 来自光伏 AD
    ds[('PV', 'AC MV Power Dumped')] = df['PV Power To Plant Substation BCP [MW]'] * params["eta_trafo"] * params[
        'eta_cable'] - params["pv_max_Discharge_cap"]  # 比660大的正的为结果值对把
    # Excel列 J
    ds[('PV', 'AC MV Power Dumped')] = ds[('PV', 'AC MV Power Dumped')].clip(lower=0)  # 比660大的正的为结果值对把

    # Excel列 K BESS列 | 字段: Pin_ac  新增 -
    ds[('BESS', 'AC MV Power Charge')] = df['PV Power to BESS Plant BCP [MW]']  # 储能交流侧充电功率 K
    #  = pin_ac/( 8 * 6个效率 ) , eta_ch 是6个效率乘积  更改2 , 设置定值
    # ds[('BESS', 'AC MV Power Charge')] = df['PV Power to BESS Plant BCP [MW]']/(8*params['eta_ch'])  # 储能交流侧充电功率 K
    # ds[('BESS', 'AC MV Power Charge')] = 340

    # Excel列 L | 字段: Pdis_ac
    ds[('BESS', 'AC MV Power Discharge')] = df['DisCharge Power BCP [MW]']  # 储能交流侧放电功率 L
    # 更改2  = 高压侧目标放电功率 (MW)/(高压变压器效率 * 高压电缆效率 ) + 光伏 + infra 这里infra 是 PV Power To Common Infrastructure Power [MW]'
    ds[('BESS', 'AC MV Power Discharge')] = params["target_hv_power"] / (params['eta_trafo'] * params['eta_cable']) + \
                                            ds[('PV', 'AC MV Power Available')] + ds[('PV', 'AC MV Power to Infra')]

    # Excel列 M | 字段: Pin_dc
    # ds[('BESS', 'DC Power Charge')] = df['Charge Power [DC]']  # 储能直流侧充电功率 M
    # 更改2  = k * eta_ch 充电效率
    ds[('BESS', 'DC Power Charge')] = ds[('BESS', 'AC MV Power Charge')] * params['eta_ch']

    # Excel列 N | 字段: Pdis_dc
    ds[('BESS', 'DC Power Discharge')] = df['Discharge Power [DC]']  # 储能直流侧放电功率 N

    # Excel列 O | 字段: soc
    ds[('BESS', 'DC Energy')] = df['Energy [DC]']  # 储能直流侧能量  O
    # Excel列 P | 字段: soc / capacity
    ds[('BESS', 'SOC')] = df['SOC/%']  # 储能荷电状态 P

    # 映射 Mode，0：standby，1：charge，2：discharge
    mode_reverse_map = {'Standby': '0', 'Charging': '1', 'Discharge': '2'}

    # Excel列 Q
    ds[('BESS', 'Mode')] = df['Mode'].map(mode_reverse_map)  # 储能运行模式

    # Excel列 R 新增2 储能放电时 需要储能 提供的 - 未增  R | 字段: aux_storage，更改2 ，在原始计算中，区分充电8h，放电6的功率选择
    ds[('BESS', 'AC LV Aux Power')] = df['BESS Auxiliary Power [MW]']  # 储能辅助设备消耗功率

    # # Excel列 H | 字段: pv_to_storage 新增 Excel列 H | 字段: pv_to_storage 充电时 H = K + R
    # ds[('PV', 'AC MV Power to BESS')] = df['PV Power To BESS plant aux consumuer [MW]'] # H
    #
    #
    # # Excel列 H | 字段: pv_to_storage 新增 Excel列 H | 字段: pv_to_storage 充电时 H = K + R
    # ds[('BESS','_mask')] = ds[('BESS', 'AC MV Power Charge')] + ds[ ('BESS', 'AC LV Aux Power')]
    # mask = ds[ds[('BESS', 'Mode')] == '1'].index
    # ds[('PV', 'AC MV Power to BESS')] = [ds[('BESS','_mask')][i] if i in mask else ds[('PV', 'AC MV Power to BESS')][i]  for i in ds.index ]
    # del ds[('BESS','_mask')]

    # # Excel列 H  更改2 = k + R/(mvcab * mvtr 效率) AC MV Power to BESS
    ds[('PV', 'AC MV Power to BESS')] = ds[('BESS', 'AC MV Power Charge')] + ds[('BESS', 'AC LV Aux Power')] / (
                params['eta_trafo'] * params['eta_cable'])

    #  ======================== 更新  Excel列 F ---- F 列的数据 = E-G-R , E 是负数则为0 ====================================
    ds[('PV', 'AC MV Surplus')] = ds[('PV', 'AC MV Power Available')] - ds[('PV', 'AC MV Power to Infra')] - ds[
        ('BESS', 'AC LV Aux Power')]
    ds[('PV', 'AC MV Surplus')] = ds[('PV', 'AC MV Surplus')].where(ds[('PV', 'AC MV Power Available')] > 0, 0)

    # Excel列 S 只有储能提供的时候，才会显示值 Q | 字段: bat_to_sub
    # ds[('BESS', 'AC MV Power to Infra')] = df['BESS plant Power To Common Infrastructure Power [MW]']  # 储能供给基础设施
    # 更改2 ，= 3
    ds[('BESS', 'AC MV Power to Infra')] = 3  # 储能供给基础设施

    # Excel列 T 加入 L列， # 没有更新，但是考虑的：放电功率 + 储能消耗辅助功率 ，不区分是谁提供的，只有放电的时候才会只有储能提供- 暂 | 字段: bat_to_storage
    # ds[('BESS', 'AC LV Power to BESS')] = df['BESS Power To BESS plant aux consumuer [MW]']  # 储能内部自耗或循环功率 T
    # ds[('BESS', 'AC LV Power to BESS')] = ds[('BESS', 'AC LV Power to BESS')] + ds[('BESS', 'AC MV Power Discharge')] # T
    # 更改2
    ds[('BESS', 'AC LV Power to BESS')] = ds[('BESS', 'DC Power Discharge')] * params["PCS Efficiency [%]:"] * params[
        "LV Cable Efficiency [%]:"] * params["DC Cable Efficiency [%]:"] + ds[('BESS', 'AC LV Aux Power')]

    # Excel列 U | 字段: bat_to_pv
    # ds[('BESS', 'AC MV Power to PV')] = df['BESS Power To PV Plant [MW]']  # 储能向光伏馈电
    # 更改2 光伏不发电时的 abs(E),
    ds[('BESS', 'AC MV Power to PV')] = (-ds[('PV', 'AC MV Power Available')]).clip(lower=0)  # 储能向光伏馈电

    # Excel列 V | 字段: storage2grid
    ds[('BESS', 'AC MV Power to HV')] = df['BESS Power To Plant Substation BCP [MW]']  # 储能向高压侧放电（如果没有可填 '-' 或 0）

    # Excel列 W HV列  W | 字段: pv2grid + storage2grid  新增2 列不应出现负值负值全部应为0
    ds[('HV', 'AC HV Power at MV of MV/HV Transformer')] = df['PV Power To Plant Substation BCP [MW]'] + df[
        'BESS Power To Plant Substation BCP [MW]']  # 问题列 ： 高压侧交流中压功率 Mw不含高压变压器及高压电缆效率的功

    # Excel列 X 新增，需要有反向的数据， + -1*Z   ----- X | 字段: hv_power
    ds[('HV', 'AC HV Power at EDP')] = df['Exported Power [MW]']  # X 没有原始列可用，填 0 或 '-'

    # Excel列 Y 备用列 ----- Y | 字段: hv_power
    ds[('HV', 'Exported Power at EDP')] = df['Exported Power [MW]']

    # Excel列 Z 从电网输入功率 ----- Z | 字段: grid_power
    ds[('HV', 'Imported Power at EDP')] = df['Imported Power [MW]']

    # ======================== 更新 Excel列 X ----- X = Exported Power [MW] - Imported Power [MW]，hv_power - grid_power  相当于 = X - Z ===================
    ds[('HV', 'AC HV Power at EDP')] = ds[('HV', 'AC HV Power at EDP')] - ds[
        ('HV', 'Imported Power at EDP')]  # 新增，需要有反向的数据， + -1*Z

    # Excel列 AA 没有合并 | 字段: hv_power
    ds[('HVs', 'Exported Power at EDP.1')] = df['Exported Power [MW]']  # 备用列 AA

    # Excel列 AB | 字段: hv_power
    ds[('HVs', 'Exported Power > 1,000 MW')] = df['Exported Power [MW]']  # 超大功率输出 AB 无意义

    # 字段: storage2grid
    # ds[('HVs', 'Exported Power from BESS at EDP')] = df['BESS Power To Plant Substation BCP [MW]']  # 来自储能

    # # 新增   AA - AD
    # 字段: hv_power
    # ds[('HVs', 'Exported Power from BESS at EDP')] = df['Exported Power [MW]']  # 来自储能  AC
    #
    # # 新增 - AD   来自光伏 乘以 params["eta_trafo"] = 0.995    # 高压变压器效率    params["eta_cable"] = 0.99     # 高压电缆效率
    # 字段: pv2grid
    # ds[('HVs', 'Exported Power from PV at EDP')] = df['PV Power To Plant Substation BCP [MW]'] * params["eta_trafo"] * params['eta_cable'] # 来自光伏 AD
    # # AC = AA-AD
    # ds[('HVs', 'Exported Power from BESS at EDP')] = ds[('HVs', 'Exported Power at EDP.1')] - ds[('HVs', 'Exported Power from PV at EDP')]
    # 新增 - AD   来自光伏 乘以 params["eta_trafo"] = 0.995    # 高压变压器效率    params["eta_cable"] = 0.99     # 高压电缆效率

    # Excel列 AC  使用其他列 Exported Power [MW]， 如果 I>0 取值 Y 否则0 ， AC MV Power to HV 即 pv2grid>0 ,那么  取值 Y Exported Power [MW] 即 hv_power
    ds[('HVs', 'Exported Power from BESS at EDP')] = ds[('HV', 'Exported Power at EDP')].where(
        ds[('BESS', 'AC MV Power to HV')] > 0, 0)

    # Excel列 AD AD = AA-AC
    ds[('HVs', 'Exported Power from PV at EDP')] = ds[('HVs', 'Exported Power at EDP.1')] - ds[
        ('HVs', 'Exported Power from BESS at EDP')]

    # 映射 Mode，0：standby，1：charge，2：discharge

    # 更新 excel 列 H, 充电的时候有值，其余为0
    ds[('PV', 'AC MV Power to BESS')] = ds[('PV', 'AC MV Power to BESS')].where(ds[('BESS', 'Mode')] == '1', 0)

    # Excel列 L 更改3 #  L = S + U +V + R * (params["MV Transformer Efficiency [%]:"] * params['MV Cable Efficiency [%]:'])
    ds[('BESS', 'AC MV Power Discharge')] = ds[('BESS', 'AC MV Power to Infra')] + ds[('BESS', 'AC MV Power to PV')] + \
                                            ds[('BESS', 'AC MV Power to HV')]
    ds[('BESS', 'AC MV Power Discharge')] = ds[('BESS', 'AC MV Power Discharge')] + ds[('BESS', 'AC LV Aux Power')] * (
                params["MV Transformer Efficiency [%]:"] * params['MV Cable Efficiency [%]:'])

    # 更新 excel 列 L N T, 放电的时候有值，其余为0
    ds[('BESS', 'AC MV Power Discharge')] = ds[('BESS', 'AC MV Power Discharge')].where(ds[('BESS', 'Mode')] == '2', 0)

    # Excel列 N | 字段: Pdis_dc 更改3  Mode，0：standby，1：charge，2：discharge
    # [ L + S + U + R * (params["eta_trafo"] * params['eta_cable']) ]/ 放电效率
    # ds[('BESS', 'DC Power Discharge')] = ds[('BESS', 'AC MV Power Discharge')] +  ds[('BESS', 'AC MV Power to Infra')] + ds[('BESS', 'AC MV Power to PV')] + ds[('BESS', 'AC LV Aux Power')] * (params["MV Transformer Efficiency [%]:"] * params['MV Cable Efficiency [%]:'])
    # ds[('BESS', 'DC Power Discharge')] = ds[('BESS', 'DC Power Discharge')]/params['eta_dis']
    #  更新  N  =  L / 放电效率
    ds[('BESS', 'DC Power Discharge')] = ds[('BESS', 'AC MV Power Discharge')] / params['eta_dis']
    ds[('BESS', 'DC Power Discharge')] = ds[('BESS', 'DC Power Discharge')].where(ds[('BESS', 'Mode')] == '2', 0)

    # 更新 excel列 I  新增3 = F-G - k - R/(params["eta_trafo"] * params['eta_cable'])
    ds[('PV', 'AC MV Power to HV')] = ds[('PV', 'AC MV Surplus')] - ds[('PV', 'AC MV Power to Infra')] - ds[
        ('BESS', 'AC MV Power Charge')] - ds[('BESS', 'AC LV Aux Power')] / (params["eta_trafo"] * params['eta_cable'])
    ds[('PV', 'AC MV Power to HV')] = ds[('PV', 'AC MV Power to HV')].where(ds[('PV', 'AC MV Power Available')] > 0, 0)

    # Excel列 T  更改3 放电状态下：T=R ，其他未0
    ds[('BESS', 'AC LV Power to BESS')] = ds[('BESS', 'AC LV Aux Power')]
    ds[('BESS', 'AC LV Power to BESS')] = ds[('BESS', 'AC LV Power to BESS')].where(ds[('BESS', 'Mode')] == '2', 0)

    # Excel列 N  更改3  = L / eta_dis 放电效率
    ds[('BESS', 'DC Power Discharge')] = ds[('BESS', 'AC MV Power Discharge')] / params['eta_dis']

    return ds[output_columns]
