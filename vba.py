"""
文件: vba.py
作者: chang xiao
创建日期: 2026-04-06
功能: TODO: 填写功能描述
"""

T_POINTS = [0, 10, 20, 30, 40, 50, 55]   # 温度
OP_POINTS = [2.34, 2.94, 3.56, 4.27, 4.7, 5.54, 5.92] # 储能系统正常工作时的辅助功率消耗
IDLE_POINTS = [2.96, 1.81, 1.04, 1.4, 2.33, 3.61, 4.59] # 储能系统空闲待机时的辅助功率消耗

hour_charge = [1,2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]    # 充电时间
hour_discharge = [0, 19, 20, 21, 22, 23]  # 放电时间段 判断是否为放电时段（19:00-01:00）

# 效率参数
params = {"eta_ch": 0.9325,       # 充电效率
          "eta_dis": 0.9747,      # 放电效率
          "target_hv_power": 260, # 高压侧目标放电功率 MW
          "eta_trafo": 0.995,     # 高压变压器效率
          "eta_cable": 0.99       # 高压电缆效率
        }
# 输入参数，一定大于0，否则不进行计算
params["capacity"] = 1687   # 储能容量 MWh
params["maxPower"] = 338  # 最大充放电功率 MW
params["subAux"] = 3     # 变电站辅助功率常数 MW

# 储能初始值 默认设置
# initSOC = params['capacity'] * 0.5
initSOC = params["capacity"] * 0.335  # 16.6793

# 储能初始比例值
soc_init = f"{round(100 * initSOC / params['capacity'],1)}%" # 初始的soc值,比率值
# soc_init =16.6793