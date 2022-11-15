# ************************ #
# This code reads input from PLC to perform Point,Position and Sequence    #
# based goal and provide acknlowedgements                                  #
# ************************ #
 
import pandas as pd
from navigate_amr import navigate_amr
import os
import rospy
import sys
import rospkg
from std_srvs.srv import Empty, EmptyRequest
import pymcprotocol
import time


class navigate():

    def _init_(self):
        sys.setrecursionlimit(10**6)
        #connecting to plc 
        self.pymc3e = pymcprotocol.Type3E()
        self.pymc3e.connect("192.168.0.39", 8890,timeout=5.0)


        rospy.init_node('Navigation')
        rospack = rospkg.RosPack()
        #Make sure there is a path called mowito_difacto with default_stations containing default.csv (format - station_name,x,y,theta)
        input_path = os.path.join(rospack.get_path('mowito_difacto'),"default_stations","default.csv")

        if not os.path.exists(input_path):
            print('Error: The path specified does not exist')
            sys.exit()

        room_df = pd.read_csv(input_path,names=['roomName','x','y','theta'])

        #Passing the data_frame of .csv to navigate_humanoid.py
        self.navigate_humanoid = navigate_amr(room_df)
        self.main()


    def pos_bas_nav(self):
        def data():
            #Register D401 will contain the station_name
            plcip = self.pymc3e.randomread(word_devices=["D401"], dword_devices=[])
            return plcip[0][0]


        print('Position Based Goal')
        print('--------------------------')
        input_val = data()
        #Initiate the station_goal
        self.navigate_humanoid.goalRoom(input_val)
        #Once the data is sent, data sent acknowledgement sent to register D400
        self.pymc3e.randomwrite(word_devices=["D400"], word_values=[input_val], dword_devices=[], dword_values=[])
        time.sleep(1.0)

        #Pluse signal of 1 sec to X300 to reset all registers which also considered as data recieved acknowledgement
        self.pymc3e.randomwrite_bitunits(bit_devices=["X300"], values=[1])
        time.sleep(1.0)
        self.pymc3e.randomwrite_bitunits(bit_devices=["X300"], values=[0])
        self.main()


    def poi_bas_nav(self):
        def data():
            # 2 Registers each having intergr and float value eg. 1.23 number will be "1" in one register and "23" in the second register
            #D402,D404 - X , D406,D408 - Y , D410,D412 - Theata
            plcip = self.pymc3e.randomread(word_devices=["D402","D404","D406","D408","D410","D412"], dword_devices=[])
            return plcip[0]

        print('Position Based Goal')
        print('--------------------------')
        coor = data()
        for i in range(0,len(coor)):
            #As the PLC gives 2's complement if a negative value is passed, converting it back to negative value
            if (coor[i]>64537):
                coor[i] = coor[i]-2**16
        #As -0 cant't be passed, if we want -0.23, we pass 0 in 1st register and -23 in 2nd register which will give -0.23
        x=float("-"+str(abs(coor[0]))+"."+str(abs(coor[1]))) if coor[1] < 0 else float(str(coor[0])+"."+str(coor[1]))
        y=float("-"+str(abs(coor[2]))+"."+str(abs(coor[3]))) if coor[3] < 0 else float(str(coor[2])+"."+str(coor[3]))
        t=float("-"+str(abs(coor[4]))+"."+str(abs(coor[5]))) if coor[5] < 0 else float(str(coor[4])+"."+str(coor[5]))

        #Initiate Point Goal
        self.navigate_humanoid.go_to_point_set_path(x,y,t)

        #Pluse signal of 1 sec to X300 to reset all registers which also considered as data recieved acknowledgement
        self.pymc3e.randomwrite_bitunits(bit_devices=["X300"], values=[1])
        time.sleep(1.0)
        self.pymc3e.randomwrite_bitunits(bit_devices=["X300"], values=[0])
        self.main()

    def seq_bas_nav(self):
        def data():
            #Station names in the registers for sequences
            plcip = self.pymc3e.randomread(word_devices=["D200","D201","D202","D203","D204","D205","D206","D207","D208","D209","D210","D211"], dword_devices=[])
            return plcip[0]

        print('Sequence Based Goal')
        print('--------------------------')
        input_val = data()
        staip=[]
        for i in range(0,len(input_val)):
            #Removing the registers where no value is passed
            if input_val[i]!=0:
                staip.append(input_val[i])

        #Initiate Sequence goal
        for i in range(0,len(staip)):
            self.navigate_humanoid.goalRoom(staip[i])
            self.pymc3e.randomwrite(word_devices=["D400"], word_values=[i], dword_devices=[], dword_values=[])
            time.sleep(1.0)

        #Pluse signal of 1 sec to X300 to reset all registers which also considered as data recieved acknowledgement
        self.pymc3e.randomwrite_bitunits(bit_devices=["X300"], values=[1])
        time.sleep(1.0)
        self.pymc3e.randomwrite_bitunits(bit_devices=["X300"], values=[0])
        self.main()

    def data(self):
        # Data from PLC to Initiate operations, 1- position based goal, 2- point based goal, 3- sequence based goal, 4- exit
        plcip = self.pymc3e.randomread(word_devices=["D414"], dword_devices=[])
        return plcip[0][0]


    def main(self):
        while (self.pymc3e._is_connected==True):
            print("Enter Command")
            #Keep on checking for value from D414
            choice = self.data()
            if (choice == 1):
                self.pos_bas_nav()
            elif (choice == 2):
                self.poi_bas_nav()
            elif (choice == 3):
                self.seq_bas_nav()
            elif(choice == 4):
                exit()
            time.sleep(2.0)


if _name_ == '_main_':
    navigate()