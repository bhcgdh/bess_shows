import time
import pandas as pd
import xlsxwriter

def format_excel_all_sheets(
        input_file,
        output_file,
        fill_config=None,      # [(r1, r2, c1, c2, fill_color)]
        font_config=None,      # [(col_idx, font_color, font_size, bold)]
        underline_config=None, # [(row_idx, col_start, col_end)]
        right_border_config=None, # [(col_idx, row_start, row_end)]
        merge_config=None,     # [(r1, c1, r2, c2, value)]
        left_align_rows=None,  # [(r1, r2, c1, c2)]
        col_width=None,
):
    all_sheets = pd.read_excel(input_file, sheet_name=None, header=None)

    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        for sheet_name, df in all_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
            workbook = writer.book
            ws = writer.sheets[sheet_name]
            nrows, ncols = df.shape

            # 列宽
            if col_width:
                if isinstance(col_width, (int, float)):
                    ws.set_column(0, ncols-1, col_width)
                elif isinstance(col_width, dict):
                    for col_idx, width in col_width.items():
                        ws.set_column(col_idx-1, col_idx-1, width)

            format_cache = {}
            def get_format(props):
                key = tuple(sorted(props.items()))
                if key not in format_cache:
                    format_cache[key] = workbook.add_format(props)
                return format_cache[key]

            cell_styles = {}   # (row, col) -> dict of properties

            # 1. 背景填充
            if fill_config:
                for r1, r2, c1, c2, color in fill_config:
                    for row in range(r1-1, r2):
                        for col in range(c1-1, c2):
                            pos = (row, col)
                            cell_styles.setdefault(pos, {}).update({'bg_color': color})

            # 2. 字体
            if font_config:
                for col_idx, font_color, font_size, bold in font_config:
                    for row in range(nrows):
                        pos = (row, col_idx-1)
                        cell_styles.setdefault(pos, {}).update({
                            'font_color': font_color, 'font_size': font_size, 'bold': bold
                        })

            # 3. 下划线
            if underline_config:
                for row_idx, col_start, col_end in underline_config:
                    for col in range(col_start-1, col_end):
                        pos = (row_idx-1, col)
                        cell_styles.setdefault(pos, {}).update({'bottom': 1})

            # 4. 右边框
            if right_border_config:
                for col_idx, row_start, row_end in right_border_config:
                    for row in range(row_start-1, min(row_end, nrows)):
                        pos = (row, col_idx-1)
                        cell_styles.setdefault(pos, {}).update({'right': 1})

            # 5. 左对齐
            if left_align_rows:
                for r1, r2, c1, c2 in left_align_rows:
                    for row in range(r1-1, min(r2, nrows)):
                        for col in range(c1-1, min(c2, ncols)):
                            pos = (row, col)
                            cell_styles.setdefault(pos, {}).update({
                                'align': 'left', 'valign': 'vcenter', 'text_wrap': True
                            })

            # 6. 合并单元格（先处理，避免冲突）
            if merge_config:
                for r1, c1, r2, c2, value in merge_config:
                    row_start, col_start = r1-1, c1-1
                    row_end, col_end = r2-1, c2-1
                    # # 取值
                    # if value is None:
                    #     val = df.iat[row_start, col_start] if row_start < nrows and col_start < ncols else ""
                    # else:
                    #     val = value
                    val = value

                    # 合并区域的样式：居中 + 左上角原有样式（如背景色）
                    merge_props = {'align': 'center', 'valign': 'vcenter'}
                    if (row_start, col_start) in cell_styles:
                        merge_props.update(cell_styles[(row_start, col_start)])
                    merge_fmt = workbook.add_format(merge_props)
                    ws.merge_range(row_start, col_start, row_end, col_end, val, merge_fmt)
                    # 移除合并区域内的样式标记
                    for row in range(row_start, row_end+1):
                        for col in range(col_start, col_end+1):
                            cell_styles.pop((row, col), None)

            # 7. 应用所有剩余样式
            for (row, col), props in cell_styles.items():
                if row < nrows and col < ncols:
                    value = df.iat[row, col] if pd.notna(df.iat[row, col]) else ""
                    fmt = get_format(props)
                    ws.write(row, col, value, fmt)

    print(f"处理完成：{output_file}")

