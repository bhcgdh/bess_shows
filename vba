Option Explicit

' 温度查表数据（储能辅助功率）
Private Const T_POINTS As String = "0,10,20,30,40,50,55"
Private Const OP_POINTS As String = "2.34,2.94,3.56,4.27,4.70,5.54,5.92"
Private Const IDLE_POINTS As String = "2.96,1.81,1.04,1.40,2.33,3.61,4.59"

'-------------------------------------------------------------------------
' 主程序
'-------------------------------------------------------------------------
Sub MinimizeChargingTime_Advanced()
    Dim ws As Worksheet
    Set ws = ActiveSheet

    ' 获取光伏数据范围（D列）
    Dim lastRow As Long
    lastRow = ws.Cells(ws.Rows.Count, "D").End(xlUp).Row
    If lastRow < 2 Then
        MsgBox "D列（光伏出力）没有数据！"
        Exit Sub
    End If

    ' 用户输入参数
    Dim capacity As Double, maxPower As Double, subAux As Double
    On Error Resume Next
    capacity = InputBox("请输入储能容量（单位：MWh）", "储能参数", 100)
    If capacity <= 0 Then Exit Sub
    maxPower = InputBox("请输入最大充放电功率（单位：MW）", "储能参数", 50)
    If maxPower <= 0 Then Exit Sub
    subAux = InputBox("请输入变电站辅助功率常数（单位：MW）", "储能参数", 0.5)
    If subAux < 0 Then subAux = 0
    On Error GoTo 0

    ' 常数
    Const eta_ch As Double = 0.9325   ' 充电效率
    Const eta_dis As Double = 0.9747  ' 放电效率
    Const target_hv_power As Double = 260   ' 高压侧目标放电功率 (MW)
    Const eta_trafo As Double = 0.995       ' 高压变压器效率
    Const eta_cable As Double = 0.99        ' 高压电缆效率

    ' 初始SOC固定为容量50%
    Dim initSOC As Double
    initSOC = capacity * 0.5

    ' 读取输入数据（A列日期，B列时间，C列温度，D列光伏）
    Dim data() As Variant
    data = ws.Range("A2:D" & lastRow).Value
    Dim n As Long
    n = UBound(data, 1)

    ' 建立字典：按日期存储全天24小时的光伏出力 和 温度
    Dim dictPV As Object, dictTemp As Object
    Set dictPV = CreateObject("Scripting.Dictionary")
    Set dictTemp = CreateObject("Scripting.Dictionary")

    Dim i As Long, j As Integer, currDate As Date, currHour As Integer
    For i = 1 To n
        currDate = data(i, 1)
        currHour = Hour(data(i, 2))
        If currHour >= 0 And currHour <= 23 Then
            ' 存储光伏
            If Not dictPV.exists(currDate) Then
                Dim arrPV(0 To 23) As Double
                dictPV.Add currDate, arrPV
            End If
            Dim tmpPV() As Double
            tmpPV = dictPV(currDate)
            tmpPV(currHour) = data(i, 4)
            dictPV(currDate) = tmpPV
            ' 存储温度
            If Not dictTemp.exists(currDate) Then
                Dim arrTemp(0 To 23) As Double
                dictTemp.Add currDate, arrTemp
            End If
            Dim tmpTemp() As Double
            tmpTemp = dictTemp(currDate)
            tmpTemp(currHour) = data(i, 3)
            dictTemp(currDate) = tmpTemp
        End If
    Next i

    ' 设置输出列标题（F~W列）
    ws.Range("F1").Value = "SOC/%"
    ws.Range("G1").Value = "BESS Auxiliary Power [MW]"
    ws.Range("H1").Value = "Common Infrastructure Aux Power[MW]"
    ws.Range("I1").Value = "PV Power To Plant Substation BCP [MW]"
    ws.Range("J1").Value = "BESS Power To Plant Substation BCP [MW]"
    ws.Range("K1").Value = "Mode"
    ws.Range("L1").Value = "PV Power to BESS Plant BCP  [MW]"
    ws.Range("M1").Value = "DisCharge Power BCP [MW]"
    ws.Range("N1").Value = "PV Power To BESS plant aux consumuer [MW]"
    ws.Range("O1").Value = "PV Power To Common Infrastructure Power [MW] "
    ws.Range("P1").Value = "Charge Power [DC]"
    ws.Range("Q1").Value = "Discharge Power [DC]"
    ws.Range("R1").Value = "BESS Power To BESS plant aux consumuer [MW]"
    ws.Range("S1").Value = "BESS plant Power To Common Infrastructure Power [MW]"
    ws.Range("T1").Value = "Imported Power [MW]"
    ws.Range("U1").Value = "BESS Power To PV Plant [MW]"
    ws.Range("V1").Value = "Energy [DC]"
    ws.Range("W1").Value = "Exported Power [MW]"

    ' 初始化SOC
    Dim soc As Double
    soc = initSOC
    Debug.Print "初始SOC = " & soc & " MWh (" & Round(soc / capacity * 100, 1) & "%)"

    ' 初始化日期跟踪和充电计划
    Dim lastDate As Date
    lastDate = data(1, 1)
    Dim dayPV() As Double, dayTemp() As Double
    If dictPV.exists(lastDate) Then
        dayPV = dictPV(lastDate)
    Else
        ReDim dayPV(0 To 23)
        For j = 0 To 23
            dayPV(j) = 0
        Next
    End If
    If dictTemp.exists(lastDate) Then
        dayTemp = dictTemp(lastDate)
    Else
        ReDim dayTemp(0 To 23)
        For j = 0 To 23
            dayTemp(j) = 0
        Next
    End If

    Dim chargePlan() As Boolean
    Dim needNewPlan As Boolean
    needNewPlan = True   ' 需要计算新计划

    ' 主循环
    For i = 1 To n
        currDate = data(i, 1)
        currHour = Hour(data(i, 2))
        Dim pv As Double
        pv = data(i, 4)
        Dim temp As Double
        temp = data(i, 3)

        ' 检查是否新的一天
        If currDate <> lastDate Then
            lastDate = currDate
            If dictPV.exists(currDate) Then
                dayPV = dictPV(currDate)
            Else
                ReDim dayPV(0 To 23)
                For j = 0 To 23
                    dayPV(j) = 0
                Next
            End If
            If dictTemp.exists(currDate) Then
                dayTemp = dictTemp(currDate)
            Else
                ReDim dayTemp(0 To 23)
                For j = 0 To 23
                    dayTemp(j) = 0
                Next
            End If
            needNewPlan = True   ' 新的一天，需要重新计算计划（但要在凌晨放电后）
        End If

        ' 判断是否为放电时段（19:00-01:00）
        Dim isDischarge As Boolean
        isDischarge = (currHour >= 19) Or (currHour = 0)

        ' 计算光伏夜间辅助需求（光伏负值表示消耗）
        Dim pvAuxDemand As Double
        pvAuxDemand = -pv
        If pvAuxDemand < 0 Then pvAuxDemand = 0

        ' 本小时变量
        Dim Pin_ac As Double, Pdis_ac As Double       ' 中压侧充放电功率
        Dim Pin_dc As Double, Pdis_dc As Double       ' 直流侧充放电功率
        Dim pv2grid As Double, storage2grid As Double
        Dim state As String
        Dim pv_to_storage As Double, pv_to_sub As Double
        Dim bat_to_storage As Double, bat_to_sub As Double, bat_to_pv As Double
        Dim grid_to_storage As Double, grid_to_sub As Double, grid_to_pv As Double
        Dim grid_power As Double
        Dim aux_storage As Double, aux_total As Double
        Dim hv_power As Double

        ' 调试输出基本信息
        Debug.Print "行 " & i + 1 & ": 日期=" & currDate & ", 小时=" & currHour & ", 光伏=" & Round(pv, 2) & ", 温度=" & temp & ", SOC=" & Round(soc / capacity, 3)

        ' ---------- 放电时段处理 ----------
