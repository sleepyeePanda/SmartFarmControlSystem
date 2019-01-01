from monitoring_gui import *
from DEF import *
from StyleSheet import *
from DB import *
import PyQt5
import pyqtgraph as pg
import serial
import asyncio
import serial_asyncio
from threading import Thread
import time
import datetime
import json
from functools import partial
import sqlite3
import glob
import os

class DBInsertManager(PyQt5.QtCore.QThread):
    
    def __init__(self):
        super().__init__()
        try:
            self.get_connection()
        except Exception as e:
            print(str(e))
            return
        for index in range(1,6):
            self.fetchSFDayData(index)
        self.fetchWATERStatData()
        self.fetchELECDayData()
        self.fetchELEC_StatData()
        self.start()

    def get_connection(self):
        #sqlite Connection 연결
        self.connection = sqlite3.connect('test.db')

    def fetchSFDayData(self, sfID):
        if self.connection:
            cursor = self.connection.cursor()
            cursor.execute(FETCH_SF_query,(sfID,))
            rows = cursor.fetchall()
            if rows:
                for k,v in { 0 : 'CO2', 1: 'LUX', 2:'INTMP',3:'INHUMID'}.items():
                    data_list = [row[k] for row in rows]
                    data_list.reverse()
                    for i in range(len(data_list)):
                        sfDef_list[sfID-1].DayData_dict[v].append(data_list[i])
                        sfDef_list[sfID-1].DayData_dict[v].pop(0)
                time_list = [row[4][-8:] for row in rows]
                time_list.reverse()
                for i in range(len(time_list)):
                    sfDef_list[sfID-1].DayData_dict['TIME'].append(time_list[i])
                    sfDef_list[sfID-1].DayData_dict['TIME'].pop(0)
               
    def fetchELECDayData(self):
        if self.connection:
            cursor = self.connection.cursor()
            cursor.execute(FETCH_ELEC_query,('electron',))
            rows = cursor.fetchall()
            if rows:
                data_list = [row[0] for row in rows]
                data_list.reverse()
                for i in range(len(data_list)):
                    SENSOR.DayData_dict['ELECTRON'].append(data_list[i])      
                    SENSOR.DayData_dict['ELECTRON'].pop(0)
                time_list = [row[1][-8:] for row in rows]
                time_list.reverse()
                for i in range(len(time_list)):
                    SENSOR.DayData_dict['TIME'].append(time_list[i])
                    SENSOR.DayData_dict['TIME'].pop(0)

    def fetchWATERStatData(self):
        if self.connection:
            cursor = self.connection.cursor()
            cursor.execute(FETCH_WATER_query)
            rows = cursor.fetchmany(1)
            if rows:
                SENSOR.Data_dict['TMP'] = int(rows[0][0])
                SENSOR.Data_dict['TDS'] = int(rows[0][1])
                SENSOR.Data_dict['PH'] = int(rows[0][2])
                SENSOR.Data_dict['DO'] = int(rows[0][3])

    def fetchELEC_StatData(self):
        if self.connection:
            cursor = self.connection.cursor()
            cursor.execute(FETCH_ELEC_query_byHour)
            SENSOR.ELECTRON_dict['1h'] = cursor.fetchall()[0][0]
            cursor.execute(FETCH_ELEC_query_byDay) 
            SENSOR.ELECTRON_dict['1d'] =  cursor.fetchall()[0][0]         
            cursor.execute(FETCH_ELEC_query_byWeek)
            SENSOR.ELECTRON_dict['1w'] = cursor.fetchall()[0][0]
            cursor.execute(FETCH_ELEC_query_byMonth)
            SENSOR.ELECTRON_dict['1m'] = cursor.fetchall()[0][0]

    @PyQt5.QtCore.pyqtSlot(dict, str)
    def insertData(self, values, data):
        if self.connection:
            # Connection 으로부터 Cursor 생성
            # Array based cursor : return tuple after exectuing SQL 
            try:
                cursor = self.connection.cursor()
                if data == 'sf':
                    cursor.execute(INSERT_SF_query,(values['ID'],values['sfID'],values['CO2'],values['LUX'], values['INTMP'],values['INHUMID'], values['TIME']))
                    self.connection.commit()
                elif data == 'water':
                    cursor.execute(INSERT_SENSOR_query,(values['ID'], values['TMP'], values['DO'], values['PH'], values['TDS'], values['TIME']))
                    self.connection.commit()
                elif data == 'electron':
                    cursor.execute(INSERT_ELEC_query, (values['ID'], values['ELEC'], values['TIME']))
                    self.connection.commit()
            except Exception as e:
                print(str(e))

    def disconnect(self):
        #connection 닫기
        if self.connection:
            self.connection.close()
            print('inserting DB disconnected!')

