import pandas as pd
import numpy as np
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

# 负数乘以0.99， 否则不用
def get_data_pv_rate(df,params, name='pv'):
    df.loc[df[name]>0,'pv'] = df.loc[df[name]>0,'pv']  * params['pv_rate']
    return df

def get_data_pv_to_curtailed(df,params):
    df['pv_to_curtailed'] = df['pv_to_curtailed'] - params["pv_max_Discharge_cap"]
    df['pv_to_curtailed'] = [i if i>0 else 0 for i in df['pv_to_curtailed']]
    return df