If isDischarge Then
    ' 计算所需上网功率（中压侧）以实现高压侧260MW
    Dim target_grid_ac As Double
    target_grid_ac = target_hv_power / (eta_trafo * eta_cable)

    ' 总辅助需求
    aux_storage = GetAuxPower(temp, "op")
    aux_total = aux_storage + subAux + pvAuxDemand

    ' 所需放电功率 = 上网目标 + 辅助需求
    Dim required_discharge As Double
    required_discharge = target_grid_ac + aux_total

    ' 实际放电功率受限于最大功率和SOC
    Dim max_discharge_ac As Double
    max_discharge_ac = Application.WorksheetFunction.Min(maxPower, soc * eta_dis)
    Pdis_ac = Application.WorksheetFunction.Min(required_discharge, max_discharge_ac)

    If Pdis_ac >= aux_total Then
        ' 成功放电，上网功率 = 放电功率 - 辅助
        state = "Discharge"
        bat_to_storage = aux_storage
        bat_to_sub = subAux
        bat_to_pv = pvAuxDemand
        pv_to_storage = 0: pv_to_sub = 0
        grid_to_storage = 0: grid_to_sub = 0: grid_to_pv = 0
        grid_power = 0

        storage2grid = Pdis_ac - aux_total
        pv2grid = Application.WorksheetFunction.Max(0, pv)
        Pin_ac = 0
        Pin_dc = 0
        Pdis_dc = Pdis_ac / eta_dis
    Else
        ' 放电功率不足，不放电，转为空闲
        state = "Standby"
        aux_storage = GetAuxPower(temp, "idle")
        aux_total = aux_storage + subAux + pvAuxDemand
        bat_to_storage = 0: bat_to_sub = 0: bat_to_pv = 0
        pv_to_storage = 0: pv_to_sub = 0
        grid_to_storage = aux_storage
        grid_to_sub = subAux
        grid_to_pv = pvAuxDemand
        grid_power = aux_total
        Pdis_ac = 0
        storage2grid = 0
        pv2grid = Application.WorksheetFunction.Max(0, pv)
        Pin_ac = 0: Pin_dc = 0: Pdis_dc = 0
    End If

        ' ---------- 非放电时段处理 ----------
        Else
            ' 如果是凌晨2点及以后，且需要新计划，则计算充电计划（基于当前SOC和净光伏）
            If needNewPlan And currHour >= 2 Then
                chargePlan = ComputeDailyChargePlan(dayPV, dayTemp, soc, capacity, maxPower, eta_ch, subAux)
                needNewPlan = False
                Debug.Print "  在小时 " & currHour & " 重新计算充电计划"
            End If

            If pv <= 0 Then
                ' 光伏无出力或为负：空闲，辅助由电网提供
                state = "Standby"
                aux_storage = GetAuxPower(temp, "idle")
                aux_total = aux_storage + subAux + pvAuxDemand
                pv_to_storage = 0: pv_to_sub = 0
                bat_to_storage = 0: bat_to_sub = 0: bat_to_pv = 0
                grid_to_storage = aux_storage
                grid_to_sub = subAux
                grid_to_pv = pvAuxDemand
                grid_power = aux_total
                pv2grid = 0
                storage2grid = 0
                Pin_ac = 0: Pdis_ac = 0: Pin_dc = 0: Pdis_dc = 0
            Else
                ' 光伏有正出力
                If soc >= capacity Then
                    ' 储能已满，不充电，空闲
                    state = "Standby"
                    aux_storage = GetAuxPower(temp, "idle")
                    aux_total = aux_storage + subAux + pvAuxDemand
                    If pv >= aux_total Then
                        ' 光伏足够覆盖所有辅助
                        pv_to_storage = aux_storage
                        pv_to_sub = subAux
                        bat_to_storage = 0: bat_to_sub = 0: bat_to_pv = 0
                        grid_to_storage = 0: grid_to_sub = 0: grid_to_pv = 0
                        grid_power = 0
                        pv2grid = pv - aux_total
                    Else
                        ' 光伏不足以覆盖，不足部分由电网提供
                        pv_to_storage = aux_storage * (pv / aux_total)
                        pv_to_sub = subAux * (pv / aux_total)
                        Dim pv_to_pv As Double
                        pv_to_pv = pvAuxDemand * (pv / aux_total)
                        bat_to_storage = 0: bat_to_sub = 0: bat_to_pv = 0
                        grid_to_storage = aux_storage - pv_to_storage
                        grid_to_sub = subAux - pv_to_sub
                        grid_to_pv = pvAuxDemand - pv_to_pv
                        grid_power = aux_total - pv
                        pv2grid = 0
                    End If
                    storage2grid = 0
                    Pin_ac = 0: Pdis_ac = 0: Pin_dc = 0: Pdis_dc = 0
                Else
                    ' 需要决定是否充电
                    If Not needNewPlan And chargePlan(currHour) Then
                        ' 计划充电
                        ' 先确定辅助模式为 op（充电时）
                        aux_storage = GetAuxPower(temp, "op")
                        aux_total = aux_storage + subAux + pvAuxDemand
                        Dim remCap As Double
                        remCap = capacity - soc
                        ' 最大可充电功率（中压侧）
                        Dim maxPin As Double
                        maxPin = Application.WorksheetFunction.Min(maxPower, remCap / eta_ch)
                        ' 光伏首先要满足辅助，剩余用于充电
                        If pv >= aux_total Then
                            ' 光伏充足
                            Pin_ac = Application.WorksheetFunction.Min(pv - aux_total, maxPin)
                            If Pin_ac > 0 Then
                                state = "Charging"
                                ' 充电成功，辅助全部由光伏提供
                                pv_to_storage = aux_storage
                                pv_to_sub = subAux
                                ' 光伏给光伏辅助（pvAuxDemand 由光伏自身提供）
                                pv_to_pv = pvAuxDemand
                                bat_to_storage = 0: bat_to_sub = 0: bat_to_pv = 0
                                grid_to_storage = 0: grid_to_sub = 0: grid_to_pv = 0
                                grid_power = 0
                                ' 更新SOC
                                soc = soc + Pin_ac * eta_ch
                                pv2grid = pv - aux_total - Pin_ac
                                storage2grid = 0
                                Pin_dc = Pin_ac * eta_ch
                                Pdis_ac = 0: Pdis_dc = 0
                            Else
                                ' 虽然光伏充足，但受限于功率或剩余容量，无法充电，视为空闲
                                state = "Standby"
                                ' 辅助仍由光伏提供（因为光伏充足）
                                pv_to_storage = aux_storage
                                pv_to_sub = subAux
                                pv_to_pv = pvAuxDemand
                                bat_to_storage = 0: bat_to_sub = 0: bat_to_pv = 0
                                grid_to_storage = 0: grid_to_sub = 0: grid_to_pv = 0
                                grid_power = 0
                                pv2grid = pv - aux_total
                                Pin_ac = 0: Pin_dc = 0
                            End If
                        Else
                            ' 光伏不足以覆盖辅助，无法充电，空闲
                            state = "Standby"
                            ' 辅助由光伏和电网共同提供
                            pv_to_storage = aux_storage * (pv / aux_total)
                            pv_to_sub = subAux * (pv / aux_total)
                            pv_to_pv = pvAuxDemand * (pv / aux_total)
                            bat_to_storage = 0: bat_to_sub = 0: bat_to_pv = 0
                            grid_to_storage = aux_storage - pv_to_storage
                            grid_to_sub = subAux - pv_to_sub
                            grid_to_pv = pvAuxDemand - pv_to_pv
                            grid_power = aux_total - pv
                            pv2grid = 0
                            Pin_ac = 0: Pin_dc = 0
                        End If
                    Else
                        ' 不在计划中，不充电，空闲
                        state = "Standby"
                        aux_storage = GetAuxPower(temp, "idle")
                        aux_total = aux_storage + subAux + pvAuxDemand
                        If pv >= aux_total Then
                            pv_to_storage = aux_storage
                            pv_to_sub = subAux
                            pv_to_pv = pvAuxDemand
                            bat_to_storage = 0: bat_to_sub = 0: bat_to_pv = 0
                            grid_to_storage = 0: grid_to_sub = 0: grid_to_pv = 0
                            grid_power = 0
                            pv2grid = pv - aux_total
                        Else
                            pv_to_storage = aux_storage * (pv / aux_total)
                            pv_to_sub = subAux * (pv / aux_total)
                            pv_to_pv = pvAuxDemand * (pv / aux_total)
                            bat_to_storage = 0: bat_to_sub = 0: bat_to_pv = 0
                            grid_to_storage = aux_storage - pv_to_storage
                            grid_to_sub = subAux - pv_to_sub
                            grid_to_pv = pvAuxDemand - pv_to_pv
                            grid_power = aux_total - pv
                            pv2grid = 0
                        End If
                        storage2grid = 0
                        Pin_ac = 0: Pdis_acPdis_ac = 0: Pin_dc = 0: Pdis_dc = 0
                    End If
                End If
            End If
        End If

        ' 计算高压侧功率
        hv_power = (pv2grid + storage2grid) * eta_trafo * eta_cable
        If hv_power < 0 Then hv_power = 0

        ' 输出到工作表（注意行偏移：第i行数据对应第i+1行输出）
        ws.Cells(i + 1, "F").Value = soc / capacity
        ws.Cells(i + 1, "G").Value = aux_storage
        ws.Cells(i + 1, "H").Value = subAux
        ws.Cells(i + 1, "I").Value = pv2grid
        ws.Cells(i + 1, "J").Value = storage2grid
        ws.Cells(i + 1, "K").Value = state
        ws.Cells(i + 1, "L").Value = Pin_ac
        ws.Cells(i + 1, "M").Value = Pdis_ac
        ws.Cells(i + 1, "N").Value = pv_to_storage
        ws.Cells(i + 1, "O").Value = pv_to_sub
        ws.Cells(i + 1, "P").Value = Pin_dc
        ws.Cells(i + 1, "Q").Value = Pdis_dc
        ws.Cells(i + 1, "R").Value = bat_to_storage
        ws.Cells(i + 1, "S").Value = bat_to_sub
        ws.Cells(i + 1, "T").Value = grid_power
        ws.Cells(i + 1, "U").Value = bat_to_pv
        ws.Cells(i + 1, "V").Value = soc
        ws.Cells(i + 1, "W").Value = hv_power
    Next i

    MsgBox "计算完成！"
