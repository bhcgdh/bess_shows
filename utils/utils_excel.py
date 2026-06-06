import pandas as pd
import re
from collections import Counter
import numpy as np
from difflib import SequenceMatcher

# ===========================================================
# 工具-读取excel-找到字段所在的行和数据
def utils_read_excel_by_fields(
        file_path,
        sheet_name=None,
        name1=None,
        match_all=False,
        read_mode="all_columns",  # "all_columns" 或 "only_name1_columns"
        engine=None,
        dtype=None,
        strip_columns=True
):
    """
    根据 name1 在 Excel 中查找字段所在行，再按指定方式读取数据。

    参数
    ----------
    file_path : str
        Excel 文件路径
    sheet_name : str/int, default 0
        sheet 名称或索引
    name1 : str 或 list
        要查找的字段
    match_all : bool, default False
        当 name1 是 list 时：
        - False: 行中命中任意一个字段即可
        - True : 行中必须同时包含全部字段
    read_mode : str, default "all_columns"
        - "all_columns"       : 读取所在行作为表头后的所有列
        - "only_name1_columns": 只保留 name1 对应的列
    engine : str, default None
        例如 openpyxl
    dtype : default None
        传给 pd.read_excel 的 dtype
    strip_columns : bool, default True
        是否对列名去掉首尾空格

    """

    if name1 is None:
        raise ValueError("name1 不能为空")

    if isinstance(name1, str):
        target_fields = [name1]
    elif isinstance(name1, list):
        if len(name1) == 0:
            raise ValueError("name1 不能为空列表")
        target_fields = [str(x).strip() for x in name1]
    else:
        raise TypeError("name1 只能是 str 或 list")

    # 整体读取，先找目标行
    df_raw = pd.read_excel(
        file_path,
        sheet_name=sheet_name,
        header=None,
        dtype=str,
        engine=engine
    )

    start_row = None
    matched_fields_in_row = None

    for i in range(len(df_raw)):
        row_values = df_raw.iloc[i].fillna("").astype(str).str.strip().tolist()

        if match_all:
            matched = all(field in row_values for field in target_fields)
        else:
            matched = any(field in row_values for field in target_fields)

        if matched:
            start_row = i
            matched_fields_in_row = [field for field in target_fields if field in row_values]
            break

    if start_row is None:
        raise ValueError(f"没有找到匹配字段所在的行: {target_fields}")

    # 用找到的行作为表头重新读取
    df = pd.read_excel(
        file_path,
        sheet_name=sheet_name,
        header=start_row,
        engine=engine,
        dtype=dtype
    )

    if strip_columns:
        df.columns = [str(col).strip() for col in df.columns]

    #  从该字段开始读取所有的数据
    if read_mode == "all_columns":
        return df # , start_row, matched_fields_in_row

    #  从该字段开始读取所有的数据  》 且只要这几列的数据
    elif read_mode == "only_name1_columns":
        cols_to_keep = [col for col in df.columns if col in matched_fields_in_row]

        if not cols_to_keep:
            raise ValueError(f"读取后未找到这些列: {matched_fields_in_row}")

        df = df[cols_to_keep]
        return df # , start_row, matched_fields_in_row

    else:
        raise ValueError("read_mode 只能是 'all_columns' 或 'only_name1_columns'")

# =========================================================== 查找行号码

# 工具 在 DataFrame 中查找指定值所在的行号。
def _normalize_text(x):
    if pd.isna(x):
        return ""
    return " ".join(str(x).strip().split())

def utils_mask_index(df, values):
    # 先把整个 df 标准化一次，避免每次循环重复处理
    # df_norm = df.map(_normalize_text)
    df_norm = df.apply(lambda col: col.map(_normalize_text))
    if isinstance(values, str):
        target = _normalize_text(values)
        mask = df_norm.eq(target)
        row_index = df.index[mask.any(axis=1)].tolist()
        if not row_index:
            raise ValueError(f"未找到值: {values}")
        return min(row_index)
    else:
        row_indexs = []

        for value in values:
            target = _normalize_text(value)
            mask = df_norm.eq(target)
            row_index = df.index[mask.any(axis=1)].tolist()

            if row_index:
                row_indexs.append(row_index[0])
        if not row_indexs:
            raise ValueError(f"未找到任何值: {values}")

        most_common_value = Counter(row_indexs).most_common(1)[0][0]
        return most_common_value

# =========================================================== # 提取字段所在 的值，判断在右边还是下边，小数点后5位
def _norm_text(s):
    
    s = str(s).strip().lower()
    s = re.sub(r'[\s:%\[\]：]+', '', s)
    return s

