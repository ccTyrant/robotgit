from robot import Robot
from robot import BRAKE, COAST
from robot import WALL, TOKEN_ZONE_0,TOKEN_ZONE_1, TOKEN_ZONE_2, TOKEN_ZONE_3
import time
import datetime
from time import sleep
import math
from robot import PinMode, PinValue
r = Robot()
board = r.servo_board
zone = 2
IRPin = 0
forwardConst = 2.2

if zone == 0:
    tokenMarkers = list(TOKEN_ZONE_0)
    leftWallMarkers = [41,42]
    rightWallMarkers = [29,30]
elif zone == 1:
    tokenMarkers = list(TOKEN_ZONE_1)
    leftWallMarkers = [31,30]
    rightWallMarkers = [35,34]
    
elif zone == 2:
    tokenMarkers =list(TOKEN_ZONE_2)
    leftWallMarkers = [32,35]
    rightWallMarkers = [36,39]

elif zone == 3:
    tokenMarkers = list(TOKEN_ZONE_3)
    leftWallMarkers = [36,37]
    rightWallMarkers = [40,41]

errorMarkerID = 6969
errorMarkerDistance = 4201337

arduino = r.servo_board.gpios[2]
arduino.pin_mode = PinMode.INPUT

#TERMINOLOGY
#FRONT and BACK are constant for the robot
#FORWARD is the direction in which the camera is facing

#Arduino Pin Numbers
from robot import PinMode
armBack1pos = 3
armBack1neg = 2#right is pin 1 left is pin to
armBack2pos = 5
armBack2neg = 4

#Servos
RightServo = r.servo_board.servos[1]
LeftServo = r.servo_board.servos[2]
camera = r.servo_board.servos[0]

leftPower = -0.72
rightPower = -0.75

forward = True

def Forward(dist):
        if dist > 0:
            r.motor_board.m1 = leftPower
            r.motor_board.m0 = rightPower
        else:
            r.motor_board.m1 = -leftPower
            r.motor_board.m0 = -rightPower
        time.sleep(abs(dist * forwardConst))
        r.motor_board.m1 = BRAKE
        r.motor_board.m0 = BRAKE
        print("forward " + str(dist) + " completed")
        time.sleep(0.3)

def Rotate(ang):
       const = 0.2
       if ang < 0:
           r.motor_board.m1 = leftPower
           r.motor_board.m0 = -rightPower
       else:
           r.motor_board.m1 = -leftPower
           r.motor_board.m0 = rightPower
       time.sleep(abs(ang * const))
       r.motor_board.m1 = BRAKE
       r.motor_board.m0 = BRAKE
       print("rotated " + str(ang) + " completed")
       time.sleep(0.3)

def lookAndGo():
    markers = r.camera.see()
    print("Number of Markers: " + str(len(markers)))
    if len(markers) != 0:
        for marker in markers:
            print("Marker Object Type: " , type(marker))
            print("Marker: " + str(marker.id))
            if marker.is_token_marker():
                goToMarker(marker.id)
                break
def GetAllMarkersInVision(IDWhitelist):
    markers = r.camera.see()
    markersSelected = ()
    for x in markers:
        if x.id in IDWhitelist:
            markersSelected = markersSelected + (x,)
    return markersSelected

def GetNearestMarkerInVision(IDWhitelist):
    markers = r.camera.see()
    for m in markers:
        if m.id in IDWhitelist:
            return m.id
    return errorMarkerID

def goToNearestMarkerInVision(IDWhitelist):
    markerID = GetNearestMarkerInVision(IDWhitelist)
    if markerID != errorMarkerID:
        print("do you remember gucci gang gucci gang?")
        if goToMarker(markerID):
            armFrontClose()


def goToMarker(markerID):
    captured = False
    markerSeen = False
    while not captured:
        markers = r.camera.see()
        if len(markers) != 0:
            for marker in markers:
                if marker.id == markerID:
                    print(markerID)
                    markerSeen = True
                    ourMarker = marker
                    break
            if markerSeen:
                if ourMarker.distance_metres > 0.7:
                    Rotate(ourMarker.spherical.rot_y_radians)
                    Forward(ourMarker.spherical.distance_metres * 0.6)
                else:
                    Rotate(ourMarker.spherical.rot_y_radians)
                    if ForwardTillIRHit(ourMarker.spherical.distance_metres * 1.2):
                        time.sleep(0.5)
                        Forward(0.3)
                        captured = True
                    else:
                        break
            else:
                print("I aint seen no markers")
                if ForwardTillIRHit(marker.distance_metres * 1.2):
                    captured = True
                    time.sleep(0.5)
                    Forward(0.3)
                else:
                    break
    return captured