End Sub

'-------------------------------------------------------------------------
' 计算当天充电计划：基于净光伏（光伏 - op辅助 - 变电站辅助）
' 输入：dayPV - 当天24小时光伏数组，dayTemp - 当天24小时温度数组，
'       startSOC - 当天起始SOC，capacity - 容量，maxPower - 最大功率，
'       eta_ch - 充电效率，subAux - 变电站辅助
'-------------------------------------------------------------------------
Function ComputeDailyChargePlan(dayPV() As Double, dayTemp() As Double, startSOC As Double, capacity As Double, maxPower As Double, eta_ch As Double, subAux As Double) As Boolean()
    Dim plan(0 To 23) As Boolean
    Dim i As Integer, j As Integer

    ' 计算每个小时的净光伏（光伏 - 储能运行状态辅助功率 - 变电站辅助）
    Dim netPV(0 To 23) As Double
    For i = 0 To 23
        Dim pv_i As Double
        pv_i = dayPV(i)
        ' 获取该小时的运行状态辅助功率（op）
        Dim temp_i As Double
        temp_i = dayTemp(i)
        Dim aux_op As Double
        aux_op = GetAuxPower(temp_i, "op")
        netPV(i) = pv_i - aux_op - subAux
        If netPV(i) < 0 Then netPV(i) = 0
    Next i

    Dim remaining As Double
    remaining = capacity - startSOC
    Debug.Print "计算充电计划: 起始SOC=" & Round(startSOC, 2) & ", 剩余容量=" & Round(remaining, 2)

    If remaining <= 0 Then
        For i = 0 To 23
            plan(i) = False
        Next
        ComputeDailyChargePlan = plan
        Exit Function
    End If

    ' 创建索引-净光伏值对
    Dim hours() As Variant
    ReDim hours(0 To 23, 0 To 1)
    For i = 0 To 23
        hours(i, 0) = i
        hours(i, 1) = netPV(i)
    Next

    ' 降序排序
    For i = 0 To 22
        For j = i + 1 To 23
            If hours(i, 1) < hours(j, 1) Then
                Dim tmpIdx As Integer, tmpVal As Double
                tmpIdx = hours(i, 0)
                tmpVal = hours(i, 1)
                hours(i, 0) = hours(j, 0)
                hours(i, 1) = hours(j, 1)
                hours(j, 0) = tmpIdx
                hours(j, 1) = tmpVal
            End If
        Next j
    Next i

    ' 累加充电能量（考虑最大功率限制和效率）
    Dim charged As Double
    charged = 0
    For i = 0 To 23
        If charged >= remaining - 0.001 Then Exit For
        Dim net_i As Double
        net_i = hours(i, 1)
        If net_i > 0 Then
            Dim chargeEnergy As Double
            chargeEnergy = Application.WorksheetFunction.Min(net_i, maxPower) * eta_ch
            Dim need As Double
            need = remaining - charged
            If chargeEnergy >= need Then
                charged = remaining
            Else
                charged = charged + chargeEnergy
            End If
            plan(hours(i, 0)) = True
            Debug.Print "  选中小时 " & hours(i, 0) & " (净光伏=" & Round(net_i, 2) & "), 可充电量=" & Round(chargeEnergy, 2) & ", 累计=" & Round(charged, 2)
        End If
    Next i

    ' 输出最终计划
    Dim planStr As String
    planStr = "充电计划小时: "
    For i = 0 To 23
        If plan(i) Then planStr = planStr & i & " "
    Next i
    Debug.Print planStr

    ComputeDailyChargePlan = plan
