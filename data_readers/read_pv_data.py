import pandas as pd
"""
说明 ：read_pv_data 有多个读取光伏的方法，每一种数据，都有各自读取的处理方式，如果换了表格形式，需要重新更新，或者增加新的方法，
"""

# 读取phaseA类的数据- 例如 PVsyst数据\Phase_A\159-UAE-DEWA-7 Project_Project_VCN_HourlyRes_1.CSV
def get_data_pv_phaseA(file_path):
    if file_path is None:
        file_path = R'../PVsyst数据\Phase_A\159-UAE-DEWA-7 Project_Project_VCN_HourlyRes_1.CSV'

    start_row = None
    with open(file_path, 'r', encoding='latin1') as f:
        for i, line in enumerate(f):
            if 'E_Grid' in line:
                start_row = i
                break
    if start_row is None:
        raise ValueError("文件中没有找到 'E_Grid'")

    df = pd.read_csv(
        file_path,
        skiprows=start_row,  # 从 E_Grid 行开始
        encoding='latin1',  # 避免 UTF-8 解码错误
        on_bad_lines='skip'  # 跳过列数不一致行
    )

    # a = df[df['E_Grid'].str.contains('kW')].index[0]
    # df.drop(index=a, inplace=True)
    a = df[df[df.columns[0]] == '01/01/90 00:00'].index[0]
    df = df.loc[a:,:]

    df[['E_Grid', 'T_Amb', 'GlobHor']] = df[['E_Grid', 'T_Amb', 'GlobHor']].astype(float)
    df.columns = ["date", "pv", "temp", "pv2"]
    # df['pv'].fillna(0, inplace=True)

    # E_Grid 是光伏，重命名为pv, 注意除以1000 ，保持单位
    df['pv'] = [round(i,5) for i in df['pv']/1000]
    df['t'] = pd.to_datetime(df['date'], format='%d/%m/%y %H:%M')
    df['day'] = pd.to_datetime(df['t'].dt.date)
    df['hour'] = df['t'].dt.hour
    df = df.groupby(['t']).head(1)
    # df = get_pv_fillna(df)
    df.sort_values(by='t', inplace=True)      # 根据时间进行排序
    df.reset_index(drop=True, inplace=True)   # 索引更新时间顺序
    return df


# 未使用 光伏数据进行缺失值填充 当前不可以用，因为数据中出现，年度跨的很长的，请注意。
def get_pv_fillna(df_pv):
    df_pv = df_pv[(df_pv['pv'].notna()) & (df_pv['pv'].astype(str).str.strip() != '')]
    df = pd.DataFrame(pd.date_range(df_pv['day'].min(),df_pv['day'].max()+pd.Timedelta(hours=23) ,freq='60Min'),columns=['t'])
    df = pd.merge(df, df_pv,how='left',on='t')
    df['temp'] = df['temp'].fillna(0)
    df['pv'] = df['pv'].fillna(0)
    return df


# 获取基本的光伏数据 类似 表格 159-UAE-DEWA-7 Project_Project_VCJ_HourlyRes_Phase C.csv 的光伏数据
def get_data_pv_159_UAE_DEWA_7_Project(file_path=None):
    if file_path is None:
        file_path = r"..\PVsyst数据\159-UAE-DEWA-7 Project_Project_VCJ_HourlyRes_Phase C.CSV"  # 替换成你的文件路径
    # | date	E_Grid	T_Amb	GlobHor
    # | E_Grid  | 光伏系统并网功率或能量输出（kWh 或 kW，具体单位需查看 PVsyst 设置）              |
    # | T_Amb   | 环境温度（Ambient Temperature, °C）                          |
    # | GlobHor | 全球水平辐照度（Global Horizontal Irradiance, W/m² 或 kWh/m²/h） |
    dfv = pd.read_csv(file_path,encoding='utf-8',skiprows=12,header=None)
    dfv.columns = ["date","pv","temp","ghi"]
    dfv['t'] = pd.to_datetime(dfv['date'], format='%d/%m/%y %H:%M')
    dfv['day'] = pd.to_datetime(dfv['t'].dt.date)
    dfv['hour'] = dfv['t'].dt.hour
    dfv = dfv.groupby(['t']).head(1)
    # dfv = get_pv_fillna(dfv) # 以防数据有问题，有跳跃，导致数据有问题。
    dfv.sort_values(by='t', inplace=True)
    dfv.reset_index(drop=True, inplace=True)
    return dfv

# 读取类似 Calculation - 5_3.23.xls 表格的光伏数据, pv是光伏，E_out=pv, Amp.Temp=temp,
def get_data_pv_Calculation_5_3_23(file_path=None):
    if file_path is None:
        file_path = r"..\PVsyst数据\Calculation - 5_3.23.xls"  # 替换成你的文件路径
    dfv2 = pd.read_excel(file_path, sheet_name='Sheet1')
    dfv2 = dfv2[['Date', 'Time', 'Amp.Temp', 'E_out']]
    dfv2.columns = ['day', 't', 'temp', 'pv']
    dfv2['s'] = [len(str(i)) for i in dfv2['t']]
    dfv2['t2'] = [str(dfv2['day'][i])[0:10] + ' ' + str(dfv2['t'][i]) for i in dfv2.index]
    dfv2.loc[dfv2['s'] == 8, 't'] = dfv2.loc[dfv2['s'] == 8, :]['t2']
    del dfv2['t2']
    del dfv2['s']
    dfv2['t'] = pd.to_datetime(dfv2['t'])
    dfv2['day'] = pd.to_datetime(dfv2['t'].dt.date)
    dfv2['hour'] = dfv2['t'].dt.hour
    dfv2 = dfv2.groupby(['t']).head(1)
    # dfv2 = get_pv_fillna(dfv2)
    dfv2.sort_values(by='t', inplace=True)
    dfv2.reset_index(drop=True, inplace=True)
    return dfv2

# df = get_data_pv_159_UAE_DEWA_7_Project()
# df = get_data_pv_Calculation_5_3_23()