def _parse_percent_value(x):

    if pd.isna(x):
        return None

    # 已经是数值
    if isinstance(x, (int, float)):
        x = float(x)
        return x if 0 <= x <= 1 else x / 100

    s = str(x).strip().replace(",", "")

    # 过滤明显不是值的内容
    if re.search(r'[a-zA-Z\u4e00-\u9fff]', s) and '%' not in s:
        return None

    try:
        if '%' in s:
            return float(s.replace('%', '')) / 100
        else:
            v = float(s)
            return v if 0 <= v <= 1 else v / 100
    except:
        return None

# 提取字段所在 的值，判断在右边还是下边，小数点后5位
def utils_extract_near_values(file_path=None, sheet_name=None,fields=None):

    df = pd.read_excel(file_path, sheet_name=sheet_name)
    result = {}

    for field in fields:
        field_std = _norm_text(field)

        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                cell = df.iat[i, j]
                if pd.isna(cell):
                    continue

                cell_std = _norm_text(cell)

                if cell_std == field_std or cell_std in field_std or field_std in cell_std:
                    value = None

                    # 1. 先看右边是不是有效值
                    if j + 1 < df.shape[1]:
                        value = _parse_percent_value(df.iat[i, j + 1])

                    # 2. 右边不是值，再看下面
                    if value is None and i + 1 < df.shape[0]:
                        value = _parse_percent_value(df.iat[i + 1, j])

                    if value is not None:
                        result[field] = round(value,5)
                    break

            if field in result:
                break

    return result

def utils_extract_right_value(file_path, sheet_name=None, fields=None, offset=1):
    """
    查找字段，并严格取右边第 offset 列的值
    """
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    result = {}

    for field in fields:
        field_std = _norm_text(field)
        found = False

        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                cell = df.iat[i, j]
                if pd.isna(cell):
                    continue

                cell_std = _norm_text(cell)
                if cell_std == field_std or cell_std in field_std or field_std in cell_std:
                    # 严格取右边第 offset 列
                    if j + offset < df.shape[1]:
                        value = _parse_percent_value(df.iat[i, j + offset])
                        if value is not None:
                            result[field] = round(value, 5)
                    found = True
                    break
            if found:
                break

    return result


def _utils_merge_two_header_rows(top_headers, sub_headers, time_fill=4):
    """
    合并两行表头：
    1. 前 time_fill 列归到 Time
    2. 第一行空值向左填充
    3. 生成扁平列名，格式：一级字段__二级字段
    """
    top_headers = list(top_headers)
    sub_headers = list(sub_headers)

    merged_top = []
    last_valid_top = None

    for idx, value in enumerate(top_headers):
        if idx < time_fill:
            current_top = "Time"
        else:
            if pd.isna(value) or str(value).strip() == "":
                current_top = last_valid_top
            else:
                current_top = str(value).strip()
        merged_top.append(current_top)
        last_valid_top = current_top

    columns = []
    for top_value, sub_value in zip(merged_top, sub_headers):
        sub_value = "" if pd.isna(sub_value) else str(sub_value).strip()
        if not sub_value:
            columns.append(str(top_value))
        elif str(top_value) == sub_value:
            columns.append(sub_value)
        else:
            columns.append(f"{top_value}__{sub_value}")
    return columns


def _utils_try_parse_excel_value(value):
    """
    将 Excel 中常见的字符串数字转换为数值：
    - 1,718.47 -> 1718.47
    - 34.389% -> 34.389
    其余保留原值
    """
    if pd.isna(value):
        return np.nan

    if isinstance(value, (int, float, np.integer, np.floating)):
        return value

    text = str(value).strip()
    if text == "":
        return np.nan

    text_no_comma = text.replace(",", "")
    if text_no_comma.endswith("%"):
        text_no_comma = text_no_comma[:-1].strip()

    try:
        return float(text_no_comma)
    except:
        return value


def utils_read_pvsyst_result_for_analysis(
        file_path,
        sheet_name=0,
        header_rows=(0, 1),
        data_start_row=5,
        time_fill=4,
        drop_empty_rows=True
):
    """
    读取结果汇总表用于分析。

    适用于这类格式：
    1. 第 1、2 行是字段
    2. 第 6 行开始是数据
    3. 中间可能有汇总值和单位行
    """
    df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

    top_headers = df_raw.iloc[header_rows[0]].tolist()
    sub_headers = df_raw.iloc[header_rows[1]].tolist()
    columns = _utils_merge_two_header_rows(top_headers, sub_headers, time_fill=time_fill)

    df_data = df_raw.iloc[data_start_row:].copy().reset_index(drop=True)
    df_data.columns = columns

    if drop_empty_rows:
        df_data = df_data.dropna(how='all').reset_index(drop=True)

    for col in df_data.columns:
        df_data[col] = df_data[col].apply(_utils_try_parse_excel_value)

    return df_data