End Function

'-------------------------------------------------------------------------
' 统计True个数
'-------------------------------------------------------------------------
Function CountTrue(arr() As Boolean) As Integer
    Dim cnt As Integer, i As Integer
    cnt = 0
    For i = LBound(arr) To UBound(arr)
        If arr(i) Then cnt = cnt + 1
    Next i
    CountTrue = cnt
End Function

'-------------------------------------------------------------------------
' 获取储能辅助功率（线性插值）
'-------------------------------------------------------------------------
Function GetAuxPower(temp As Double, mode As String) As Double
    Dim tArr() As String, opArr() As String, idleArr() As String
    tArr = Split(T_POINTS, ",")
    opArr = Split(OP_POINTS, ",")
    idleArr = Split(IDLE_POINTS, ",")

    Dim n As Integer
    n = UBound(tArr)

    Dim tVals() As Double, opVals() As Double, idleVals() As Double
    ReDim tVals(n)
    ReDim opVals(n)
    ReDim idleVals(n)

    Dim i As Integer
    For i = 0 To n
        tVals(i) = Val(tArr(i))
        opVals(i) = Val(opArr(i))
        idleVals(i) = Val(idleArr(i))
    Next i

    ' 边界处理
    If temp <= tVals(0) Then
        If mode = "op" Then GetAuxPower = opVals(0) Else GetAuxPower = idleVals(0)
        Exit Function
    End If
    If temp >= tVals(n) Then
        If mode = "op" Then GetAuxPower = opVals(n) Else GetAuxPower = idleVals(n)
        Exit Function
    End If

    ' 线性插值
    For i = 0 To n - 1
        If temp >= tVals(i) And temp <= tVals(i + 1) Then
            Dim ratio As Double
            ratio = (temp - tVals(i)) / (tVals(i + 1) - tVals(i))
            If mode = "op" Then
                GetAuxPower = opVals(i) + ratio * (opVals(i + 1) - opVals(i))
            Else
                GetAuxPower = idleVals(i) + ratio * (idleVals(i + 1) - idleVals(i))
            End If
            Exit Function
        End If
    Next i
End Function
