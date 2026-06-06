import os
from openpyxl import load_workbook
from pathlib import Path
import pandas as pd
import time
from pandas.api.types import is_numeric_dtype
from  .output_excel_config import save_excel_with_field_config_pv
from  .output_excel_config import save_excel_with_field_config_GWh
import sys

def setup_path():

    current = Path(__file__).resolve()
    # 向上查找包含 bess_shows 目录的父目录
    for parent in current.parents:
        if (parent / "bess_shows").is_dir():
            root = parent
            break
    else:
        # 如果没找到，假设当前在 bess_shows 下两级
        root = current.parents[1]  # 向上两级到 bess_shows 的父目录
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
setup_path()

from utils.utils_file import utils_insert_df_into_df_GWh


"""
数据保存到表格中作以下处理
1）定义字段名称
2）soc 转为 soc%,保留小数点
3）数值数据，小数点都进行保留  
4) 调用

"""

# 小数点取数据 数值数据取小数据点后2位置(point_float) ， soc%设置为乘以100之后的后三位(point_soc)
def _format_dataframe_columns(df,point_soc=3, point_float=2):
    c1 = ['day', 't', 'temp', 'pv', 'Placeholder', 'soc|capacity', 'aux_storage', 'subAux', 'pv2grid', 'storage2grid',
          'state', 'Pin_ac', 'Pdis_ac', 'pv_to_storage', 'pv_to_sub', 'Pin_dc', 'Pdis_dc', 'bat_to_storage',
          'bat_to_sub', 'grid_power', 'bat_to_pv', 'soc', 'hv_power', 'PV power Dump [MW]']
    c2 = ['SOC/%', 'BESS Auxiliary Power [MW]', 'Common Infrastructure Aux Power[MW]', 'PV Power To Plant Substation BCP [MW]',
          'BESS Power To Plant Substation BCP [MW]', 'Mode', 'PV Power to BESS Plant BCP [MW]',
          'DisCharge Power BCP [MW]', 'PV Power To BESS plant aux consumuer [MW]', 'PV Power To Common Infrastructure Power [MW] ',
          'Charge Power [DC]', 'Discharge Power [DC]', 'BESS Power To BESS plant aux consumuer [MW]',
          'BESS plant Power To Common Infrastructure Power [MW]', 'Imported Power [MW]', 'BESS Power To PV Plant [MW]',
          'Energy [DC]', 'Exported Power [MW]']
    cols = c1+c2
    df = df.copy()
    df['Date'] = [str(i)[0:10] for i in df['Date']]
    for col in df.columns:
        if col == 'SOC/%':
            vals = pd.to_numeric(df[col], errors='coerce')
            df[col] = vals.apply(lambda x: f"{x * 100:.{point_soc}f}%" if pd.notna(x) else "")
        else:
            if col!='Date':
                # 先判断本身是不是数值列
                if is_numeric_dtype(df[col]):
                    if col not in cols:
                        df[col] = df[col].round(5)
                    else:
                        df[col] = df[col].round(point_float)
                else:
                    # 非数值列，尝试转成数值
                    converted = pd.to_numeric(df[col], errors='coerce')

                    # 只有在“这一列确实有数值”时才替换
                    if converted.notna().any():
                        if col not in cols:
                            df[col] = df[col].round(5)
                        else:
                            df[col] = df[col].round(point_float)
                    # 否则保持原样
    return df