def utils_analyze_pvsyst_result(
        file_path,
        sheet_name=0,
        header_rows=(0, 1),
        data_start_row=5,
        time_fill=4
):
    """
    读取并分析结果表，返回：
    - df: 清洗后的明细数据
    - numeric_summary: 数值列统计
    - missing_summary: 缺失值统计
    """
    df = utils_read_pvsyst_result_for_analysis(
        file_path=file_path,
        sheet_name=sheet_name,
        header_rows=header_rows,
        data_start_row=data_start_row,
        time_fill=time_fill,
    )

    numeric_df = df.select_dtypes(include=[np.number])
    numeric_summary = numeric_df.describe().T if not numeric_df.empty else pd.DataFrame()
    missing_summary = pd.DataFrame({
        "column": df.columns,
        "missing_count": df.isna().sum().values,
        "missing_ratio": (df.isna().mean().values).round(6),
    })

    return {
        "df": df,
        "numeric_summary": numeric_summary,
        "missing_summary": missing_summary,
    }

# =========================================================== # 提取字段所在 的值，温度 和 负荷数据

# 第一种温度数据： 读取温度对应的数据，参考表：Calculation - Update_PV_Phase C.xlsx
# 数据 Temperature℃， Aux power operation MW，Aux power idle MW字段下方的数据
def utils_extract_aux_table_type1(file_path=None, sheet_name=0):
    """
    读取 Excel，查找字段，并提取字段正下方连续数值
    遇到空值或非数值就停止
    """
    # 整表读取，不指定表头
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

    # 目标字段
    targets = {
        "Temperature℃": ["temperature℃", "temperature"],
        "Aux power operation MW": ["aux power operation mw", "aux power operation"],
        "Aux power idle MW": ["aux power idle mw", "aux power idle"]
    }

    def norm(x):
        """文本标准化，便于模糊匹配"""
        if pd.isna(x):
            return ""
        x = str(x).strip().lower()
        x = re.sub(r"\s+", "", x)
        x = x.replace("℃", "").replace(":", "")
        return x
    def to_float(x):
    
        try:
            return float(str(x).replace(",", "").strip())
        except:
            return None
    result = {}
    for std_name, keys in targets.items():
        result[std_name] = []
        found = False

        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                cell = norm(df.iat[i, j])
                # 找到字段
                if any(norm(k) in cell for k in keys):
                    vals = []
                    # 只读取字段正下方
                    for r in range(i + 1, df.shape[0]):
                        v = df.iat[r, j]
                        num = to_float(v)
                        # 空值或非数值就停止
                        if pd.isna(v) or str(v).strip() == "" or num is None:
                            break
                        vals.append(num)
                    result[std_name] = vals
                    found = True
                    break
            if found:
                break
    result = {"T_POINTS": result.get("Temperature℃", []),
              "OP_POINTS": result.get("Aux power operation MW", []),
              "IDLE_POINTS": result.get("Aux power idle MW", [])}
    return result

# 第二种温度数据： 读取温度对应的数据，参考表：Input_ppp.xlsx, 温度在右侧
def utils_extract_aux_table_type2(file_path, sheet_name=0):
    """
    读取 Excel，查找字段，并提取字段正下方连续数值
    遇到空值或非数值就停止
    # """
    # file_path = r"F:\bess_shows\PVsyst数据\参数数据\Input_ppp.xlsx"
    # sheet_name = "BESS"

    df = pd.read_excel(file_path, sheet_name=sheet_name)

    k1 = utils_mask_index(df, "Amb temp")
    k2 = utils_mask_index(df, "Aux power idle")
    k3 = utils_mask_index(df, "Aux power operation")

    df_new = df.loc[[k1, k2, k3], :].T.reset_index(drop=True)
    df_new.columns = df_new.iloc[0]
    df_new = df_new.iloc[1:].reset_index(drop=True)
    df_new["Amb temp"] = pd.to_numeric(df_new["Amb temp"], errors="coerce")
    df_new = df_new.dropna(subset=["Amb temp"]).reset_index(drop=True)
    df_new.columns = [i.strip() for i in df_new.columns]

    data = {'T_POINTS': df_new["Amb temp"].tolist(),
            'OP_POINTS': df_new["Aux power idle"].tolist(),
            'IDLE_POINTS': df_new["Aux power operation"].tolist()
            }
    return data
