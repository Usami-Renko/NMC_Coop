import datetime 

def gen_timelines(start_ddate, end_ddate, fcst_step):
    dfcst_step  = datetime.timedelta(hours=fcst_step)
    work_time   = datetime.datetime.strptime(start_ddate, "%Y%m%d%H")
    timelines   = []
    
    while start_ddate <= end_ddate:
         timelines.append(start_ddate)
         work_time = work_time + dfcst_step
         start_ddate = datetime.datetime.strftime(work_time,"%Y%m%d%H")
                   
    return timelines
