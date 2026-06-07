import warnings
warnings.filterwarnings('ignore')
import os
import time
from datetime import datetime
# 当前时间：20250523_140303
time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
from run_year import run_data_year # 调用每年的执行
from data_readers.read_input_params import get_origh_params # 获取所有参数的工具
from data_readers.read_update_params import * # 参数更新
from data_calculators.calculate_output import save_all_year_raw_dfs_to_single_workbook # 新增最后的输出
from utils.utils_file import utils_ensure_folder,utils_save_params_to_yaml  # 处理文件的通用工具

# 指定 效率参数
# def define_Efficiency(params):
    # params["eta_ch"] = 0.9325  # 充电效率 变动的 ===使用计算的 === 之前写死的，后面表格读取
    # params["eta_dis"] = 0.9747  # 放电效率  变动的 之前写死的，后面表格读取
    # params["target_hv_power"] = 260  # 高压侧目标放电功率 MW  之前写死的，后面表格读取
    # params["eta_trafo"] = 0.995    # 高压变压器效率 暂时写死
    # params["eta_cable"] = 0.99     # 高压电缆效率
    # return params
# =====================  下面是针对每年的计算，进行的参数定义，参数读取，参数更新，结果保存等功能的实现  ==================== 
# 指定 充放电的小时
def define_hour_charge(params):
    # 充电 放电 小时时间
    params['hour_charge'] = [1,2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]    # 充电时间
    params['hour_discharge'] = [0, 19, 20, 21, 22, 23]  # 放电时间段 判断是否为放电时段（19:00-01:00）
    return params

def define_all_params(params=None):
    if params is None:
        params = {}
    define_hour_charge(params)   # 指定充电小时 ，19-01放电
    return params


def _phase_name_to_json_key(phase_name):
    return phase_name.replace("_", " ")


def _build_phase_year_by_ids(params, phase_name_json):
    return {
        ids: year_key
        for ids, year_key in enumerate(params["Phase"][phase_name_json].keys())
    }


def update_param_from_phase_year(params, ids):
    ids_year = params["phase_year_by_ids"][ids]
    phase_year_params = params["Phase"][params["Phase_name_json"]][ids_year]

    params["ids_year"] = ids_year
    params["capacity"] = phase_year_params["capacity"]
    params["Battery Efficiency [%]:"] = phase_year_params["Battery Efficiency [%]:"]
    params["eta_ch"] = phase_year_params["eta_ch"]
    params["eta_dis"] = phase_year_params["eta_dis"]
    return params


def _build_aux_power_year25(aux_power_params, phase_name_json):
    result = {"AuxPower_year25": {}}
    for stage_name, stage_values in aux_power_params.items():
        aux_key = stage_name.replace("Stage ", "Stage-")
        phase_values = stage_values[phase_name_json]
        result["AuxPower_year25"][aux_key] = {
            "T_POINTS": phase_values["Temperature"],
            "OP_POINTS": phase_values["Aux power operation MW"],
            "IDLE_POINTS": phase_values["Aux power idle MW"],
        }
    return result