class DBFetchManager(PyQt5.QtCore.QThread):
    fetchSFOldDataSignal = PyQt5.QtCore.pyqtSignal(bool, int)
    fetchElectronOldDataSignal = PyQt5.QtCore.pyqtSignal(bool)
    fetchElectronStatSignal = PyQt5.QtCore.pyqtSignal()
     
    def __init__(self, ui, eventThread):
        super().__init__()
        self.get_connection()
        for i in range(5):
            eventThread.radioButton_list[1][i].clicked.connect(partial(self.fetchSF_OldData,i+1,'week',sfDef_list[i].WeekData_dict))
            eventThread.radioButton_list[2][i].clicked.connect(partial(self.fetchSF_OldData,i+1,'month',sfDef_list[i].MonthData_dict))
        
        ui.elec_week.clicked.connect(partial(self.fetchELEC_OldData, 'week', SENSOR.WeekData_dict))
        ui.elec_month.clicked.connect(partial(self.fetchELEC_OldData, 'month', SENSOR.MonthData_dict))
        
        self.fetchSFOldDataSignal.connect(eventThread.updateSFPlot)
        self.fetchElectronOldDataSignal.connect(eventThread.updateELECPlot)
        self.fetchElectronStatSignal.connect(eventThread.updateELEC)
        
        self.timer = PyQt5.QtCore.QTimer()
        self.timer.timeout.connect(self.fetchELEC_StatData)
        self.timer.start(1000*60*60)
        self.start()

    def get_connection(self):
        try:
        # sqlite Connection 연결
            self.connection = sqlite3.connect('test.db')
        except Exception as e:
            print(str(e))
            return
    
    @PyQt5.QtCore.pyqtSlot(int, str, dict)
    def fetchSF_OldData(self, sfID, period, dictionary):
        if period == 'week':
            by = byWeek
            parameter = (sfID,)
        else :
            by = byMonth
            parameter = (sfID,) + tuple(hours[int(datetime.datetime.now().strftime('%H'))%6])
        if self.connection:
            cursor = self.connection.cursor()
            cursor.execute(FETCH_SF_query_+by,parameter)
            rows = cursor.fetchall()
            if rows:
                for k, v in {0:'CO2', 1:'LUX', 2:'INTMP', 3:'INHUMID'}.items():
                    dictionary[v]=[row[k] for row in rows]
                    dictionary[v].reverse()
                dictionary['TIME']=[row[4][-14:-6] for row in rows]
                dictionary['TIME'].reverse()
        self.fetchSFOldDataSignal.emit(False, sfID-1)

    @PyQt5.QtCore.pyqtSlot(int, str, dict)
    def fetchELEC_OldData(self, period, dictionary):
        if self.connection:
            cursor = self.connection.cursor()
            if period == 'week':
                cursor.execute(FETCH_ELEC_query_+byWeek, ('electron',))
            else :
                cursor.execute(FETCH_ELEC_query_+byMonth,('electron',)+tuple(hours[int(datetime.datetime.now().strftime('%H'))%6]))
            rows = cursor.fetchall()
            if rows:
                dictionary['ELECTRON']=[int(row[0]) for row in rows]
                dictionary['ELECTRON'].reverse()
                dictionary['TIME']=[row[1][-14:-6] for row in rows]
                dictionary['TIME'].reverse()
        self.fetchElectronOldDataSignal.emit(False)

    def fetchELEC_StatData(self):
        if self.connection:
            cursor = self.connection.cursor()
            cursor.execute(FETCH_ELEC_query_byHour)
            SENSOR.ELECTRON_dict['1h'] = cursor.fetchall()[0][0]
            cursor.execute(FETCH_ELEC_query_byDay) 
            SENSOR.ELECTRON_dict['1d'] =  cursor.fetchall()[0][0]         
            cursor.execute(FETCH_ELEC_query_byWeek)
            SENSOR.ELECTRON_dict['1w'] = cursor.fetchall()[0][0]
            cursor.execute(FETCH_ELEC_query_byMonth)
            SENSOR.ELECTRON_dict['1m'] = cursor.fetchall()[0][0]
            self.fetchElectronStatSignal.emit()

    def disconnect(self):
        #connection 닫기
        if self.connection:
            self.connection.close()
            print('fetching DB disconnected!')


