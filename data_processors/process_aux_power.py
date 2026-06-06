import numpy as np
# T_POINTS = [0, 10, 20, 30, 40, 50, 55]   # 温度
# OP_POINTS = [2.34, 2.94, 3.56, 4.27, 4.7, 5.54, 5.92] # 储能系统正常工作时的辅助功率消耗
# IDLE_POINTS = [2.96, 1.81, 1.04, 1.4, 2.33, 3.61, 4.59] # 储能系统空闲待机时的辅助功率消耗

# 计算不同温度下返回的功率
def get_aux_power(temp, mode, T_POINTS, OP_POINTS, IDLE_POINTS, charge=False):
    """
    输入：
    temp → 当前环境温度（℃）
    mode → 模式字符串 "op" 或其它（表示储能系统是否在工作状态或待机状态）
    T_POINTS 温度
    OP_POINTS  运行时功率
    IDLE_POINTS 静止时功率
    输出：返回储能系统在该温度下的辅助功率（MW 或 kW，取决于数据单位） 边界值为功率值
    否则 = 左侧功率 + （温度-左侧温度）/(右侧温度-左侧文档） * （右侧功率-左侧功率）
    """
    # if charge is True:
    #     temp = 55 # 新增，现在是温度按照 固定55来计算

    tArr = T_POINTS
    opArr = OP_POINTS
    idleArr = IDLE_POINTS

    # 选择对应模式 op 或则 idle
    n = len(tArr) - 1

    # 转成浮点数，对应 VBA Val()
    tVals = [float(x) for x in tArr]
    opVals = [float(x) for x in opArr]
    idleVals = [float(x) for x in idleArr]

    # ---------------- 2. 边界处理 ----------------
    if temp <= tVals[0]:
        return opVals[0] if mode == "op" else idleVals[0]
    if temp >= tVals[n]:
        return opVals[n] if mode == "op" else idleVals[n]

    # ---------------- 3. 线性插值 ----------------
    for i in range(n):
        if tVals[i] <= temp <= tVals[i + 1]:
            ratio = (temp - tVals[i]) / (tVals[i + 1] - tVals[i])
            if mode == "op":
                return opVals[i] + ratio * (opVals[i + 1] - opVals[i])
            else:
                return idleVals[i] + ratio * (idleVals[i + 1] - idleVals[i])

    # 万一没匹配到，返回最后一个值（保险）
    return opVals[n] if mode == "op" else idleVals[n]