def ForwardTillIRHit(maxDist):#returns true if the IR has gone off, false if maxdist reached
    endTime = time.time() + forwardConst * maxDist
    r.motor_board.m1 = leftPower
    r.motor_board.m0 = rightPower
    print("Forwarding till hit" + str(maxDist))
    while time.time() < endTime:
        if arduino.read() == PinValue.HIGH:
            r.motor_board.m1 = BRAKE
            r.motor_board.m0 = BRAKE
            print("I done hit the marker")
            return True
    r.motor_board.m1 = BRAKE
    r.motor_board.m0 = BRAKE
    print("I NO hit marker")
    return False

def IRSensorCheck():
    pass
            
#def getWallMarkerZoneLeft(marker):

def returnToZone():
    pass

#def cameraLook(ang):
#    cameraAngle(ang)
#    markers=r.camera.see()
#    TokenMarkerSeen = ()
#    WallSeen = ()
#    if len(markers) !=0:
#        for m in markers:
#            print("Marker Object Type: " , type(marker))
#            print("Marker: " + str(marker.id))
#            if marker.is_token_marker():
#                TokenMarkerSeen = TokenMarkerSeen + (marker,)
#            elif marker.is_wall_marker():
#                WallSeen = WallSeen + (marker,)
#    TokensSeen = ()
#    TokenIDSeen = ()
#    for m in TokenMarkerSeen:
#        if not TokenIDSeen.__contains__(m.id):
#            TokenIDSeen = TokenIDSeen + (m.id, )
#            TokensSeen = TokensSeen + (m, )
            
    
    


def armFrontClose():
    print("front")
    RightServo.position = 0.35
    print("1close")
    LeftServo.position = -0.53
    print("2close")

def armFrontOpen():
    print("front")
    RightServo.position = -0.5
    print("1open")
    LeftServo.position = 0.4
    print("2open")

#def armBackOpen():
    #print("back")
    #board.gpios[armBack1pos].mode = PinMode.OUTPUT_HIGH
    #board.gpios[armBack1neg].mode = PinMode.OUTPUT_LOW
    #board.gpios[armBack2pos].mode = PinMode.OUTPUT_HIGH
    #board.gpios[armBack2neg].mode = PinMode.OUTPUT_LOW
    #time.sleep(0.2)
    #board.gpios[armBack1pos].mode = PinMode.OUTPUT_LOW
    #board.gpios[armBack1neg].mode = PinMode.OUTPUT_LOW
    #board.gpios[armBack2pos].mode = PinMode.OUTPUT_LOW
    #board.gpios[armBack2neg].mode = PinMode.OUTPUT_LOW
    #print("open")

#def armBackClose():
    #print("back")
    #board.gpios[armBack1pos].mode = PinMode.OUTPUT_LOW
    #board.gpios[armBack1neg].mode = PinMode.OUTPUT_HIGH
    #board.gpios[armBack2pos].mode = PinMode.OUTPUT_LOW
    #board.gpios[armBack2neg].mode = PinMode.OUTPUT_HIGH
    #time.sleep(0.2)
    #board.gpios[armBack1pos].mode = PinMode.OUTPUT_LOW
    #board.gpios[armBack1neg].mode = PinMode.OUTPUT_LOW
    #board.gpios[armBack2pos].mode = PinMode.OUTPUT_LOW
    #board.gpios[armBack2neg].mode = PinMode.OUTPUT_LOW
    #print("close")

#def armForwardOpen():
    #if(forward):
        #armFrontOpen()
    #else:
        #armBackOpen()

#def armForwardClose():
    #if(forward):
        #armFrontClose()
    #else:
        #armBackClose()

#def cameraAngle(ang):
    #const = 0.5/math.pi
    #pos = const * ang
    #if(pos<=0.6 and pos>=-0.6):
        #camera.position = const * ang
        #time.sleep(0.5)
        #print("it worked good")
    #else:
        #print("servo is a knob")
        #wallace()

