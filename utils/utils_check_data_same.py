import pandas as pd
def compare_excel_ignore_top_rows(file1, file2, skiprows=5, key_col=0):
    """
    比较两个 Excel 文件，跳过顶部指定行，以第一列为键匹配行。

    参数:
        file1, file2: 文件路径
        skiprows: 跳过前N行（默认5，即忽略第1-5行）
        key_col: 用作匹配键的列索引（默认0，即第一列）

    返回:
        bool: 是否完全相同
        dict: 差异详情
    """
    # 读取所有 sheet，跳过前 skiprows 行，且不将第一行作为列名
    sheets1 = pd.read_excel(file1, sheet_name=None, header=None, skiprows=skiprows)
    sheets2 = pd.read_excel(file2, sheet_name=None, header=None, skiprows=skiprows)

    # 检查 sheet 名称是否一致
    if set(sheets1.keys()) != set(sheets2.keys()):
        print(f"Sheet 名称不一致: {set(sheets1.keys())} vs {set(sheets2.keys())}")
        return False, {"sheet_mismatch": (list(sheets1.keys()), list(sheets2.keys()))}

    all_match = True
    diff_details = {}

    for sheet_name in sheets1.keys():
        df1 = sheets1[sheet_name]
        df2 = sheets2[sheet_name]

        # 如果数据框为空，跳过比较
        if df1.empty and df2.empty:
            continue
        if df1.empty or df2.empty:
            all_match = False
            diff_details[sheet_name] = f"一方为空: df1 shape {df1.shape}, df2 shape {df2.shape}"
            continue

        # 使用第一列作为行键
        # 注意：第一列可能有重复值？通常应是唯一标识，但如果有重复，pandas 会保留最后一个
        # 为了安全，我们检查重复值并警告
        key1 = df1[key_col]
        key2 = df2[key_col]
        if key1.duplicated().any():
            print(f"警告: {sheet_name} 文件1的第一列有重复值，将使用最后出现的行为准")
        if key2.duplicated().any():
            print(f"警告: {sheet_name} 文件2的第一列有重复值，将使用最后出现的行为准")

        # 设置为索引以便对齐
        df1_idx = df1.set_index(key_col)
        df2_idx = df2.set_index(key_col)

        # 找出共同的 key 和独有的 key
        common_keys = df1_idx.index.intersection(df2_idx.index)
        only_in_1 = df1_idx.index.difference(df2_idx.index)
        only_in_2 = df2_idx.index.difference(df1_idx.index)

        if len(only_in_1) > 0 or len(only_in_2) > 0:
            all_match = False
            diff_details[sheet_name] = {
                "only_in_file1": only_in_1.tolist(),
                "only_in_file2": only_in_2.tolist()
            }

        # 对共同 key 逐行比较
        for key in common_keys:
            row1 = df1_idx.loc[key]
            row2 = df2_idx.loc[key]
            # 比较所有列（包括第一列本身已经通过 key 对齐，无需再比）
            # 但为了完整性，可以比较所有值
            if not row1.equals(row2):
                all_match = False
                # 记录哪些列不同
                diff_cols = []
                for col in range(len(row1)):
                    val1 = row1.iloc[col] if isinstance(row1, pd.Series) else row1[col]
                    val2 = row2.iloc[col] if isinstance(row2, pd.Series) else row2[col]
                    # 处理 NaN 比较
                    if pd.isna(val1) and pd.isna(val2):
                        continue
                    if val1 != val2:
                        diff_cols.append((col, val1, val2))
                if diff_cols:
                    diff_details.setdefault(sheet_name, {}).setdefault("value_mismatch", {})[key] = diff_cols

        # 检查列数是否相同
        if df1.shape[1] != df2.shape[1]:
            all_match = False
            diff_details.setdefault(sheet_name, {}).setdefault("column_count", (df1.shape[1], df2.shape[1]))

    return all_match, diff_details


# 使用示例 检测 文件是否相同
def run_compare_excel_ignore_top_rows():
    file_a = r"F:\bess_shows\PVsyst数据\结果数据\UAE_DEWA7_PhaseA_PM_Output v1.0.xlsx"
    file_b = r"F:\bess_shows\PVsyst数据\结果数据\UAE_DEWA7_PhaseA_PM_Output v1.0_format.xlsx"

    is_same, diffs = compare_excel_ignore_top_rows(file_a, file_b, skiprows=5, key_col=0)

    if is_same:
        print("两个文件完全一致（跳过前5行，按第一列匹配）。")
    else:
        print("发现差异：")
        import pprint

        pprint.pprint(diffs)