# 读取表格数据 参数数据
# 1 25年的容量
def run_phase(params,input_folder,finally_folder):
    # 1 是否保存每次的结果值
    params.setdefault("save_yearly_output", True)  # 保存单表
    params.setdefault("save_final_workbook", True) #  保存到一个大表
    params.setdefault("format_final_workbook", True)  # 更新大表数据和格式

    phase_name = params['Phase_name'] # 进行计算的 a b c 名称
    phase_name_json = _phase_name_to_json_key(phase_name) # Phase_A 转为 Phase A
    params['Phase_name_json'] = phase_name_json

    # 2 获取进行增补的年份，暂时手动
    params = define_all_params(params)   # 先 读取本文件中，自定义的参数, 定死的数据
    params = get_origh_params(params)    # 再 读取表格中的参数数据
    params["phase_year_by_ids"] = _build_phase_year_by_ids(params, phase_name_json)

    # 获取充电的8小时 或者 放电 6小时，对应的 辅助功率值
    params["AuxPower_year25_charge"] = _build_aux_power_year25(params["Aux power 8h"], phase_name_json)
    params["AuxPower_year25_discharge"] = _build_aux_power_year25(params["AuxPower6h"], phase_name_json)

    # 指定表格的，Phase 对应的参数数据 , 直接读取
    ppm_phase = params['PPM Design Input Sheet'][phase_name_json]
    params["MV/HV Transformer Efficiency[%]:"] = ppm_phase["MV/HV Transformer Efficiency[%]:"]
    params["HV Losses up to DP[%]:"] = ppm_phase["HV Losses up to DP[%]:"]
    params["MV Transformer Efficiency [%]:"] = ppm_phase["MV Transformer Efficiency [%]:"]
    params["MV Cable Efficiency [%]:"] = ppm_phase["MV Cable Efficiency [%]:"]
    params["PCS Efficiency [%]:"] = ppm_phase["MV Cable Efficiency [%]:"]
    params["LV Cable Efficiency [%]:"] = ppm_phase["LV Cable Efficiency [%]:"]
    params["DC Cable Efficiency [%]:"] = ppm_phase["DC Cable Efficiency [%]:"]

    params["eta_trafo"] = params["MV/HV Transformer Efficiency[%]:"]    # 高压 变压器效率
    params["eta_cable"] = params["HV Losses up to DP[%]:"]              # 高压 电缆效率

    # 3 保存所有的参数 > A B C 都是不一样的 可以注释，节省时间
    utils_save_params_to_yaml(params, f"所有参数_{params['Phase_name']}.txt")

    # 读取光伏表格 所在的文件 ，以及结果存放的excel
    output_folder = input_folder.replace("原始数据",'结果数据')  # 文件夹名字更改，存放位置到结果数据

    # 判断是否存在文件夹，不存在，则新建
    utils_ensure_folder(output_folder)

    # 提取初始值，作为后续参数更新 subAux 即 变电站辅助功率常数 MW 即 Common Infrastructure Aux Power[MW]
    init_param = {'soc': 0, 'subAux': params['subAux']}
    all_year_raw_dfs = []

    # 读取所有文件名称
    input_folder_files = sorted(os.listdir(input_folder))

    # 文件的个数
    input_folder_files_number = len(input_folder_files)
    if input_folder_files_number == 0:
        print(f"{phase_name} 输入目录没有可计算文件。")
        return

    # 注意默认，表格都是按顺序排好的 从1到25这样的，如果有变化，根据需要进行更改
    for ids, file_name in enumerate(input_folder_files):
        print(f"{phase_name}， 第{ids+1}年的数据 ")
        start_year = time.time()  # 结束时间

        # ids 是 索引，表示是第几个表 ，ids=0,表示第一年的数据，file_name是第一年文件名称
        if ids < input_folder_files_number-2:
            file_path_next = os.path.join(input_folder, input_folder_files[ids + 1])  # 第二年的文件数据
        else:
            file_path_next = None
        params['file_path_next'] = file_path_next

        # output_path = os.path.join(output_folder, file_name) # 重新保存的文件 全路径

        params['ids'] = {ids:file_name}  # 记录下id数据，第几个文件
        params['ids_now'] = ids         # 记录下当前的ids数据，方便后面使用
        params['mark_year'] = ids+1


        # 不同年下的容量、电池效率、充放电效率，按 Phase 表的顺序读取
        params = update_param_from_phase_year(params, ids)
        # print(f'年份 {ids+1}  容量 {params["capacity"]}， 电池充电效率 {params["eta_ch"]}' )

        # 不同年下的 不同温度 IDLE_POINTS 值 即 Aux power idle MW
        # params = update_param_IDLE_POINTS(params,ids)
        params = update_param_IDLE_POINTS_list(params,ids)  # 增加对下一年的 数据的读取 最后一年就按当年的了

        # 读取下一年的0点的数据
        params['info'] = ''

        print(f' 充电 温度 {params["AuxPower_Points_charge"]["T_POINTS"]}' )
        print(f' 充电 功率 op  {params["AuxPower_Points_charge"]["OP_POINTS"]}' )
        print(f' 充电 功率 idle  {params["AuxPower_Points_charge"]["IDLE_POINTS"]}' )

        print(f' 放电 温度 {params["AuxPower_Points_discharge"]["T_POINTS"]}')
        print(f' 放电 功率 op  {params["AuxPower_Points_discharge"]["OP_POINTS"]}')
        print(f' 放电 功率 idle  {params["AuxPower_Points_discharge"]["IDLE_POINTS"]}')

        print('当年的容量：',params["capacity"] )
        print('读取光伏数据：',file_name)
        print('初始参数数据：',init_param)

        # 开始对一年的数据进行处理保存
        params['pv_rate'] = 0.99 # 光伏的效率系数

        # 初始值，第一个点，读取更新后的第一年的容量，后续的soc 都是读取结果后
        if ids==0:
            params['initSOC'] = params["capacity"] * 0.5  # 16.6793 #
            init_param['soc'] = params['initSOC']

        # init_param['soc'] = 320.1160237967535 # 用来测试最后一天的数据
        new_soc_init, df_year_raw = run_data_year(
            input_folder,
            output_folder,
            file_name,
            params,
            params['AuxPower_Points_charge']['T_POINTS'],
            params['AuxPower_Points_charge']['OP_POINTS'],
            params['AuxPower_Points_charge']['IDLE_POINTS'],
            params['AuxPower_Points_discharge']['T_POINTS'],
            params['AuxPower_Points_discharge']['OP_POINTS'],
            params['AuxPower_Points_discharge']['IDLE_POINTS'],
            params['hour_charge'],
            params['hour_discharge'],
            init_param,
            save_year_output=params["save_yearly_output"],
        )
        all_year_raw_dfs.append({
            "year_index": params['mark_year'],
            "file_name": file_name,
            "df": df_year_raw,
            "params": params.copy(),
        })

        """
        1）0点时刻，soc是50%，
        2）0点 此时读取光伏数据，计算负荷供电，得到 充放电供电的字段结果A
        3）那么就是0-1点，进行处理后的结果是A
        4）保存时，0点对应的字段，是A , 还是1点对应的字段是A?
        
        之前的计算，相当于
        0点，是0-1执行充放后的结果A, 所以，soc是50%经过0-1点放电之后的结果33%这样
        """

        init_param['soc'] = new_soc_init # 更新soc下一年的初始值
        end_year = time.time()  # 结束时间
        print(f"{phase_name} 执行时间: {end_year - start_year:.3f} 秒")

        print("===================== \n")
    #
    # =============================================================  完成循环后，进行表格生成
    print("开始对表格数据 进行拼接为一张大表 更改格式 ")
    if ids >= len(input_folder_files)-1 and params.get("save_final_workbook", True):
        # folder_path 是保存的结果数据 \Phase_A-27 years_260406 的地址
        # 注意 finally_folder 不要保存到 上面的文件里，
        # output_mul_folder_save(folder_path=output_folder,
        #                        output_file=finally_folder,params=params)
        save_all_year_raw_dfs_to_single_workbook(
            all_year_raw_dfs=all_year_raw_dfs,
            output_file=finally_folder,
            format_after_save=params["format_final_workbook"]
        )