class UartCom():
    
    def __init__(self, ui, eventThread, dbInsertManagerThread):
        self.ui=ui
        self.get_com()
        self.eventThread = eventThread
        self.dbInsertManagerThread = dbInsertManagerThread
        ui.connect.clicked.connect(self.connect_serial)
        ui.disconnect.clicked.connect(self.disconnect_serial)
        ui.fan1_f.clicked.connect(lambda: self.controlFanPower('1'))
        ui.fan2_f.clicked.connect(lambda: self.controlFanPower('2'))
        ui.uv_f.clicked.connect(self.controlUVPower)
        ui.make.clicked.connect(lambda: self.controlNutMixer('make'))
        ui.stop.clicked.connect(lambda: self.controlNutMixer('stop'))
        self.uart = None
        self.connect_serial()

    def get_com(self, waiting = 0):
        time.sleep(waiting)
        connect_port=[]
        if sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            self.isLinux = True
        else:
            self.isLinux = False
        COM_Ports=self.serial_ports()
        for port in COM_Ports:
            if port.find('COM') > -1:
                connect_port.append(port)
        print (connect_port)
        if not connect_port:
            eventThread.alert('통신 연결을 확인한 후 프로그램을 재실행 해주십시오')
        else:
            for comport in connect_port:
                ui.coms.addItem(comport)

    def serial_ports(self):  
        if sys.platform.startswith('win'):   
            ports = ['COM%s' % (i + 1) for i in range(256)]   
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):   
            # this excludes your current terminal "/dev/tty"   
            ports = glob.glob('/dev/tty[A-Za-z]*')   
        elif sys.platform.startswith('darwin'):   
            ports = glob.glob('/dev/tty.*')   
        else:   
            raise EnvironmentError('Unsupported platform')   
        result = []   
        for port in ports:   
            try:   
                s = serial.Serial(port)   
                s.close()   
                result.append(port)   
            except (OSError, serial.SerialException):  
                pass
        return result

    def run(self, loop):
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        print("Closed Uart thread!")

    def connect_serial(self):
        com_no = str(ui.coms.currentText())
        print(com_no)
        if com_no:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            if self.isLinux:
                self.coro = serial_asyncio.create_serial_connection(self.loop, lambda: UartProtocol(self, self.eventThread, self.dbInsertManagerThread), com_no, baudrate=115200)
                print(str(com_no)+' connected')
            else:
                self.coro = serial_asyncio.create_serial_connection(self.loop, lambda: UartProtocol(self, self.eventThread, self.dbInsertManagerThread), com_no, baudrate=115200)
                print(str(com_no)+' connected')
            self.loop.run_until_complete(self.coro)

            self.t = Thread(target=self.run, args=(self.loop,))
            self.t.start()
            ui.connect.setText('완료')
            ui.connect.setChecked(True)
            ui.connect.setEnabled(False)
            ui.coms.setEnabled(False)
        else:
            ui.connect.setText('연결')
            ui.connect.setChecked(False)
            ui.coms.setEnabled(True)

    def disconnect_serial(self):
        if self.uart != None:
            self.uart.loop.shutdown_asyncgens()
            self.uart.close()
            self.uart = None
        ui.coms.clear()
        self.get_com(0.3)
        ui.connect.setChecked(False)
        ui.connect.setText('연결')
        ui.connect.setEnabled(True)
        ui.coms.setEnabled(True)

    def sendUart(self):
        if self.uart != None:
            self.sendTemp()
            time.sleep(0.2)
            self.sendWater()
            time.sleep(0.2)
            self.sendElectron()
            time.sleep(0.2)
    
    def sendTemp(self):
        msg = '\x02TNTEMP?\x03\x0A\x0D'
        if self.uart != None:
            try:    
                for i in range(1,6):
                    self.uart.write(msg.replace('N',str(i)).encode())
                    time.sleep(0.1)
            except Exception as e:
                print(str(e))
                eventThread.alertSignal.emit('통신 연결 상태를 확인해 주십시오.')
        else : 
            eventThread.alertSignal.emit('통신 연결 상태를 확인해 주십시오.')
            print('Not Connected')

    def sendWater(self):
        msg = '\x02W1WATER?\x03\x0A\x0D'
        print(msg)
        if self.uart != None:
            try:
                self.uart.write(msg.encode())  
            except Exception as e:
                print(str(e))
                eventThread.alertSignal.emit('통신 연결 상태를 확인해 주십시오.')
        else :
            eventThread.alertSignal.emit('통신 연결 상태를 확인해 주십시오.')
            print('Not Connected')

    
    def sendElectron(self):
        msg = '\x02P1P1\x03\x0A\x0D'
        pass
        if self.uart != None:
            try:
                self.uart.write(msg.encode())
            except Exception as e:
                print(str(e))
                eventThread.alertSignal.emit('통신 연결 상태를 확인해 주십시오.')
        else :
            eventThread.alertSignal.emit('통신 연결 상태를 확인해 주십시오.')
            print('Not Connected')

    def controlFanPower(self, fanID):
        if SETTINGS.fan['fan'+fanID] == 'off':
            msg = '\x02F'+fanID+'FO\x03\x0A\x0D'
        else:
            msg = '\x02F'+fanID+'FX\x03\x0A\x0D'
        if self.uart != None:
            try:
                self.uart.write(msg.encode())   
                print(msg)
            except Exception as e:
                print(str(e))
                eventThread.alertSignal.emit('통신 연결 상태를 확인해 주십시오.') 
        else : 
            eventThread.alertSignal.emit('통신 연결 상태를 확인해 주십시오.')
            print('Not Connected')

    def controlUVPower(self):
        if SETTINGS.uv == 'off':
            msg = '\x02U1UO\x03\x0A\x0D'
        else:
            msg = '\x02U1UX\x03\x0A\x0D'
        if self.uart != None:
            try:
                self.uart.write(msg.encode())    
                print(msg)
            except Exception as e:
                print(str(e))
                eventThread.alertSignal.emit('통신 연결 상태를 확인해 주십시오.')
        else : 
            eventThread.alertSignal.emit('통신 연결 상태를 확인해 주십시오.')
            print('Not Connected')

    def controlLEDPower(self, order, ledID):
        if order == 'on':
            msg = '\x02L0'+ledID+'W255R255G255B255\x03\x0A\x0D'
        elif order == 'off':
            msg = '\x02L0'+ledID+'W000R000G000B000\x03\x0A\x0D'
        if self.uart != None:
            try:
                self.uart.write(msg.encode())    
                print(msg)
            except Exception as e:
                print(str(e))
                eventThread.alertSignal.emit('통신 연결 상태를 확인해 주십시오.')
        else : 
            eventThread.alertSignal.emit('통신 연결 상태를 확인해 주십시오.')
            print('Not Connected')

    def controlNutMixer(self, order):
        if order == 'make':
            SETTINGS.nut['volume'] = ui.nut_vol.value()
            SETTINGS.nut['ratio'] = ui.nut_ratio.value()
            T = str(SETTINGS.nut['volume']+1000)[1:]
            R = str(SETTINGS.nut['ratio']+1000)[1:]
            msg = '\x02NT'+T+'R'+R+'\x03\x0A\x0D'
        elif order == 'stop':
            msg = '\x02NTSTOP\x03\x0A\x0D'
        if self.uart != None:
            try:
                self.uart.write(msg.encode())    
                print(msg)
            except Exception as e:
                print(str(e))
                eventThread.alertSignal.emit('통신 연결 상태를 확인해 주십시오.')
        else : 
            eventThread.alertSignal.emit('통신 연결 상태를 확인해 주십시오.')
            print('Not Connected')
        
    def controlNutTime(self, order):
        if order == 'start':
            msg = '\x02NTSTART\x03\x0A\x0D'
        elif order == 'stop':
            msg = '\x02NTSTOP\x03\x0A\x0D'
        if self.uart != None:
            try :
                self.uart.write(msg.encode())
                print(msg)
            except Exception as e:
                print(str(e))
                eventThread.alertSignal.emit('통신 연결 상태를 확인해 주십시오.')
        else : 
            eventThread.alertSignal.emit('통신 연결 상태를 확인해 주십시오.')
            print('Not Connected')


class UartProtocol(asyncio.Protocol):
    def __init__(self, uartCom, eventThread, dbInsertManagerThread):
        self.uartCom = uartCom
        self.rcvParser = RcvParser(uartCom, eventThread, dbInsertManagerThread)

    def connection_made(self, transport):
        self.transport = transport
        print('port opened', transport)
        # rts (Request to Send) : 송신 요청
        # cts (Clear to Send) : 송신 확인
        transport.serial.rts = False 
        self.uartCom.uart = transport

    def data_received(self, data):
        message = data.decode()
        print('data received', message)
        self.rcvParser.parsing(message)

    def connection_lost(self, exc):
        print('port closed')
        self.transport.loop.stop()

    def pause_writing(self):
        print('pause writing')
        print(self.transport.get_write_buffer_size())

    def resume_writing(self):
        print(self.transport.get_write_buffer_size())
        print('resume writing')


