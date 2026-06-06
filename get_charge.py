from get_charge_pvLess0 import charge_pv_negative
from get_charge_pvMore0_socMoreCapacity import charge_pv_positive_with_soc_full
from get_charge_pvMore0_socLessCapacity_plan import charge_pv_positive_with_soc_plan
from get_charge_pvMore0_socLessCapacity_notplan import charge_pv_positive_with_soc_notplan

from data_processors.process_aux_power import get_aux_power
from data_processors.process_daily_charge_plan import get_ComputeDailyChargePlan
def charge(currHour=None,
            needNewPlan=None,
            dayPV=None,
            soc=None,
            pv=None,
            temp=None,
            pvAuxDemand=None,
            capacity=None,
            maxPower=None,
            eta_ch=None,
            subAux=None,
            T_POINTS=None,
            OP_POINTS=None,
            IDLE_POINTS=None,
            chargePlan=None,
            params=None
           ):
    if pv<=0:
        result = charge_pv_negative( pv=pv,temp=temp,subAux=subAux,T_POINTS=T_POINTS,OP_POINTS=OP_POINTS,IDLE_POINTS=IDLE_POINTS,params=params)
    else:
        if soc>=capacity:
            result = charge_pv_positive_with_soc_full(pv=pv,soc=soc,capacity=capacity,temp=temp,
                                                      subAux=subAux,pvAuxDemand=pvAuxDemand,
                                                      T_POINTS=T_POINTS,OP_POINTS=OP_POINTS,IDLE_POINTS=IDLE_POINTS,params=params)
        else:
            """If Not needNewPlan And chargePlan(currHour) Then """
            if not needNewPlan and chargePlan[int(currHour)]:
                # print("not needNewPlan and chargePlan[int(currHour)]: ")
                result = charge_pv_positive_with_soc_plan(pv=pv,soc=soc,temp=temp,
                                                          capacity=capacity,eta_ch=eta_ch,
                                                          subAux=subAux,pvAuxDemand=pvAuxDemand,maxPower=maxPower,
                                                          T_POINTS=T_POINTS,OP_POINTS=OP_POINTS,IDLE_POINTS=IDLE_POINTS,params=params)
            else:

                result = charge_pv_positive_with_soc_notplan(pv=pv, temp=temp,
                                                             subAux=subAux, pvAuxDemand=pvAuxDemand,
                                                             T_POINTS=T_POINTS, OP_POINTS=OP_POINTS, IDLE_POINTS=IDLE_POINTS,params=params)
    # return result, chargePlan
    return result