def build_phase_params(phase_name, finally_folder):
    params = {
        "Phase_name": phase_name,
        "finally_folder": finally_folder,
        "save_yearly_output": True,
        "save_final_workbook": True,
        "format_final_workbook": True,
    }

    if '_A' in phase_name:
        params["pv_max_Discharge_cap"] = 660
        params["target_hv_power"] = 260
        params["maxPower"] = 338
        params['param_storage_supplement_year'] = [4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26]
        params['phase_soc_max'] = 1687
    elif '_B' in phase_name:
        params["pv_max_Discharge_cap"] = 1020
        params["target_hv_power"] = 570
        params["maxPower"] = 724.5
        params['param_storage_supplement_year'] = [4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26]
        params['phase_soc_max'] = 3653
    elif '_C' in phase_name:
        params["pv_max_Discharge_cap"] = 1020
        params["target_hv_power"] = 570
        params["maxPower"] = 710
        params['param_storage_supplement_year'] = [4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24]
        params['phase_soc_max'] = 3653

    return params


def run_Phase_ABC():
    # 定义各 Phase 信息
    # startfile = "/root/pyprojects/bess_shows"
    startfile = r"E:\bess_shows"
    data = 'PVsyst数据'

    phases = [
        ('Phase_A', os.path.join(startfile, data, "原始数据", "Phase_A-27 years_260406")),
        ('Phase_B', os.path.join(startfile, data, "原始数据", "Phase_B-26 years")),
        ('Phase_C', os.path.join(startfile, data, "原始数据", "Phase_C-25 years")),
    ]

    #  参数所在的文件位置
    params_file = R"E:\bess_shows\PVsyst数据\参数数据\DEWA7 - BESS_PPM Design Sheet -06-04-2026.xlsx"

    # params_file = os.path.join(startfile, data, "参数数据", "params.xlsx")

    params = {}
    for phase_name, input_folder in phases:
        print(f"--------------------------------- 开始执行 {phase_name} 数据 ----------------------------------------- ")
        start = time.time()  # 开始时间

        params['Phase_name'] = phase_name
        if '_A' in phase_name:
            params["subAux"] = 3  # 变电站辅助功率常数 MW === 之前写死的，后面表格读取
            params["pv_max_Discharge_cap"] = 660
            params["target_hv_power"] = 260  #  高压侧目标放电功率 MW A 是260
            params["maxPower"] = 338  # 最大充放电功率 MW
            # params['param_storage_supplement_year'] = [7, 12, 17, 22] # 没有用到，直接读取的容量，
            params['param_storage_supplement_year'] = [4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26] # 没有用到，直接读取的容量，
            params['phase_soc_max'] = 1687 # PhaseA：1687；PhaseB：3653；PhaseC：3653

        elif '_B' in phase_name:
            params["subAux"] = 4  # 变电站辅助功率常数 MW === 之前写死的，后面表格读取
            params["pv_max_Discharge_cap"] = 1020
            params["target_hv_power"] = 570  # 高压侧目标放电功率 MW A 是260
            params["maxPower"] = 724.5  # 最大充放电功率 MW
            # params['param_storage_supplement_year'] = [6, 11, 16, 21]
            params['param_storage_supplement_year'] = [4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26] # 没有用到，直接读取的容量，
            params['phase_soc_max'] = 3653 # PhaseA：1687；PhaseB：3653；PhaseC：3653


        elif '_C' in phase_name:
            params["subAux"] = 4  # 变电站辅助功率常数 MW === 之前写死的，后面表格读取
            params["pv_max_Discharge_cap"] = 1020
            params["target_hv_power"] = 570  #  高压侧目标放电功率 MW A 是260
            params["maxPower"] = 710  # 最大充放电功率 MW
            # params['param_storage_supplement_year'] = [5, 10, 15, 20]
            params['param_storage_supplement_year'] = [4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24]
            params['phase_soc_max'] = 3653 # PhaseA：1687；PhaseB：3653；PhaseC：3653

        else:
            pass

        # finally_folder = os.path.join(startfile, data, "结果数据", f"UAE_DEWA7_{phase_name}_PM_Output v1.0.xlsx")
        finally_folder = os.path.join(startfile, data, f"结果数据", f"UAE_DEWA7_{phase_name}_PM_Output v1.0.xlsx")
        params['finally_folder'] = finally_folder
        params['save_yearly_output'] = True
        params['save_final_workbook'] = True
        params['format_final_workbook'] = True  # 最后是否 格式更改，

        run_phase(params, input_folder, finally_folder)

        end = time.time()  # 结束时间
        print(f"{phase_name} 执行时间: {end - start:.3f} 秒")
        print(f"--------------------------------- 执行完成 {phase_name} 数据 ----------------------------------------- ")


start_year = time.time()  # 结束时间
run_Phase_ABC()
end_year = time.time()  # 结束时间
print(f" 所有代码执行时间: {end_year - start_year:.3f} 秒")