class RcvParser(PyQt5.QtCore.QObject):
    
    updateTempSignal = PyQt5.QtCore.pyqtSignal(bool,int)
    updateWaterSignal = PyQt5.QtCore.pyqtSignal()
    updateElectronSignal = PyQt5.QtCore.pyqtSignal(bool)
    updateActuatorSignal  = PyQt5.QtCore.pyqtSignal(str,str)
    
    insertDBSignal = PyQt5.QtCore.pyqtSignal(dict, str)

    def __init__(self, uartCom, eventThread, dbInsertManagerThread):
        super().__init__()
        self.uartCom = uartCom
        self.dbInsertManagerThread = dbInsertManagerThread
        self.initProtocol()

        self.updateTempSignal.connect(eventThread.updateSFPlot)
        self.updateWaterSignal.connect(eventThread.updateSF)
        self.updateWaterSignal.connect(eventThread.updateNutrient)
        self.updateElectronSignal.connect(eventThread.updateELECPlot)
        self.updateActuatorSignal.connect(eventThread.updateActuator)

        self.insertDBSignal.connect(dbInsertManagerThread.insertData)

    def parsing(self, pkt):
        self.command = pkt.strip("\x02\x03\n\r")
        cmd = self.command[0]
        try:
            func = self.protocol.get(cmd)
            return func(self.command)
        except Exception as e:
            print("Error{!r}, errorno is {}:".format(e, e.args[0]))

    def rcvTemp(self, command):
        print('data parsed ', command)
        time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            index = int(command[1])   
        except Exception as e:
            print(str(e))
            index = -1
            pass 
        try:
            intmp = float(command[3:8])
        except Exception as e:
            print(str(e))
            intmp = sfDef_list[index-1].DayData_dict['INTMP'][-1]
        try:
            inhumid = float(command[9:11])
        except Exception as e:
            print(str(e))
            inhumid = sfDef_list[index-1].DayData_dict['INHUMID'][-1]
        try:
            co2 = float(command[12:16])
        except Exception as e:
            print(str(e))
            co2 = sfDef_list[index-1].DayData_dict['CO2'][-1]
        try:
            lux = float(command[17:])
        except Exception as e:
            print(str(e))
            lux =sfDef_list[index-2].DayData_dict['LUX'][-1]
        self.insertDBSignal.emit({'ID':'sf','sfID':index-1,'INTMP':intmp, 'INHUMID': inhumid, 'CO2':co2, 'LUX':lux,'TIME':time},'sf')
        for k, v in {'INTMP': intmp, 'INHUMID':inhumid, 'CO2':co2, 'LUX':lux, 'TIME':time[-8:]}.items():
            sfDef_list[index-2].DayData_dict[k].append(v)
        self.updateTempSignal.emit(True, index-2)
        for k in ['INTMP', 'INHUMID', 'CO2', 'LUX', 'TIME']:
            sfDef_list[index-2].DayData_dict[k].pop(0)

    def rcvWater(self, command):
        print('data parsed ', command)
        time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            tmp = float(command[3:8])
        except Exception as e:
            print(str(e))
            tmp= SENSOR.Data_dict['TMP']
        try:
            do = float(command[9:13])
        except Exception as e:
            print(str(e))
            do = SENSOR.Data_dict['DO']
        try:
            ph = float(command[14:18])
        except Exception as e:
            print(str(e))
            ph = SENSOR.Data_dict['PH']
        try:
            tds = int(command[19:])
        except Exception as e:
            print(str(e))
            tds = SENSOR.Data_dict['TDS']
        self.insertDBSignal.emit({'ID':'water','TMP':tmp,'DO':do,'PH':ph,'TDS':tds, 'TIME':time}, 'water')
        for k, v in {'TMP': tmp, 'DO':do, 'PH':ph, 'TDS':tds}.items():
            SENSOR.Data_dict[k] = v
        self.updateWaterSignal.emit()
        
    def rcvFanpower(self, command):
        print('data parsed ', command)
        if command[1] == '1':
            SETTINGS.fan['fan1'] = 'on' if command[3] =='O' else 'off'
            self.updateActuatorSignal.emit('fan1', SETTINGS.fan['fan1'])
        elif command[1] == '2':
            SETTINGS.fan['fan2'] = 'on' if command[3] == 'O' else 'off'
            self.updateActuatorSignal.emit('fan2',SETTINGS.fan['fan2'])

    def rcvUVpower(self, command):
        print('data parsed ', command)
        try:
            SETTINGS.uv = 'on' if command[3]=='O' else 'off'
            self.updateActuatorSignal.emit('uv', SETTINGS.uv)
        except Exception as e:
            print(str(e))

    def rcvLEDpower(self, command):
        print('data parsed ', command)
        try :
            ledID = str(int(command[1:3]))
            SETTINGS.led[ledID]['sts'] ='off' if command[4:7] =='000' and command[8:11] == '000' \
                and command[12:15]=='000' and command[16:] == '000' else 'on'
        except Exception as e:
            print(str(e))

    def rcvElectron(self, command):
        print('data parsed', command)
        time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            electron = float(command[3:6])
        except Exception as e:
            print(str(e))
            electron = SENSOR.DayData_dict['ELECTRON'][-1]
        self.insertDBSignal.emit({'ID':'electron','ELEC':electron,'TIME':time}, 'electron')
        SENSOR.DayData_dict['ELECTRON'].append(electron)
        SENSOR.DayData_dict['TIME'].append(time[-9:])
        self.updateElectronSignal.emit(True)
        SENSOR.DayData_dict['ELECTRON'].pop(0)
        SENSOR.DayData_dict['TIME'].pop(0)

    def rcvNutTime(self, command):
        print('data parsed', command)
        try:
            order = command[1:6]
            if order == 'START':
                SETTINGS.nut['sts'] = 'on'
            elif order == 'STOP':
                SETTINGS.nut['sts'] = 'off'

        except Exception as e:
            print(str(e))

        
    def initProtocol(self):
        self.protocol = {
        'T': self.rcvTemp,
        'W': self.rcvWater,
        'F': self.rcvFanpower,
        'L': self.rcvLEDpower,
        'U': self.rcvUVpower,
        'P': self.rcvElectron,
        'S': self.rcvNutTime
        }  

#QThread를 상속받는 시계 ui 업데이트 스레드
class TimeUpdateThread(PyQt5.QtCore.QThread):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.timer = PyQt5.QtCore.QTimer()
        self.timer.timeout.connect(self.changeTime)
        self.timer.start(1000)
        self.start()

    def changeTime(self):
        cur_time = PyQt5.QtCore.QTime.currentTime()
        ui.time_h.setText(cur_time.toString('hh'))
        ui.time_m.setText(cur_time.toString('mm'))
        ui.time_s.setText(cur_time.toString('ss'))
        cur_date = PyQt5.QtCore.QDate.currentDate()
        ui.time_date.setText(cur_date.toString('yyyy년  MM월  dd일'))

