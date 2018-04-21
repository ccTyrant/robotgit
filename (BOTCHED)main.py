from robot import Robot
from robot import BRAKE, COAST
from robot import WALL, TOKEN_ZONE_0,TOKEN_ZONE_1, TOKEN_ZONE_2, TOKEN_ZONE_3, TOKEN
import time
from time import sleep
import math
r = Robot()
board = r.servo_board
zone = 2
IRPin = 0

errorMarkerID = 6969
errorMarkerDistance = 4201337

#Arduino Pin Numbers
from robot import PinMode
armBack1pos = 3
armBack1neg = 2
armBack2pos = 5
armBack2neg = 4

#Servos
RightArm = r.servo_board.servos[1]
LeftArm = r.servo_board.servos[2]
camera = r.servo_board.servos[0]
arduino = r.servo_board.gpios[2]
arduino.pin_mode = PinMode.INPUT


#tokenMarkers
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

leftPower = -0.61
rightPower = -0.65

fconst = 2.2

def Forward(dist):
    if dist > 0:
        r.motor_board.m1 = leftPower
        r.motor_board.m0 = rightPower
    else:
        r.motor_board.m1 = -leftPower
        r.motor_board.m0 = -rightPower
    time.sleep(abs(dist * fconst))
    r.motor_board.m1 = BRAKE
    r.motor_board.m0 = BRAKE
    print("forward " + str(dist) + " completed")
    time.sleep(0.2)

def ForwardTillIRHit(maxDist):#returns true if the IR has gone off, false if maxdist reached
    endTime = time.time() + fconst * maxDist
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
       time.sleep(0.2)

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
    markersSelected = []
    for x in markers:
        if x.id in IDWhitelist:
            markersSelected = markersSelected + [x]
    return markersSelected

def GetNearestMarkerInVision(IDWhitelist):
    markers = r.camera.see()
    for m in markers:
        if m.id in IDWhitelist:
            return m.id
    return errorMarkerID

def goToNearestMarkerInVision(IDWhitelist):
    print("gotonearestmarker")
    markerID = GetNearestMarkerInVision(IDWhitelist)
    if markerID != errorMarkerID:
        print("do you remember gucci gang gucci gang?")
        if goToMarker(markerID):
            armFrontClose()

def goToMarker(markerID):
    captured = False
    while not captured:
        markerSeen = False
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
        else:
            print("notseen")
            Forward(-0.5)
    return captured

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
        armFrontOpen()
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
        

def getWallMarkerZoneLeft(MarkerID):
    if MarkerID in range(0,7): 
        return 0
    elif MarkerID in range (7,14):
        return 1
    elif MarkerID in range(14,21):
        return 2
    elif MarkerID in range(21,28):
        return 3
    else:
        return errorMarkerID

def getPosition():
    wallMarkers = GetAllMarkersInVision(list(WALL))
    if wallMarkers.count >=2:
        markerA = wallMarkers[0]
        markerB = wallMarkers[1]
        alpha = markerA.spheical.rot_y_radians
        beta = markerB.spheical.rot_y_radians
        a = markerA.spheical.distance_metres
        b = markerB.spheical.distance_metres
        Ax = GetWallMarkerX(markerA.id)
        Ay = GetWallMarkerY(markerA.id)
        Bx = GetWallMarkerX(markerB.id)
        By = GetWallMarkerY(markerB.id)
        phi = beta-alpha
        BAx = Bx-Ax
        BAy = By-Ay
        magBA = BAx*BAx+BAy*BAy 

        tanDelta = (b/a)*(1/math.sin(phi))-(1/math.tan(phi))
        sinDelta = tanDelta/math.sqrt((tanDelta*tanDelta)+1)
        cosDelta = 1//math.sqrt((tanDelta*tanDelta)+1)

        phatx = BAx/magBA
        phaty = BAy/magBA
        rhatx = -phaty
        rhaty = phatx

        Rx = Bx + phatx*b*sinDelta + rhatx*b*cosDelta
        Ry = By + phaty*b*sinDelta + rhaty*b*cosDelta
        return [Rx,Ry]
    else:
        Rotate(-1)
        return getPosition()

def GetWallMarkerX(markid):
    if markid in range(7,14):
        return 8
    elif markid in range(21,28):
        return 0
    elif markid in range(0,7):
        return (markid + 1)
    elif markid in range(14,21):
        return (21-markid)
    else:
        return errorMarkerDistance

def GetWallMarkerY(markid):
    if markid in range(0,7):
        return 0
    elif markid in range(14,21):
        return 8
    elif markid in range(7,14):
        return (markid - 6)
    elif markid in range(21,28):
        return (28-markid)
    else:
        return errorMarkerDistance

def returnToZone():
    markers = r.camera.see()
    markersNearZoneRight = []
    markersNearZoneLeft = []
    markersFarFromZone = []
    if len(markers) != 0:
        for x in markers:
            if getWallMarkerZoneLeft(x.id) == zone:
                markersNearZoneRight = markersNearZoneRight + [x]
            if (getWallMarkerZoneLeft(x.id) +1)%4 == zone :
                markersNearZoneLeft = markersNearZoneLeft + [x]
            else:
                markersFarFromZone = markersFarFromZone + [x]
        if markersNearZoneRight.count != 0 or markersNearZoneLeft.count != 0:
            pass        
        else:
            Rotate(-1)
            returnToZone()
    else:
        Rotate(-1)
        returnToZone()

def armFrontClose():
    print("front")
    RightArm.position = 0.4
    print("1close")
    LeftArm.position = -0.5
    print("2close")

def armFrontOpen():
    print("front")
    RightArm.position = -0.5
    print("1open")
    LeftArm.position = 0.4
    print("2open")


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


print("THIS IS TOTALLY RUNNING")


BotchGetBlocks()
Rotate(100 * math.pi / 180)
BotchGetBack()