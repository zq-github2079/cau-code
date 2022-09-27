from machine import Pin, ADC 
import os
import utime
import binascii
#import picosleep

print(os.uname())

ADC0= ADC(Pin(26))
sensor_temp = ADC(4)
led_pin =25  #onboard led
pwr_en = 15  #pin to control the power of the module
uart_port = 0
uart_baute = 9600

APN = "cmnbiot"

uart_port1 = 1
uart_baute1 = 4800

#RS485协议1-3层读取数据指令
txdata1=b'\x01\x03\x00\x00\x00\x02\xC4\x0B\r\n'
txdata2=b'\x01\x03\x00\x02\x00\x02\x65\xCB\r\n'
txdata3=b'\x01\x03\x00\x04\x00\x02\x85\xCA\r\n'

txdata4=b'\x02\x03\x00\x00\x00\x02\xC4\x38\r\n'
txdata5=b'\x03\x03\x00\x00\x00\x02\xC5\xE9\r\n'
txdata6=b'\x04\x03\x00\x00\x00\x02\xC4\x5E\r\n'

i=0
reading=0
temperature=0
rec_buff = ''
time=''
device=''

#uart setting
uart = machine.UART(uart_port, uart_baute, bits=8, parity=None, stop=1)
uart1 = machine.UART(uart_port1, uart_baute1, bits=8, parity=None, stop=1)

#LED indicator on Raspberry Pi Pico
led_onboard = machine.Pin(led_pin, machine.Pin.OUT)

#电极驱动引脚指定
FI=machine.Pin(2, machine.Pin.OUT)
BI=machine.Pin(3, machine.Pin.OUT)

# MQTT Server info
mqtt_host = '124.70.92.144'           
mqtt_port = '20883'

mqtt_topic1 = 'testtopic'
mqtt_topic2 = 'testtopic/led'
mqtt_topic3 = 'testtopic/temp'
mqtt_topic4 = 'testtopic/adc'
mqtt_topic5 = 'testtopic/tempwarning'
mqtt_topic6 = 'testtopic/warning'
mqtt_topic7 = 'testtopic/gpsinfo'

mqtt_msg = 'on'

def DeviceContrl_ON():#控制电磁阀开
    FI.value(1)
    BI.value(0)
    utime.sleep(1)
    
def DeviceContrl_OFF():#控制电磁阀关
    FI.value(0)
    BI.value(1)
    utime.sleep(1)
    

def writeRS485(txdata):#向RS485传感器写指令并返回读取到的指令
    uart1.write(txdata)
    utime.sleep(2)
    rxdata=bytes()
    print(uart1.any())
    while uart1.any()>0:
        rxdata += uart1.read(1)
    return rxdata

def bytes_to_int(rxdata):#字节转整数数组
    data=[x for x in rxdata]
    return data

def led_blink():#树莓派pico板载LED灯控制
    led_onboard.value(1)
    utime.sleep(0.5)
    led_onboard.value(0)
    utime.sleep(0.5)
    led_onboard.value(1)
    utime.sleep(0.5)
    led_onboard.value(0)

#power on/off the module
def powerOn_Off(pwr_en,time):
    pwr_key = machine.Pin(pwr_en, machine.Pin.OUT)
    pwr_key.value(1)
    utime.sleep(time)
    pwr_key.value(0)

#Get ADC and temperature value of Raspberry Pi Pico
def ADC_temp():
    global reading
    global ADC0_reading
    global temperature
    ADC0_reading = ADC0.read_u16()*33/65535
    print("ADC0 voltage = {0:.2f}V \r\n".format(ADC0_reading))   
    reading = sensor_temp.read_u16()*3.3/65535
    temperature = 27 - (reading - 0.706)/0.001721
    print("temperature = {0:.2f}℃ \r\n".format(temperature))
    
def hexStr_to_str(hex_str):#二进制字符转换为字符
    hex = hex_str.encode('utf-8')
    str_bin = binascii.unhexlify(hex)
    return str_bin.decode('utf-8')

def str_to_hexStr(string):#字符转换为二进制字符
    str_bin = string.encode('utf-8')
    return binascii.hexlify(str_bin).decode('utf-8')    
    
def waitResp_info(info='',timeout=2000):#等待串口数据数据相应
    prvMills = utime.ticks_ms()
    info = b""
    while (utime.ticks_ms()-prvMills)<timeout:
        if uart.any():
            info = b"".join([info, uart.read(1)])
    print(info.decode())
    return info

#Send AT command
def sendAt(cmd,back,timeout=1000):
    rec_buff = b''
    uart.write((cmd+'\r\n').encode())
    prvMills = utime.ticks_ms()
    while (utime.ticks_ms()-prvMills)<timeout:
        if uart.any():
            rec_buff = b"".join([rec_buff, uart.read(1)])
    if rec_buff != '':
        if back not in rec_buff.decode():
            print(cmd + ' back:\t' + rec_buff.decode())
            return 0
        else:
            print(rec_buff.decode())
            return 1
    else:
        print(cmd + ' no responce')
        