class ValueUpdateThread(PyQt5.QtCore.QThread):
    def __init__(self, ui, uartCom, eventThread):
        super().__init__()
        self.ui = ui
        self.uartCom = uartCom
        self.eventThread = eventThread
        self.sens_timer = PyQt5.QtCore.QTimer()
        self.sens_timer.timeout.connect(self.updateValue)
        self.freq = 10000
        if SETTINGS.sens_unit == 's':
            self.freq = SETTINGS.sens_freq*1000
        elif SETTINGS.sens_unit == 'm':
            self.freq = SETTINGS.sens_freq*1000*60
        elif SETTINGS.sens_unit == 'h':
            self.freq = SETTINGS.sens_freq*1000*60*60
        self.sens_timer.start(self.freq)
        self.led_timer = PyQt5.QtCore.QTimer()
        self.led_timer.timeout.connect(lambda: self.checkLED(datetime.datetime.now()))
        self.led_timer.start(60000)
        self.nut_timer = PyQt5.QtCore.QTimer()
        self.nut_timer.timeout.connect(self.checkNutTime)
        self.nut_timer.start(SETTINGS.nut_freq*60*1000)
        self.start()

    def updateValue(self):
        if self.uartCom.uart != None:
            self.uartCom.sendUart()

    def checkLED(self, now):
        print('---check LED---')
        for ledID, led in SETTINGS.led.items():
            if led['act']=='O' and led['on_at']==now.strftime('%H:%M'):
                self.uartCom.controlLEDPower('on', str(ledID))
            elif led['act']=='O' and led['off_at']==now.strftime('%H:%M'):
                self.uartCom.controlLEDPower('off', str(ledID))

    def checkNutTime(self):
        print('---check NutTime---')
        self.uartCom.controlNutTime('start')
        self.timer = PyQt5.QtCore.QTimer.singleShot(SETTINGS.nut_time*60*1000,
            lambda: self.uartCom.controlNutTime('stop'))

        