def _deal_save_data_df_pv_sheet1(df,params):
    
    # 1 重命名前 4 列
    df.rename(columns={
        'day': 'Date',
        't': 'Time',
        'temp': 'Amp.Temp',
        'pv': 'E_out'
    }, inplace=True)
    df['Time'] = df['Time'].astype(str).str[11:]  # 截取时间部分

    # 2⃣ 插入空列作为 Excel E 列占位
    df.insert(4, 'Placeholder', pd.NA)  # 第5列，列名随意，这里用 'Placeholder'
    if 'pv2' in df.columns:
        del df['pv2']

    # 3重命名 BESS/光伏列
    rename_dict = {
        "soc|capacity": "SOC/%",  # 避免重复 soc
        "aux_storage": "BESS Auxiliary Power [MW]",
        "subAux": "Common Infrastructure Aux Power[MW]",
        "pv2grid": "PV Power To Plant Substation BCP [MW]",
        "storage2grid": "BESS Power To Plant Substation BCP [MW]",
        "state": "Mode",
        "Pin_ac": "PV Power to BESS Plant BCP [MW]",
        "Pdis_ac": "DisCharge Power BCP [MW]",
        "pv_to_storage": "PV Power To BESS plant aux consumuer [MW]",
        "pv_to_sub": "PV Power To Common Infrastructure Power [MW]",
        "Pin_dc": "Charge Power [DC]",
        "Pdis_dc": "Discharge Power [DC]",
        "bat_to_storage": "BESS Power To BESS plant aux consumuer [MW]",
        "bat_to_sub": "BESS plant Power To Common Infrastructure Power [MW]",
        "grid_power": "Imported Power [MW]",
        "bat_to_pv": "BESS Power To PV Plant [MW]",
        "soc": "Energy [DC]",
        "hv_power": "Exported Power [MW]",
        "pv_to_curtailed":"PV power Dump [MW]" # 新增一列，光伏弃光量
    }
    df.rename(columns=rename_dict, inplace=True)

    column_order = [
        "Date",
        "Time",
        "Amp.Temp",
        "E_out",
        "Placeholder",  # 空列对应 Excel E
        "SOC/%",
        "BESS Auxiliary Power [MW]",
        "Common Infrastructure Aux Power[MW]",
        "PV Power To Plant Substation BCP [MW]",
        "BESS Power To Plant Substation BCP [MW]",
        "Mode",
        "PV Power to BESS Plant BCP [MW]",
        "DisCharge Power BCP [MW]",
        "PV Power To BESS plant aux consumuer [MW]",
        "PV Power To Common Infrastructure Power [MW]",
        "Charge Power [DC]",
        "Discharge Power [DC]",
        "BESS Power To BESS plant aux consumuer [MW]",
        "BESS plant Power To Common Infrastructure Power [MW]",
        "Imported Power [MW]",
        "BESS Power To PV Plant [MW]",
        "Energy [DC]",
        "Exported Power [MW]",
        "PV power Dump [MW]" # 新增排序字段
        ""
    ]
    if 1 in df.columns:
        column_order = column_order+[0,1,2]
    df = df.reindex(columns=column_order)
    # 小数点数据进行处理
    df = _format_dataframe_columns(df)
    # 新增3 更新分表I列的值，
    df["PV Power To Plant Substation BCP [MW]"] = (df['E_out'] - df['PV Power to BESS Plant BCP [MW]'] -
                                                   df['Common Infrastructure Aux Power[MW]'] -
                                                   df['BESS Auxiliary Power [MW]'] / (params["MV Transformer Efficiency [%]:"] * params["MV Cable Efficiency [%]:"]))

    df["PV Power To Plant Substation BCP [MW]"] = [df["PV Power To Plant Substation BCP [MW]"][i]  if df['E_out'][i]>0 else 0 for i  in df.index]
    return df

def save_data_phaseA(df=None,sheet_name_df='Sheet1',
                     df_gwh=None, sheet_name_df_gwh='Sheet2',
                     output_path=None,params =None
                     ):
    """
    savesheets : 结果数据保存到一张表，还是保存到两张表中
    """
    # 假设原始 df
    df = df.copy()
    # print("save_data_phaseA   ----- df['pv2grid'].min()   ",df['pv2grid'].min())
    df_gwh = df_gwh.copy()

    output_path = output_path.replace(".CSV", ".xlsx").replace(".csv", ".xlsx")

    # 判断文件是否存在且为有效 Excel
    valid_excel = False
    if os.path.exists(output_path):
        try:
            # 尝试加载，如果能成功则认为是有效文件
            pd.ExcelFile(output_path)
            valid_excel = True
        except Exception:
            # 文件存在但不是有效 Excel，后续会覆盖
            os.remove(output_path)
            valid_excel = False



    # 储能的结果保存 和 统计值放在两张表里,即指定了不同的表格名称
    if sheet_name_df != sheet_name_df_gwh:
        if valid_excel:
            # 文件有效：追加模式
            with pd.ExcelWriter(output_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df = _deal_save_data_df_pv_sheet1(df,params)
                df.to_excel(writer, sheet_name=sheet_name_df, index=False)
                df_gwh.to_excel(writer, sheet_name=sheet_name_df_gwh, index=False, header=False)
        else:
            # 文件无效或不存在：新建
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df = _deal_save_data_df_pv_sheet1(df,params)
                df.to_excel(writer, sheet_name=sheet_name_df, index=False)
                df_gwh.to_excel(writer, sheet_name=sheet_name_df_gwh, index=False, header=False)

        # save_excel_with_header_style(saveName)
        # 对dfv 光伏结果 表格进行格式更新，字头宽度和颜色
        save_excel_with_field_config_pv(output_path,   sheet_name=sheet_name_df) # 表的名称

        # 对dfv 统计gwh的结果 表格进行格式更新，字头宽度和颜色
        save_excel_with_field_config_GWh(output_path,   sheet_name=sheet_name_df_gwh) # 表的名称

    else:
        distance_from_end = 1 # df_gwh 插入到df 右侧
        add_GWh_col = int(distance_from_end + df.shape[1])

        #  统计 总和值，拼接到页面右侧
        df = utils_insert_df_into_df_GWh(df,df_gwh,distance_from_end=distance_from_end)
        df = _deal_save_data_df_pv_sheet1(df,params)

        df.to_excel(output_path, sheet_name=sheet_name_df, index=False )

        add_GWh_col = int(distance_from_end + df.shape[1]-3)
        save_excel_with_field_config_pv(output_path, sheet_name=sheet_name_df, add_GWh=True,add_GWh_col=add_GWh_col) # 表的名称
        time.sleep(0.5)
