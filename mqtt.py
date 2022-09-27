import sim7020
import utime
import picosleep

def curTime():
    now = machine.RTC().datetime()
    return "{:02d}:{:02d}:{:02d}".format(now[4], now[5], now[6])

print(curTime())

uart = machine.UART(0, 115200, txbuf=1024, rxbuf=1024)
print(uart) 

sim = sim7020.SIM7020(uart)
sim.reboot(force=True)
sim.wait_ready()

print(sim.exec_cmd('AT+CEREG=0'))
print(sim.exec_cmd('AT+CPSMSTATUS=1'))   
print(sim.exec_cmd('AT+IPR=115200'))
print(sim.exec_cmd('AT+CEREG=4'))
print(sim.exec_cmd('AT+CEREG?'))   #禁止PSM模式
print(sim.exec_cmd('AT+CPSMS=1,,,"01011111","00000001"'))
print(sim.exec_cmd('AT+CEREG?'))
print(sim.exec_cmd('AT+CEREG=1'))
# utime.sleep(2)

# resp = sim.exec_cmd('AT+CMQNEW="124.70.92.144",20883,12000,1024')
# print(resp)
# 
# resp = sim.exec_cmd('AT+CMQCON=0,4,"1a9930fbaa20479494af3f9b636fef23",3600,0,0,cau,cau2011')
# print(resp)

while True:
    resp = sim.exec_cmd('AT+CMQNEW="124.70.92.144",20883,12000,1024')
    print(resp)

    resp = sim.exec_cmd('AT+CMQCON=0,4,"1a9930fbaa20479494af3f9b636fef23",3600,0,0,cau,cau2011')
    print(resp)
    
    cmd = 'AT+CMQPUB=0,"v1/devices/me/telemetry",0,0,0,16,"3132333435363738"'
    resp = sim.exec_cmd(cmd)
    print(resp)
    resp = sim.exec_cmd('AT+CMQUNSUB=0,"v1/devices/me/telemetry"')
    print(resp)
    resp = sim.exec_cmd('AT+CMQDISCON=0')
    print(resp)

    print(curTime())
    picosleep.seconds(20)