def checkStart():#检查NB-IoT模块AT指令
    while True:
        uart.write( 'AT\r\n'.encode() )
        utime.sleep(2)
        uart.write( 'AT\r\n'.encode() )
        recBuff = waitResp_info()
        if 'OK' in recBuff.decode():
            print( 'SIM7080G is ready\r\n' + recBuff.decode() )
            recBuff = ''
            break 
        else:
            print( 'SIM7080G is starting up, please wait...\r\n')
            utime.sleep(2)
            continue
        
def checkNetwork():#检查NB-IoT模块网络连接
#     sendAt("AT+CFUN=0","OK",2000)
    sendAt("AT+CNMP=38","OK",2000)      #Select LTE mode
    sendAt("AT+CMNB=2","OK",2000)       #Select NB-IoT mode,if Cat-M，please set to 1
    sendAt("AT+CFUN=1","OK",2000)
    utime.sleep(2)
    sendAt("AT+CSQ","OK",2000)
    sendAt("AT+CPSI?","OK",2000)
    sendAt("AT+COPS?","OK",2000)
    sendAt("AT+CGNAPN","OK",2000)#获取网络APN
    sendAt('AT+CNACT=0,1','OK',2000)#激活应用网络
    sendAt('AT+CNACT?','OK',2000)  #查询网络IP     
        
def mqttReceive1(time):#通过MQTT获取云端发送的休眠时间
    sleeptime1=''
    sendAt('AT+SMDISC','OK',2000)#断开MQTT连接
    
    #设置MQTT参数
    sendAt('AT+SMCONF=\"URL\",'+mqtt_host+','+mqtt_port,'OK',2000)
    sendAt('AT+SMCONF=\"KEEPTIME\",60','OK',2000)
    sendAt('AT+SMCONF=\"CLIENTID\",\"Pico_SIM7080G\"','OK',2000)
    sendAt('AT+SMCONF=\"QOS\",0','OK',2000)
    flag=sendAt('AT+SMCONN','OK',5000)#MQTT连接
    utime.sleep(1)
    if flag==1:
        sendAt('AT+SMUNSUB=\"sleeptime\"','OK',2000)#取消之前MQTT主题订阅
        utime.sleep(2)
        
        #获取并对数据进行处理，返回休眠时间
        uart.write('AT+SMSUB=\"sleeptime\",1\r\n')#订阅MQTT主题
        utime.sleep(2)
        data=uart.read()
        utime.sleep(1)
        data1=uart.read()#读取串口数据
        data=str(data1)
        print(data)
        print('data1',data[27:(len(data)-6)])
        sleeptime1 = data[27:(len(data)-6)]
        print(len(sleeptime1))
        if len(sleeptime1) != 0 :
            print(sleeptime1,type(sleeptime1))
            return sleeptime1
        else :
            print("sleeptime no data",sleeptime1,type(sleeptime1))
            return 0
        utime.sleep(2);
        sendAt('AT+SMUNSUB=\"sleeptime\"','OK',2000)#取消主题订阅
        print('Receive message successfully!')
        utime.sleep(2)
        sendAt('AT+SMDISC','OK',2000)
    else:
        print("Receive message error!")
        sendAt('AT+SMDISC','OK',2000)

def mqttReceive2(devicedata):#通过MQTT协议从云端获取电磁阀控制信息
    devicedata1=''
    sendAt('AT+SMDISC','OK',2000)
    sendAt('AT+SMCONF=\"URL\",'+mqtt_host+','+mqtt_port,'OK')
    sendAt('AT+SMCONF=\"KEEPTIME\",60','OK')
    sendAt('AT+SMCONF=\"CLIENTID\",\"Pico_SIM7080G\"','OK',2000)
    sendAt('AT+SMCONF=\"QOS\",0','OK',2000)
    flag=sendAt('AT+SMCONN','OK',2000)
    utime.sleep(2)
    while flag==1:
         flag1=sendAt('AT+SMUNSUB=\"devicedata\"','OK',2000)
         utime.sleep(2)
         
         #获取并处理数据，最后返回控制信息
         uart.write('AT+SMSUB=\"devicedata\",1\r\n')
         utime.sleep(2)
         data=uart.read()
         utime.sleep(1)
         data1=uart.read()
         data=str(data1)
         print('data',data)
         print('data1',data[28:(len(data)-6)])
         devicedata1=data[28:(len(data)-6)]
         if len(devicedata1) != 0:
             print("devicedata",devicedata1)
             return devicedata1
         else:
             print("devicedata 00000",devicedata1)
             return 0
         utime.sleep(2);
         sendAt('AT+SMUNSUB=\"devicedata\"','OK',2000)
         print('Receive message successfully!')
         utime.sleep(2)
         sendAt('AT+SMDISC','OK',2000)
    else:
        print("Receive message error!")
        sendAt('AT+SMDISC','OK',2000)
    
