class SETTINGS:

    fan = {'fan1':'off','fan2':'off'}
    uv = 'off'
    led={1:{'act':'X', 'sts':'off','on_at':'12:00','off_at':'12:01'},
        2:{'act':'X', 'sts':'off','on_at':'12:00','off_at':'12:01'},
        3:{'act':'X', 'sts':'off','on_at':'12:00','off_at':'12:01'},
        4:{'act':'X', 'sts':'off','on_at':'12:00','off_at':'12:01'},
        5:{'act':'X', 'sts':'off','on_at':'12:00','off_at':'12:01'},
        6:{'act':'X', 'sts':'off','on_at':'12:00','off_at':'12:01'},
        7:{'act':'X', 'sts':'off','on_at':'12:00','off_at':'12:01'},
        8:{'act':'X', 'sts':'off','on_at':'12:00','off_at':'12:01'}}
    tds = {'low' : 0, 'high':2000}
    ph = {'low':0.0, 'hih':14.0}
    nut = {'sts':'off','volume':0, 'ratio':0}
    nut_freq = 1
    nut_time = 10
    sens_freq=10
    sens_unit='s'
    serv_freq=10
    serv_unit='s'
    serv_add='127.0.0.1'
    serv_port='8080'


class SF1:
    DayData_dict = {'CO2' : [0 for i in range(48)], 'LUX' : [1 for i in range(48)],
                    'INTMP':[2 for i in range(48)],'INHUMID':[3 for i in range(48)],'TIME':['' for i in range(48)]}
    WeekData_dict = {'CO2' : [0 for i in range(48)], 'LUX' : [1 for i in range(48)],
                    'INTMP':[2 for i in range(48)],'INHUMID':[3 for i in range(48)],'TIME':['' for i in range(48)]}
    MonthData_dict =  {'CO2' : [0 for i in range(48)],'LUX':[1 for i in range(48)],
                        'INTMP':[2 for i in range(48)],'INHUMID':[3 for i in range(48)],'TIME':['' for i in range(48)]}  

class SF2:
    DayData_dict = {'CO2' : [0 for i in range(48)], 'LUX' : [1 for i in range(48)],
                    'INTMP':[2 for i in range(48)],'INHUMID':[3 for i in range(48)],'TIME':['' for i in range(48)]}
    WeekData_dict = {'CO2' : [0 for i in range(48)], 'LUX' : [1 for i in range(48)],
                    'INTMP':[2 for i in range(48)],'INHUMID':[3 for i in range(48)],'TIME':['' for i in range(48)]}
    MonthData_dict =  {'CO2' : [0 for i in range(48)],'LUX':[1 for i in range(48)],
                        'INTMP':[2 for i in range(48)],'INHUMID':[3 for i in range(48)],'TIME':['' for i in range(48)]}  
class SF3:
    DayData_dict = {'CO2' : [0 for i in range(48)], 'LUX' : [1 for i in range(48)],
                    'INTMP':[2 for i in range(48)],'INHUMID':[3 for i in range(48)],'TIME':['' for i in range(48)]}
    WeekData_dict = {'CO2' : [0 for i in range(48)], 'LUX' : [1 for i in range(48)],
                    'INTMP':[2 for i in range(48)],'INHUMID':[3 for i in range(48)],'TIME':['' for i in range(48)]}
    MonthData_dict =  {'CO2' : [0 for i in range(48)],'LUX':[1 for i in range(48)],
                        'INTMP':[2 for i in range(48)],'INHUMID':[3 for i in range(48)],'TIME':['' for i in range(48)]}  

class SF4:
    DayData_dict = {'CO2' : [0 for i in range(48)], 'LUX' : [1 for i in range(48)],
                    'INTMP':[2 for i in range(48)],'INHUMID':[3 for i in range(48)],'TIME':['' for i in range(48)]}
    WeekData_dict = {'CO2' : [0 for i in range(48)], 'LUX' : [1 for i in range(48)],
                    'INTMP':[2 for i in range(48)],'INHUMID':[3 for i in range(48)],'TIME':['' for i in range(48)]}
    MonthData_dict =  {'CO2' : [0 for i in range(48)],'LUX':[1 for i in range(48)],
                        'INTMP':[2 for i in range(48)],'INHUMID':[3 for i in range(48)],'TIME':['' for i in range(48)]}  
class SF5:
    DayData_dict = {'CO2' : [0 for i in range(48)], 'LUX' : [1 for i in range(48)],
                    'INTMP':[2 for i in range(48)],'INHUMID':[3 for i in range(48)],'TIME':['' for i in range(48)]}
    WeekData_dict = {'CO2' : [0 for i in range(48)], 'LUX' : [1 for i in range(48)],
                    'INTMP':[2 for i in range(48)],'INHUMID':[3 for i in range(48)],'TIME':['' for i in range(48)]}
    MonthData_dict =  {'CO2' : [0 for i in range(48)],'LUX':[1 for i in range(48)],
                        'INTMP':[2 for i in range(48)],'INHUMID':[3 for i in range(48)],'TIME':['' for i in range(48)]}  

class SENSOR:
    Data_dict = {'TMP':0,'DO' : 0, 'PH' : 0,'TDS':0}
    DayData_dict = {'ELECTRON' : [0 for i in range(48)],'TIME':['' for i in range(48)]}
    WeekData_dict = {'ELECTRON' : [0 for i in range(48)], 'TIME':['' for i in range(48)]}
    MonthData_dict =  {'ELECTRON' : [0 for i in range(48)],'TIME':['' for i in range(48)]}  
    ELECTRON_dict = {'1h':0, '1d':0, '1w':0, '1m':0}
    
sfDef_list = [SF1, SF2, SF3, SF4, SF5]