class EventThread(PyQt5.QtCore.QThread):
    
    alertSignal = PyQt5.QtCore.pyqtSignal(str)

    def __init__(self, ui):
        super().__init__()      
        self.alertSignal.connect(self.alert)
        self.mainButton_list = [ui.main, ui.elec, ui.nut,ui.settings]
        for i, mainButton in enumerate(self.mainButton_list):
            mainButton.clicked.connect(partial(ui.stackedWidget.setCurrentIndex,i))
        self.sf_list = [ui.sf1, ui.sf2, ui.sf3, ui.sf4, ui.sf5]
        for i,sf in enumerate(self.sf_list):
            sf.clicked.connect(partial(ui.stackedWidget_3.setCurrentIndex, i))  
        self.ledButton_b_list = [ui.led1_b, ui.led2_b, ui.led3_b, ui.led4_b, ui.led5_b, ui.led6_b, ui.led7_b, ui.led8_b]  
        self.ledButton_dict = {1:ui.led1, 2:ui.led2, 3:ui.led3, 4:ui.led4,5:ui.led5, 6:ui.led6, 7:ui.led7, 8:ui.led8 }
        self.checkbox_list = [[ui.co21, ui.lux1, ui.temp1, ui.humi1],[ui.co22, ui.lux2, ui.temp2, ui.humi2],
                            [ui.co23, ui.lux3, ui.temp3, ui.humi3],[ui.co24, ui.lux4, ui.temp4, ui.humi4],
                            [ui.co25, ui.lux5, ui.temp5, ui.humi5]]
        self.radioButton_list = [[ui.sf_day1, ui.sf_day2,ui.sf_day3, ui.sf_day4,ui.sf_day5],
                                [ui.sf_week1, ui.sf_week2, ui.sf_week3, ui.sf_week4, ui.sf_week5],
                                [ui.sf_month1, ui.sf_month2, ui.sf_month3, ui.sf_month4, ui.sf_month5]]

        self.view_list = [ui.sf_view1, ui.sf_view2, ui.sf_view3, ui.sf_view4, ui.sf_view5]
        self.font11 = PyQt5.QtGui.QFont('맑은 고딕', 11)

        for index, checkboxs in enumerate(self.checkbox_list):
            for checkbox in checkboxs:
                checkbox.clicked.connect(partial(self.classifying, self.radioButton_list[0][index], index, update = 'sf'))
        for index,radioButton in enumerate(self.radioButton_list[0]):
            radioButton.clicked.connect(partial(self.updateSFPlot, True, index))
        for ledID, ledButton in enumerate(self.ledButton_b_list):
            ledButton.clicked.connect(partial(self.updateActuator,'led_b'+str(ledID+1)))
        for ledID, ledButton in self.ledButton_dict.items():
            ledButton.pressed.connect(partial(self.updateSettings, ui, sensor='led'+str(ledID)))
        
        ui.elec_day.clicked.connect(lambda:self.updateELECPlot(True))
        ui.elec_week.clicked.connect(lambda:self.updateELECPlot(False))
        ui.elec_month.clicked.connect(lambda:self.updateELECPlot(False))

        ui.elec.clicked.connect(self.updateELEC)
        ui.elec.clicked.connect(partial(self.classifying, ui.elec_day, update = 'elec'))

        ui.nut_vol.valueChanged.connect(self.calculateNut)
        ui.nut_ratio.valueChanged.connect(self.calculateNut)

        ui.settings.clicked.connect(lambda: self.updateSettings(ui, sensor='pushButton'))
        
        ui.serv_add_save.clicked.connect(lambda :self.updateSettings(ui, sensor = 'serv_add'))
        ui.serv_add_save.clicked.connect(lambda: self.alert('프로그램 종료 후 재실행 시 적용됩니다.'))
        ui.serv_save.clicked.connect(lambda:self.updateSettings(ui, sensor = 'serv'))
        ui.serv_save.clicked.connect(lambda:self.alert('프로그램 종료 후 재실행 시 적용됩니다.'))
        
        ui.sens_save.clicked.connect(lambda: self.updateSettings(ui, sensor = 'sens'))
        ui.sens_save.clicked.connect(lambda: self.alert('프로그램 종료 후 재실행 시 적용됩니다.\n센서 측정 최소 주기는 10초입니다.'))

        ui.save_nut.clicked.connect(lambda:self.updateSettings(ui, sensor='save_nut'))
        ui.save_led_time.clicked.connect(lambda:self.updateSettings(ui, sensor='save_led_time'))
        ui.save_tds.clicked.connect(lambda:self.alert('TDS 최소 설정값은 TDS 최대 설정값보다 클 수 없습니다.'if ui.tds_l.value() > ui.tds_h.value() else ''))
        ui.save_tds.clicked.connect(lambda:self.updateSettings(ui,sensor='save_tds'))
        ui.save_ph.clicked.connect(lambda:self.alert('PH 최소 설정값은 PH 최대 설정값보다 클 수 없습니다.' if ui.ph_l.value() > ui.ph_h.value() else ''))
        ui.save_ph.clicked.connect(lambda:self.updateSettings(ui, sensor='save_ph'))
        
        self.updateSettings(ui, INIT = True)
        self.updateSF()
        self.updateNutrient()
        for index in range(5):
            self.updateSFPlot(new = True, graph = index)

    def classifying(self, radioButton, index, update):
        if update == 'sf':
            self.updateSFPlot(radioButton.isChecked(), index)
        elif update == 'elec':
            self.updateELECPlot(radioButton.isChecked())

    def alert(self, message):
        if message:
            msgBox = PyQt5.QtWidgets.QMessageBox()
            msgBox.setIcon(PyQt5.QtWidgets.QMessageBox.Information)
            msgBox.setText(message)
            msgBox.setStandardButtons(PyQt5.QtWidgets.QMessageBox.Ok | PyQt5.QtWidgets.QMessageBox.Cancel)
            subapp = msgBox.exec_()
        else:
            pass
    
    @PyQt5.QtCore.pyqtSlot(str,str)
    def updateActuator(self, button, state):
        classify1 = {'on': True, 'off':False}
        classify2 = {True:'O', False:'X'}
        if button =='uv':
            ui.uv_b.setChecked(classify1[state])
        elif button =='fan1':
            ui.fan1_b.setChecked(classify1[state])
        elif button =='fan2':
            ui.fan2_b.setChecked(classify1[state])
        elif 'led' in button:
            SETTINGS.led[int(button[-1])]['act'] = classify2[state] 

    @PyQt5.QtCore.pyqtSlot()
    def updateSF(self):
        ui.main_temp.setText(str(SENSOR.Data_dict['TMP']))
        ui.main_tds.setText(str(SENSOR.Data_dict['TDS']))
        if SETTINGS.tds['low'] <= float(ui.main_tds.text()) <= SETTINGS.tds['high']:
            ui.main_tds.setStyleSheet(normal)
            ui.main_tds_b.setChecked(False)
        else : 
            ui.main_tds.setStyleSheet(abnormal)
            ui.main_tds_b.setChecked(True)
        ui.main_ph.setText(str(SENSOR.Data_dict['PH']))
        if SETTINGS.ph['low'] <= float(ui.main_ph.text()) <= SETTINGS.ph['high']:
            ui.main_ph.setStyleSheet(normal)
            ui.main_ph_b.setChecked(False)
        else:
            ui.main_ph.setStyleSheet(abnormal)
            ui.main_ph_b.setChecked(True)
        ui.main_do.setText(str(SENSOR.Data_dict['DO']))


    @PyQt5.QtCore.pyqtSlot(bool, int)
    def updateSFPlot(self, new = True, graph = 0):
        if new :
            if self.radioButton_list[0][graph].isChecked():
                time_list = ['' if i%12 !=0 else sfDef_list[graph].DayData_dict['TIME'][i] for i in range(48)]
                self.view_list[graph].clear()
                stringaxis = pg.AxisItem(orientation = 'bottom', maxTickLength = 3)
                stringaxis.setTicks([dict(enumerate(time_list)).items()])
                graph1 = self.view_list[graph].addPlot(title = '', axisItems = {'bottom':stringaxis})
                
                graph1.getAxis('bottom').tickFont = self.font11
                graph1.getAxis('left').tickFont = self.font11
                graph1.showGrid(True, True, 0.3)
                if self.checkbox_list[graph][0].isChecked():
                    graph1.plot(sfDef_list[graph].DayData_dict['CO2'][-48:],pen=pg.mkPen(color=(245,183,0), width=3))
                if self.checkbox_list[graph][1].isChecked():
                    graph1.plot(sfDef_list[graph].DayData_dict['LUX'][-48:],pen=pg.mkPen(color=(147,0,250), width=3))
                if self.checkbox_list[graph][2].isChecked():
                    graph1.plot(sfDef_list[graph].DayData_dict['INTMP'][-48:],pen=pg.mkPen(color=(0,220,255), width=3))
                if self.checkbox_list[graph][3].isChecked():
                    graph1.plot(sfDef_list[graph].DayData_dict['INHUMID'][-48:],pen=pg.mkPen(color=(137,252,0), width=3))
        else:
            self.dictionary = []
            if self.radioButton_list[1][graph].isChecked():
                self.dictionary = sfDef_list[graph].WeekData_dict
            elif self.radioButton_list[2][graph].isChecked():
                self.dictionary = sfDef_list[graph].MonthData_dict
            if self.dictionary:
                if len(self.dictionary['TIME']) <= 5:
                    time_list = self.dictionary['TIME']
                else:
                    time_list = ['' if i%(len(self.dictionary['TIME'])//5) !=0 else self.dictionary['TIME'][i] for i in range(len(self.dictionary['TIME']))]
                stringaxis = pg.AxisItem(orientation = 'bottom', maxTickLength = 3)
                stringaxis.setTicks([dict(enumerate(time_list)).items()])
                self.view_list[graph].clear()
                graph1 = self.view_list[graph].addPlot(title='', axisItems = {'bottom':stringaxis})
                graph1.getAxis('bottom').tickFont = self.font11
                graph1.getAxis('left').tickFont = self.font11
                graph1.showGrid(True, True, 0.3)
                if self.checkbox_list[graph][0].isChecked():
                    graph1.plot(self.dictionary['CO2'],pen=pg.mkPen(color=(245,183,0), width=3))
                if self.checkbox_list[graph][1].isChecked():
                    graph1.plot(self.dictionary['LUX'],pen=pg.mkPen(color=(147,0,250), width=3))
                if self.checkbox_list[graph][2].isChecked():
                    graph1.plot(self.dictionary['INTMP'],pen=pg.mkPen(color=(0,220,200), width=3))
                if self.checkbox_list[graph][3].isChecked():
                    graph1.plot(self.dictionary['INHUMID'],pen=pg.mkPen(color=(137,252,0), width=3))

    @PyQt5.QtCore.pyqtSlot()
    def updateELEC(self):
        ui.elec_1h.setText(str(SENSOR.ELECTRON_dict['1h']) if SENSOR.ELECTRON_dict['1h'] != None else '0')
        ui.elec_1d.setText(str(SENSOR.ELECTRON_dict['1d']) if SENSOR.ELECTRON_dict['1d'] != None else '0')
        ui.elec_1w.setText(str(SENSOR.ELECTRON_dict['1w']) if SENSOR.ELECTRON_dict['1w'] != None else '0')
        ui.elec_1m.setText(str(SENSOR.ELECTRON_dict['1m']) if SENSOR.ELECTRON_dict['1m'] != None else '0')

    @PyQt5.QtCore.pyqtSlot(bool)
    def updateELECPlot(self, new = True):
        if new :
            if ui.elec_day.isChecked():
                time_list = ['' if i%12 != 0 else SENSOR.DayData_dict['TIME'][i] for i in range(1,48)]
                ui.elec_view.clear()
                stringaxis = pg.AxisItem(orientation = 'bottom')
                stringaxis.setTicks([dict(enumerate(time_list)).items()])
                elecgraph = ui.elec_view.addPlot(title = '',axisItems = {'bottom': stringaxis})
                elecgraph.getAxis('bottom').tickFont = self.font11
                elecgraph.getAxis('left').tickFont = self.font11
                elecgraph.showGrid(True, True, 0.3)
                elecgraph.plot(SENSOR.DayData_dict['ELECTRON'][-48:],pen=pg.mkPen(color=(25,255,55), width=3))
        else:
            self.dictionary = []
            if ui.elec_week.isChecked():
                self.dictionary = SENSOR.WeekData_dict
            elif ui.elec_month.isChecked():
                self.dictionary = SENSOR.MonthData_dict
            if self.dictionary:
                ui.elec_view.clear()
                if len(self.dictionary['TIME']) <= 5:
                    time_list = self.dictionary['TIME']
                else:
                    time_list = ['' if i%(len(self.dictionary['TIME'])//5) !=0 else self.dictionary['TIME'][i] for i in range(len(self.dictionary['TIME']))]
                stringaxis = pg.AxisItem(orientation = 'bottom')
                stringaxis.setTicks([dict(enumerate(time_list)).items()])
                elecgraph = ui.elec_view.addPlot(title = '',axisItems = {'bottom': stringaxis})
                elecgraph.getAxis('bottom').tickFont = self.font11
                elecgraph.getAxis('left').tickFont = self.font11
                elecgraph.showGrid(True,True, 0.3)
                elecgraph.plot(self.dictionary['ELECTRON'][-48:],pen=pg.mkPen(color=(25,255,55), width=3))

    @PyQt5.QtCore.pyqtSlot()
    def updateNutrient(self):
        ui.nut_vol.setValue(SETTINGS.nut['volume'])
        ui.nut_ratio.setValue(SETTINGS.nut['ratio'])
        ui.nut_temp.setText(str(SENSOR.Data_dict['TMP']))
        ui.nut_tds.setText(str(SENSOR.Data_dict['TDS']))
        ui.nut_ph.setText(str(SENSOR.Data_dict['PH']))
        ui.nut_do.setText(str(SENSOR.Data_dict['DO']))

    def calculateNut(self):
        ui.nutA.setText(str(round(ui.nut_vol.value()*ui.nut_ratio.value()/100,1)))
        ui.nutB.setText(str(round(ui.nut_vol.value()*ui.nut_ratio.value()/100,1)))

    def updateSettings(self, ui, INIT = False, sensor='None'):
        if INIT:
            with open ('config.json', 'r') as jsonFile:
                settingsData = json.load(jsonFile)["SETTINGS"]
                SETTINGS.fan['fan1'] = settingsData['fan']['fan1']
                SETTINGS.fan['fan2'] = settingsData['fan']['fan2']
                SETTINGS.uv = settingsData['uv']
                for ledID in range(1,9):
                    for element in ['act', 'on_at', 'off_at']:
                        SETTINGS.led[ledID][element] = settingsData['led'][str(ledID)][element]
                SETTINGS.tds['low'] = settingsData['tds']['low']
                SETTINGS.tds['high'] = settingsData['tds']['high']
                SETTINGS.ph['low'] = settingsData['ph']['low']
                SETTINGS.ph['high'] = settingsData['ph']['high']
                SETTINGS.nut['volume'] = settingsData['nut']['volume']
                SETTINGS.nut['ratio'] = settingsData['nut']['ratio']
                SETTINGS.nut_freq = settingsData['nut_freq']
                SETTINGS.nut_time = settingsData['nut_time']
                SETTINGS.sens_freq = settingsData['sens_freq']
                SETTINGS.sens_unit = settingsData['sens_unit']
                SETTINGS.serv_freq = settingsData['serv_freq']
                SETTINGS.serv_unit = settingsData['serv_unit']
                SETTINGS.serv_add = settingsData['serv_add']
                SETTINGS.serv_port = settingsData['serv_port']

                for fan, fanButton in {'fan1':ui.fan1_b, 'fan2':ui.fan2_b}.items():
                    if settingsData['fan'][fan] == 'on':
                        fanButton.setChecked(True)
                    else:
                        fanButton.setChecked(False)
                ui.uv_b.setChecked(True) if settingsData['uv'] == 'on' else ui.uv_b.setChecked(False)
                for ledID in range(1,9):
                    if settingsData['led'][str(ledID)]['act'] == 'O':
                        self.ledButton_b_list[ledID-1].setChecked(True)
                    else:
                        self.ledButton_b_list[ledID-1].setChecked(False)
        if sensor == 'pushButton':
            for i,lineEdit in enumerate([ui.ip1, ui.ip2, ui.ip3, ui.ip4]):
                lineEdit.setText(SETTINGS.serv_add.split('.')[i])
            ui.port.setText(SETTINGS.serv_port)
            ui.sens_freq.setValue(int(SETTINGS.sens_freq))
            ui.serv_freq.setValue(int(SETTINGS.serv_freq))
            classify = {'s':'초', 'm':'분', 'h':'시'}
            ui.sens_unit.setCurrentText(classify[SETTINGS.sens_unit])
            ui.serv_unit.setCurrentText(classify[SETTINGS.serv_unit])
            ui.nut_freq.setValue(SETTINGS.nut_freq)
            ui.nut_time.setValue(SETTINGS.nut_time)
            for ledID, led in self.ledButton_dict.items():
                if led.isChecked():
                    ui.led_on_at.setTime(QtCore.QTime.fromString(SETTINGS.led[ledID]['on_at'], 'hh:mm'))
                    ui.led_off_at.setTime(QtCore.QTime.fromString(SETTINGS.led[ledID]['off_at'], 'hh:mm'))
                    break
            ui.tds_l.setValue(SETTINGS.tds['low'])
            ui.tds_h.setValue(SETTINGS.tds['high'])
            ui.ph_l.setValue(SETTINGS.ph['low'])
            ui.ph_h.setValue(SETTINGS.ph['high'])
        elif sensor == 'save_nut':
            SETTINGS.nut_freq = ui.nut_freq.value()
            SETTINGS.nut_time = ui.nut_time.value()
        elif sensor == 'save_led_time':
            for ledID, led in self.ledButton_dict.items():
                if led.isChecked():
                    SETTINGS.led[ledID]['on_at'] = ui.led_on_at.time().toString('HH:mm')
                    SETTINGS.led[ledID]['off_at'] = ui.led_off_at.time().toString('HH:mm')
                    break
        elif sensor == 'save_tds':
            if ui.tds_l.value() > ui.tds_h.value():
                ui.tds_l.setValue(SETTINGS.tds['low'])
                ui.tds_h.setValue(SETTINGS.tds['high'])
            else:    
                SETTINGS.tds['low'] = ui.tds_l.value()
                SETTINGS.tds['high'] = ui.tds_h.value()
        elif sensor == 'save_ph':
            if ui.ph_l.value() > ui.ph_h.value():
                ui.ph_l.setValue(SETTINGS.ph['low'])
                ui.ph_h.setValue(SETTINGS.ph['high'])
            else: 
                SETTINGS.ph['low'] =  ui.ph_l.value()  
                SETTINGS.ph['high'] =  ui.ph_h.value()
        elif sensor == 'sens':
            classify = { '초':'s','분':'m', '시':'h'}
            if (ui.sens_freq.value() >= 10 and ui.sens_unit.currentText() == '초' )or\
            (ui.sens_unit.currentText() != '초'):
                SETTINGS.sens_freq = ui.sens_freq.value()
                SETTINGS.sens_unit = classify[ui.sens_unit.currentText()]
            else :
                SETTINGS.sens_freq = 10
                ui.sens_freq.setValue(SETTINGS.sens_freq)
        elif sensor == 'serv':
            classify = { '초':'s','분':'m', '시':'h'}
            SETTINGS.serv_freq = ui.serv_freq.value()
            SETTINGS.serv_unit = classify[ui.serv_unit.currentText()]
        elif sensor == 'serv_add':
            SETTINGS.serv_add = '.'.join([ui.ip1.text(), ui.ip2.text(),ui.ip3.text(),ui.ip4.text()])
            SETTINGS.serv_port = ui.port.text()
        elif sensor.find('led') == 0:
            ui.led_on_at.setTime(QtCore.QTime.fromString(SETTINGS.led[int(sensor[-1])]['on_at'], 'hh:mm'))
            ui.led_off_at.setTime(QtCore.QTime.fromString(SETTINGS.led[int(sensor[-1])]['off_at'], 'hh:mm'))

def stopall(eventThread, valueUpdateThread, timeUpdateThread, uartCom, dbInsertManagerThread, dbFetchManagerThread):
    if uartCom.uart != None:
        uartCom.uart.loop.shutdown_asyncgens()
        uartCom.uart.close()
    if eventThread.isRunning():
        eventThread.terminate()
    if valueUpdateThread.isRunning():
        valueUpdateThread.terminate()
    if timeUpdateThread.isRunning():
        timeUpdateThread.terminate()
    dbInsertManagerThread.disconnect()
    dbFetchManagerThread.disconnect()
    print('saving data')
    with open ('config.json', 'r') as jsonFile:
        data = json.load(jsonFile)
        settingsData = data['SETTINGS']
        settingsData['uv'] = SETTINGS.uv
        for fan in ['fan1', 'fan2']:
            settingsData['fan'][fan] = SETTINGS.fan[fan]
        for index in range(1,9):
            for element in ['act', 'on_at', 'off_at']:
                settingsData['led'][str(index)][element] = SETTINGS.led[index][element]
        settingsData['tds']['low'] = SETTINGS.tds['low']
        settingsData['tds']['high'] = SETTINGS.tds['high']
        settingsData['ph']['low'] = SETTINGS.ph['low']
        settingsData['ph']['high'] = SETTINGS.ph['high']
        settingsData['nut']['volume'] = SETTINGS.nut['volume']
        settingsData['nut']['ratio'] = SETTINGS.nut['ratio']
        classify =  {'nut_freq':SETTINGS.nut_freq, 'nut_time':SETTINGS.nut_time,
                    'sens_freq':SETTINGS.sens_freq, 'sens_unit':SETTINGS.sens_unit,
                    'serv_freq':SETTINGS.serv_freq, 'serv_unit':SETTINGS.serv_unit, 
                    'serv_add':SETTINGS.serv_add, 'serv_port':SETTINGS.serv_port}
        for k,v in classify.items():
            settingsData[k] = v
        
    with open("config.json", "w") as jsonFile:
        json.dump(data, jsonFile, indent = 4)
    print("Closed all thread!")
    
if __name__ == '__main__':
    import sys
    pg.setConfigOption('foreground', 'w')
    pg.setConfigOption('background', pg.mkColor(255,255,255,0))
    pg.setConfigOptions(antialias = True)
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    #MainWindow.showFullScreen()
    timeUpdateThread = TimeUpdateThread(ui)
    MainWindow.show()
    dbInsertManagerThread = DBInsertManager()
    eventThread = EventThread(ui)
    uartCom = UartCom(ui, eventThread, dbInsertManagerThread)
    valueUpdateThread = ValueUpdateThread(ui, uartCom, eventThread)
    dbFetchManagerThread = DBFetchManager(ui, eventThread)
    app.aboutToQuit.connect(lambda: stopall(eventThread, valueUpdateThread, timeUpdateThread, uartCom, dbInsertManagerThread, dbFetchManagerThread))
    sys.exit(app.exec_())