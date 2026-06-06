def update_param_eta_dis_single(params, year):
    params["eta_dis"] = params['Discharge_Efficiency_25years'][year]
    try:
        params["next_year_eta_dis"] = params['Discharge_Efficiency_25years'][year + 1]
    except:
        params["next_year_eta_dis"] = params['Discharge_Efficiency_25years'][year]
    return params



def update_param_IDLE_POINTS_list(params, year):
    year = year + 1  # 原逻辑：先加1再处理

    # 区间与 Stage 的映射表（包含边界和对应的配置 key）
    if params['Phase_name'] =='Phase_A':
        stages = [
            (1, 3, 'CY-01'),
            (4, 5, 'Stage-1'),
            (6, 7, 'Stage-2'),
            (8, 9, 'Stage-3'),
            (10, 11, 'Stage-4'),
            (12, 13, 'Stage-5'),
            (14, 15, 'Stage-6'),
            (16, 17, 'Stage-7'),
            (18, 19, 'Stage-8'),
            (20, 21, 'Stage-9'),
            (22, 23, 'Stage-10'),
            (24, 25, 'Stage-11'),
            (26, 38, 'Stage-12'),   # 最后一段原为 range(26, 27+11) → 26~38
        ]
    else:

        stages = [
            (1, 3+1, 'CY-01'),
            (4 + 1, 5+1, 'Stage-1'),
            (6 + 1, 7+1, 'Stage-2'),
            (8 + 1, 9+1, 'Stage-3'),
            (10 + 1, 11+1, 'Stage-4'),
            (12 + 1, 13+1, 'Stage-5'),
            (14 + 1, 15+1, 'Stage-6'),
            (16 + 1, 17+1, 'Stage-7'),
            (18 + 1, 19+1, 'Stage-8'),
            (20 + 1, 21+1, 'Stage-9'),
            (22 + 1, 23+1, 'Stage-10'),
            (24 + 1, 25+1, 'Stage-11'),
            (26 + 1, 38+1, 'Stage-12'),   # 最后一段原为 range(26, 27+11) → 26~38
        ]
    # 查找 year 所属的区间索引
    cur_idx = None
    for i, (start, end, _) in enumerate(stages):
        if start <= year <= end:
            cur_idx = i
            break

    if cur_idx is None:
        return params   # 不在任何已知区间，原 else: pass

    cur_start, cur_end, cur_stage = stages[cur_idx]

    # 处理下一年的数据
    next_year = year + 1
    # 判断下一年是否仍在当前区间
    if cur_start <= next_year <= cur_end:
        next_stage = cur_stage
    else:
        # 否则找下一个区间（如果存在），若不存在则沿用当前区间
        next_idx = cur_idx + 1
        if next_idx < len(stages):
            next_stage = stages[next_idx][2]
        else:
            next_stage = cur_stage   # 超出最后一个区间，原逻辑也是取相同 Stage

    aux = params['AuxPower_year25_charge']
    params['AuxPower_Points_charge'] = {}
    params['AuxPower_Points_charge']['T_POINTS'] = aux['AuxPower_year25'][cur_stage]['T_POINTS']
    params['AuxPower_Points_charge']['OP_POINTS'] = aux['AuxPower_year25'][cur_stage]['OP_POINTS']
    params['AuxPower_Points_charge']['IDLE_POINTS'] = aux['AuxPower_year25'][cur_stage]['IDLE_POINTS']

    params['AuxPower_Points_charge']['next_year_T_POINTS'] = aux['AuxPower_year25'][next_stage]['T_POINTS']
    params['AuxPower_Points_charge']['next_year_OP_POINTS'] = aux['AuxPower_year25'][next_stage]['OP_POINTS']
    params['AuxPower_Points_charge']['next_year_IDLE_POINTS'] = aux['AuxPower_year25'][next_stage]['IDLE_POINTS']

    aux = params['AuxPower_year25_discharge']
    params['AuxPower_Points_discharge'] = {}
    params['AuxPower_Points_discharge']['T_POINTS'] = aux['AuxPower_year25'][cur_stage]['T_POINTS']
    params['AuxPower_Points_discharge']['OP_POINTS'] = aux['AuxPower_year25'][cur_stage]['OP_POINTS']
    params['AuxPower_Points_discharge']['IDLE_POINTS'] = aux['AuxPower_year25'][cur_stage]['IDLE_POINTS']

    params['AuxPower_Points_discharge']['next_year_T_POINTS'] = aux['AuxPower_year25'][next_stage]['T_POINTS']
    params['AuxPower_Points_discharge']['next_year_OP_POINTS'] = aux['AuxPower_year25'][next_stage]['OP_POINTS']
    params['AuxPower_Points_discharge']['next_year_IDLE_POINTS'] = aux['AuxPower_year25'][next_stage]['IDLE_POINTS']
    return params

