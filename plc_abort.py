# ************************ #
# This code reads input from PLC to abort the mission being performed      #
# ************************ #
 
import rospy
from std_srvs.srv import Empty, EmptyRequest
import pymcprotocol
import time

class abort():
    #connecting to plc 
    def _init_(self):
        self.pymc3e = pymcprotocol.Type3E()
        self.pymc3e.connect("192.168.0.39", 8891)
        self.main()

    #Reads input from Register Y408 and returns 1 or 0
    def exe(self):
        inp = self.pymc3e.batchread_bitunits(headdevice="Y408", readsize=10)
        return inp[0]

    def main(self):
        while not rospy.is_shutdown():
            #Checking Register Y301 to give value 1 to perform abort operation
            while self.exe() != 0:
                rospy.wait_for_service('/mission_executive/abort_mission', timeout=3)
                try:
                    client = rospy.ServiceProxy('/mission_executive/abort_mission',Empty)
                    request = EmptyRequest()
                    response = client(request)
                    print('Mission Aborted!')
                except rospy.ServiceException as e:
                    print("Service call failed")
                #Mission Aborted acknowlegement
                self.pymc3e.randomwrite_bitunits(bit_devices=["X408"], values=[1])
                time.sleep(1.0)

                #Pluse signal of 1 sec to X300 to reset all registers which also considered as data recieved acknowledgement
                self.pymc3e.randomwrite_bitunits(bit_devices=["X300"], values=[1])
                time.sleep(1.0)
                self.pymc3e.randomwrite_bitunits(bit_devices=["X300"], values=[0])

if _name_ == '_main_':
    abort()