def mqttSend1(mqtt_msg):#通过MQTT协议向云端发送电磁阀状态
    sendAt('AT+SMCONF=\"URL\",'+mqtt_host+','+mqtt_port,'OK')
    sendAt('AT+SMCONF=\"KEEPTIME\",60','OK')
    sendAt('AT+SMCONF=\"CLIENTID\",\"Pico_SIM7080G\"','OK',1000)
    sendAt('AT+SMCONF=\"QOS\",0','OK',1000)
    flag=sendAt('AT+SMCONN','OK',5000)
    utime.sleep(1)
    if flag==1:
        sendAt('AT+SMPUB=\"mqtt\",2,1,0','OK',1000)
        uart.write(mqtt_msg.encode())
        utime.sleep(2)
        print('send message successfully!')
        sendAt('AT+SMDISC','OK',1000)
        return 1
    else:
        sendAt('AT+SMPUB=\"mqtt\",2,1,0','OK',1000)
        uart.write(mqtt_msg.encode())
        utime.sleep(2)
        print("Receive message error!")
        sendAt('AT+SMDISC','OK',1000)
        return 0
    
def mqttSend2(mqtt_msg,datalen):#通过MQTT协议向云端发送传感器数据
    sendAt('AT+SMDISC','OK',2000)
    sendAt('AT+SMCONF=\"URL\",'+mqtt_host+','+mqtt_port,'OK')
    sendAt('AT+SMCONF=\"KEEPTIME\",60','OK')
    sendAt('AT+SMCONF=\"CLIENTID\",\"Pico_SIM7080G\"','OK',2000)
    sendAt('AT+SMCONF=\"QOS\",0','OK',2000)
    flag=sendAt('AT+SMCONN','OK',2000)
    utime.sleep(2)
    if flag==1:
        sendAt('AT+SMPUB=\"mqtt\",'+datalen+',1,0','OK',2000)
        uart.write(mqtt_msg.encode())
        utime.sleep(2)
        print('send message successfully!')
        sendAt('AT+SMDISC','OK',2000)
        return 1
    else:
        sendAt('AT+SMPUB=\"mqtt\",2,1,0','OK',2000)
        uart.write(mqtt_msg.encode())
        utime.sleep(2)
        return 0
        print("Receive message error!")
        sendAt('AT+SMDISC','OK',2000)
        
def RS485data(rxdata1,rxdata2,rxdata3):#处理RS485土壤水分传感器数据并返回传感器全部数据
    data1=bytes_to_int(rxdata1)
    data2=bytes_to_int(rxdata2)
    data3=bytes_to_int(rxdata3)
    
    temperature1=(data1[5]*256+data1[6])/10
    humidity1=(data1[3]*256+data1[4])/10
    temperature1=str(temperature1)
    humidity1=str(humidity1)
    
    temperature2=(data2[5]*256+data2[6])/10
    humidity2=(data2[3]*256+data2[4])/10
    temperature2=str(temperature2)
    humidity2=str(humidity2)
    
    temperature3=(data3[5]*256+data3[6])/10
    humidity3=(data3[3]*256+data3[4])/10
    temperature3=str(temperature3)
    humidity3=str(humidity3)
    
    txdata='temperture1:'+temperature1+'  humidity1:'+humidity1+'  temperture2:'+temperature2+'  humidity2:'+humidity2+'  temperture3:'+temperature3+'  humidity3:'+humidity3+''
    return txdata

powerOn_Off(pwr_en,2)#上电开机
utime.sleep(2)

while True:
    sleeptime=60#默认休眠时间为60
    devicedata='off'#默认控制信息为关
    
    checkStart()
    checkNetwork()
#     sendAt('AT+CPSMS=0','OK',2000)
    
    #获取传感器数据指令
    rxdata1=writeRS485(txdata1)
    rxdata2=writeRS485(txdata2)
    rxdata3=writeRS485(txdata3)
    
    rxdata4=writeRS485(txdata4)
    rxdata5=writeRS485(txdata5)
    rxdata6=writeRS485(txdata6)
    
    #处理指令，获得温湿度数据
    txdata1=RS485data(rxdata1,rxdata2,rxdata3)
    txdata2=RS485data(rxdata4,rxdata5,rxdata6)
    
    sendAt('AT+CSQ','OK',2000)#读取信号强度
    
    mqttSend2(txdata1,str(len(txdata1)))#发送传感器数据
    mqttSend2(txdata2,str(len(txdata2)))#发送传感器数据
#     mqttSend1(mqtt_msg)

    #获取休眠时间，无数据则为默认休眠时间
    receivetime=mqttReceive1(time)
    if receivetime == 0:
        sleeptime=sleeptime
    else:
        sleeptime=receivetime
        sleeptime=int(sleeptime)

    #获取控制信息，无数据则为默认控制信息
    receivedevice=mqttReceive2(device)
    if receivedevice==0:
        devicedata=devicedata
    else:
        devicedata=receivedevice
    
#     if devicedata=='on':
#         DeviceContrl_ON()
#     else if devicedata=='off':
#         DeviceContrl_OFF()
    
    utime.sleep(2)
    picosleep.seconds(sleeptime)#模块进入休眠
    
    powerOn_Off(pwr_en,1)#休眠结束，唤醒模块
    utime.sleep(2)
    uart = machine.UART(uart_port, uart_baute, bits=8, parity=None, stop=1)#重新定义串口信息