def wallace():
    r.power_board.buzz(0.4, note='g')
    r.power_board.buzz(0.2, note='f')
    r.power_board.buzz(0.2, note='e')
    r.power_board.buzz(0.4, note='g')
    r.power_board.buzz(0.2, note='f')
    r.power_board.buzz(0.2, note='e')
    r.power_board.buzz(0.2, note='g')
    r.power_board.buzz(1.4, note='d')
    r.power_board.buzz(0.2, note='a')
    r.power_board.buzz(0.2, note='g')
    r.power_board.buzz(0.2, note='a')
    r.power_board.buzz(0.4, note='b')
    r.power_board.buzz(0.2, note='a')
    r.power_board.buzz(0.2, note='g')
    r.power_board.buzz(0.2, note='f')
    r.power_board.buzz(1.6, note='e')
    r.power_board.buzz(0.4, note='g')
    r.power_board.buzz(0.2, note='f')
    r.power_board.buzz(0.2, note='e')
    r.power_board.buzz(0.4, note='g')
    r.power_board.buzz(0.2, note='f')
    r.power_board.buzz(0.2, note='e')
    r.power_board.buzz(0.2, note='g')
    r.power_board.buzz(1.4, note='d')
    r.power_board.buzz(0.2, note='a')
    r.power_board.buzz(0.2, note='g')
    r.power_board.buzz(0.2, note='a')
    r.power_board.buzz(0.4, note='b')
    r.power_board.buzz(0.2, note='a')
    r.power_board.buzz(0.2, note='g')
    r.power_board.buzz(0.2, note='c')
    r.power_board.buzz(0.2, note='g')
    r.power_board.buzz(0.2, note='c')
def BotchGetBack():
    inZone = False
    while not inZone:
        wallMarkers = GetAllMarkersInVision(leftWallMarkers + rightWallMarkers)
        if wallMarkers.count > 0:
            selectedMarker = wallMarkers[0]
            Rotate(selectedMarker.spherical.rot_y_radians)
            Forward(selectedMarker.spherical.dist * 0.7)
            if selectedMarker in rightWallMarkers:
                Rotate(-35 * math.pi / 180)
                Forward(2)
                inZone = True
            else:
                Rotate(35 * math.pi / 180)
                Forward(2)
                inZone = True
        else:
            Rotate(35 * math.pi / 180)

def BotchGetBlocks():
    while True:
        armFrontClose()
        Forward(4)
        goToNearestMarkerInVision(tokenMarkers)
        Forward(-2)
        time.sleep(0.7)
        Forward(0.2)
        armFrontOpen()
        goToNearestMarkerInVision(tokenMarkers)
        Forward(-2)
        time.sleep(0.7)
        Forward(0.2)
        armFrontOpen()
        goToNearestMarkerInVision(tokenMarkers)
        
def GetViewOnBlocks():
    pass




print("THIS IS TOTALLY RUNNING")
BotchGetBlocks()
Rotate(100 * math.pi / 180)
BotchGetBack()

#cameraAngle(0)
    #cameraAngle(math.pi)
    #print("+")
    #camera.position = 0.6
    #time.sleep(2)
    #print("-")
    #camera.position = -0.6
    #time.sleep(2)
#     lookAndGo()
#    #wallace()
     #armFrontOpen()
     #time.sleep(1)
     #armFrontClose()
     #time.sleep(1) 

#    #Rotate(3.1415926)
#    #print("SLEEP")
#    #time.sleep(4)

#    armForwardOpen()
 #   sleep(2)
  #  print ("Open")
   # armForwardClose()
    #print ("Closed")
    #sleep(2)

 #while True:
 #    arm0.position = 0
 #    r.power_board.buzz(1, note = 'c')
 #    print("1")
 #    time.sleep(2)
 #    arm0.position = 0.4
 #    r.power_board.buzz(0.5, note = 'g')
 #    print("2")
 #    time.sleep(2)

 #while True:
 #    board.gpios[2].mode = PinMode.OUTPUT_HIGH
 #    board.gpios[3].mode = PinMode.OUTPUT_LOW
 #    time.sleep(0.2)
 #    board.gpios[2].mode = PinMode.OUTPUT_LOW
 #    board.gpios[3].mode = PinMode.OUTPUT_LOW
 #    time.sleep(0.2)
 #    board.gpios[2].mode = PinMode.OUTPUT_LOW
 #    board.gpios[3].mode = PinMode.OUTPUT_HIGH
 #    time.sleep(0.2)
 #    board.gpios[2].mode = PinMode.OUTPUT_LOW
 #    board.gpios[3].mode = PinMode.OUTPUT_LOW
 #    time.sleep(0.2)