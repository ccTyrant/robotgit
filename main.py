from robot import Robot
from robot import BRAKE, COAST
from robot import WALL, TOKEN_ZONE_0,TOKEN_ZONE_1, TOKEN_ZONE_2, TOKEN_ZONE_3, TOKEN, COLUMN
from robot import GameMode
import time
from time import sleep
import math
from robot import PinMode, PinValue
r = Robot()
board = r.servo_board
if r.mode == GameMode.COMPETITION:
    zone = r.zone
else:
    zone = 2
IRPin = 0

errorMarkerID = 6969
errorMarkerDistance = 4201337

columnWidth = 0.37

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
    tokenMarkers = list(TOKEN_ZONE_2)
    leftWallMarkers = [32,35]
    rightWallMarkers = [36,39]

elif zone == 3:
    tokenMarkers = list(TOKEN_ZONE_3)
    leftWallMarkers = [36,37]
    rightWallMarkers = [40,41]

rPow = -0.65
lPow = -0.65

fconst = 2.2

def Forward(dist):
    if dist > 0:
        r.motor_board.m1 = rPow
        r.motor_board.m0 = lPow
    else:
        r.motor_board.m1 = -rPow
        r.motor_board.m0 = -lPow
    time.sleep(math.fabs(dist * fconst))
    r.motor_board.m1 = BRAKE
    r.motor_board.m0 = BRAKE
    print("forward " + str(dist) + " completed")
    time.sleep(0.3)

def ForwardTillIRHit(maxDist):#returns true if the IR has gone off, false if maxdist reached
    endTime = time.time() + fconst * maxDist
    r.motor_board.m1 = rPow
    r.motor_board.m0 = lPow
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
       const = 0.3
       if ang < 0:
           r.motor_board.m1 = rPow
           r.motor_board.m0 = -lPow
       else:
           r.motor_board.m1 = -rPow
           r.motor_board.m0 = lPow
       time.sleep(math.fabs(ang * const))
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
    gotMarker = False
    turnCount = 0
    while not gotMarker:
        print("gotonearestmarker")
        markerID = GetNearestMarkerInVision(IDWhitelist)
        if markerID != errorMarkerID:
            print("do you remember gucci gang gucci gang?")
            if goToMarker(markerID):
                armFrontClose()
                gotMarker = True
        elif turnCount > 10:
            Forward(-1)
            Forward(0.4)
            turnCount = 0
        else:
            Rotate(0.5)
            time.sleep(0.5)
            turnCount = turnCount + 1
            goToNearestMarkerInVision(IDWhitelist)

def goToMarker(markerID):
    captured = False
    retried = False
    alreadyClosed = False
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
                if ourMarker.distance_metres > 0.9:
                    print("closing distance")
                    Rotate(ourMarker.spherical.rot_y_radians)
                    Forward(ourMarker.spherical.distance_metres * 0.6)
                    alreadyClosed = True
                else:
                    print("going for it")
                    Rotate(ourMarker.spherical.rot_y_radians)
                    armFrontOpen()
                    if ForwardTillIRHit(ourMarker.spherical.distance_metres * 1.2):
                        time.sleep(0.5)
                        Forward(0.3)
                        captured = True
                        armFrontClose()
                    else:
                        break
                    armFrontClose()
            else:
                print("I aint seen no markers")
                armFrontOpen()
                if ForwardTillIRHit(marker.distance_metres * 1.2):
                    captured = True
                    time.sleep(0.5)
                    Forward(0.3)
                    armFrontClose()
                else:
                    break
                armFrontClose()
            if retried:
                break
        else:
            if alreadyClosed:
                armFrontOpen()
                if ForwardTillIRHit(1):
                    time.sleep(0.5)
                    Forward(0.3)
                    armFrontClose()
                    captured = True
                else:
                    break
            else:  
                retried = True
                print("notseen")
                Forward(-0.3)
    return captured

def BotchGetBack():
    inZone = False
    while not inZone:
        wallMarkers = GetAllMarkersInVision(leftWallMarkers + rightWallMarkers)
        if len(wallMarkers) > 0:
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
            Forward(2)
            inZone = False

def BotchGetBlocks():
    armFrontClose()
    Forward(-5.8)
    Rotate(math.pi)
    goToNearestMarkerInVision(tokenMarkers)
    Forward(-2)
    time.sleep(0.7)
    Forward(0.2)
    goToNearestMarkerInVision(tokenMarkers)
    Forward(-2)
    time.sleep(0.7)
    Forward(0.2)
    goToNearestMarkerInVision(tokenMarkers)

def getWallMarkerZoneLeft(MarkerID):
    if MarkerID in range(0,7): 
        return 0
    elif MarkerID in range(7,14):
        return 1
    elif MarkerID in range(14,21):
        return 2
    elif MarkerID in range(21,28):
        return 3
    else:
        return errorMarkerID


#def returnToZone():
#    pos = getPositionAndRotation()
#    if pos[0] < 4 and pos[1] < 4:
#	    goToPosition(2,1)
#	    goToPosition(6,1)
#	    goToPosition(7,3)
#	    goToPosition(7,6)
#	    goToPosition(5,5)
#	    if zone = 2:
#		    pos = getPositionAndRotation()
#		    while(pos[0] - 5) * (pos[0] - 5) + (pos[1] - 5) * (pos[1] - 5) < 1:
#			    goToPosition(5,5)
#			    pos = getPositionAndRotation()
#	    elif zone = 1:
#		    pos = getPositionAndRotation()
#		    while(pos[0] - 5) * (pos[0] - 5) + (pos[1] - 3) * (pos[1] - 3) < 1:
#			    goToPosition(5,3)
#			    pos = getPositionAndRotation()
#	    elif zone = 3:
#		    pos = getPositionAndRotation()
#		    while(pos[0] - 3) * (pos[0] - 3) + (pos[1] - 5) * (pos[1] - 5) < 1:
#			    goToPosition(3,5)
#			    pos = getPositionAndRotation()
#    elif pos[0] > 4 and pos[1] < 4:
#	    goToPosition(6,1)
#	    goToPosition(2,1)
#	    goToPosition(1,3)
#	    goToPosition(1,6)
#	    goToPosition(3,5)
#	    if zone = 2:
#		    pos = getPositionAndRotation()
#		    while(pos[0] - 5) * (pos[0] - 5) + (pos[1] - 5) * (pos[1] - 5) < 1:
#			    goToPosition(5,5)
#			    pos = getPositionAndRotation()
#	    elif zone = 0:
#		    pos = getPositionAndRotation()
#		    while(pos[0] - 3) * (pos[0] - 3) + (pos[1] - 3) * (pos[1] - 3) < 1:
#			    goToPosition(3,3)
#			    pos = getPositionAndRotation()
#	    elif zone = 3:
#		    pos = getPositionAndRotation()
#		    while(pos[0] - 3) * (pos[0] - 3) + (pos[1] - 5) * (pos[1] - 5) < 1:
#			    goToPosition(3,5)
#			    pos = getPositionAndRotation()
#    elif pos[0] > 4 and pos[1] > 4:
#	    goToPosition(7,6)
#	    goToPosition(7,3)
#	    goToPosition(6,1)
#	    goToPosition(2,1)
#	    goToPosition(3,3)
#	    if zone = 2:
#		    pos = getPositionAndRotation()
#		    while(pos[0] - 5) * (pos[0] - 5) + (pos[1] - 5) * (pos[1] - 5) < 1:
#			    goToPosition(5,5)
#			    pos = getPositionAndRotation()
#	    elif zone = 1:
#		    pos = getPositionAndRotation()
#		    while(pos[0] - 5) * (pos[0] - 5) + (pos[1] - 3) * (pos[1] - 3) < 1:
#			    goToPosition(5,3)
#			    pos = getPositionAndRotation()
#	    elif zone = 3:
#		    pos = getPositionAndRotation()
#		    while(pos[0] - 3) * (pos[0] - 3) + (pos[1] - 5) * (pos[1] - 5) < 1:
#			    goToPosition(3,5)
#			    pos = getPositionAndRotation()
#    elif pos[0] < 4 and pos[1] > 4:
#	    goToPosition(1,6)
#	    goToPosition(1,3)
#	    goToPosition(3,1)
#	    goToPosition(6,1)
#	    goToPosition(5,3)
#	    if zone = 2:
#		    pos = getPositionAndRotation()
#		    while(pos[0] - 5) * (pos[0] - 5) + (pos[1] - 5) * (pos[1] - 5) < 1:
#			    goToPosition(5,5)
#			    pos = getPositionAndRotation()
#	    elif zone = 1:
#		    pos = getPositionAndRotation()
#		    while(pos[0] - 5) * (pos[0] - 5) + (pos[1] - 3) * (pos[1] - 3) < 1:
#			    goToPosition(5,3)
#			    pos = getPositionAndRotation()
#	    elif zone = 0:
#		    pos = getPositionAndRotation()
#		    while(pos[0] - 5) * (pos[0] - 5) + (pos[1] - 5) * (pos[1] - 5) < 1:
#			    goToPosition(5,5)
#			    pos = getPositionAndRotation()

#zones 0,1,2,3
#dead zones 4,5,6,7
def coordZone(x,y):
	if x < 1:
		if y > 4:
			return 7
		else:
			return 4
	elif x < 4:
		if y < 1:
			return 4
		elif y < 4:
			return 0
		elif y < 7:
			return 3
		else:
			return 7
	elif x < 7:
		if y < 1:
			return 5
		elif y < 4:
			return 1
		elif y < 7:
			return 2
		else:
			return 6
	else:
		if y > 4:
			return 6
		else:
			return 5
			
#like coordZone but no dead zones
def coordCorner(x,y):
	cZone = coordZone(x,y)
	return (cZone % 4)
			
#nodes: 0 = centre, 1=left (from centre of arena), 2=right (from centre of
#arena)
def goToNode(corner, node):
    print("--going to corner " + str(corner) + " node " + str(node))
    if not node in range(0,4):
        print("poo bum node " + node)
    if node == 4:
        goToPosition(4,4)
    elif corner == 0:
        if node == 0:
            goToPosition(2,2)
        elif node == 1:
            goToPosition(1,3.5)
        elif node == 2:
            goToPosition(3.5,1)
            
    elif corner == 1:
        if node == 0:
            goToPosition(6,2)
        elif node == 1:
            goToPosition(4.5,1)
        elif node == 2:
            goToPosition(1,3.5)
        
    elif corner == 2:
        if node == 0:
            goToPosition(6,6)
        elif node == 1:
            goToPosition(7,4.5)
        elif node == 2:
            goToPosition(4.5,7)
        
    elif corner == 3:
        if node == 0:
            goToPosition(2,6)
        elif node == 1:
            goToPosition(3.5,7)
        elif node == 2:
            goToPosition(1,4.5) 
    else:
        print("poo bum corner " + str(corner))

def moveToDesiredZone(desiredZone):
	print("moving to zone " + str(desiredZone))
	pos = getPositionAndRotation()
	x = pos[0]
	y = pos[1]
	currentCorner = coordCorner(x,y)
	if currentCorner == desiredZone:
		print("already in zone " + str(desiredZone))
		goToNode(currentCorner, 0)
	elif currentCorner == (desiredZone - 1) % 4:
		print("Left of zone " + str(desiredZone) + " in zone" + str(currentCorner) + ". Moving to desired zone")
		goToNode(currentCorner,2)
		goToNode(desiredZone,1)
		goToNode(desiredZone,0)
	elif currentCorner == (desiredZone + 1) % 4:
		print("Right of zone " + str(desiredZone) + " in zone" + str(currentCorner) + ". Moving to desired zone")
		goToNode(currentCorner,1)
		goToNode(desiredZone,2)
		goToNode(desiredZone,0)
	else:
		print("in opposite zone to " + str(desiredZone) + ", " + str(currentCorner) + ". Moving to zone " + str((currentCorner - 1) % 4) + " and retrying")
		goToNode(currentCorner,1)
		goToNode((currentCorner - 1) % 4,2)
		moveToDesiredZone(desiredZone)
	
def getPositionAndRotation():
    time.sleep(0.4)
    wallMarkers = GetAllMarkersInVision(list(WALL) + list(COLUMN))
    if len(wallMarkers) >= 2:	
		#markers
        markerA = wallMarkers[0]
        markerB = wallMarkers[1]
		#start info
        alpha = markerA.spherical.rot_y_radians
        beta = markerB.spherical.rot_y_radians
        a = markerA.spherical.distance_metres
        b = markerB.spherical.distance_metres
        Ax = GetWallMarkerX(markerA.id)
        Ay = GetWallMarkerY(markerA.id)
        Bx = GetWallMarkerX(markerB.id)
        By = GetWallMarkerY(markerB.id)
		#derived info
        phi = beta - alpha
        BAx = Ax-Bx
        BAy = Ay-By
        magBA = math.sqrt(BAx * BAx + BAy * BAy)

        print("phi=" + str(phi) + " a=" + str(a) + " b=" + str(b))
        print("A=(" + str(Ax) + "," + str(Ay) + ") B=(" + str(Bx) + "," + str(By) + ")")

		#angle calculation
        tanDelta = (b / a)*(1 / math.sin(phi)) - (1 / math.tan(phi))
        sinDelta = tanDelta / math.sqrt((tanDelta * tanDelta) + 1)
        cosDelta = 1 // math.sqrt((tanDelta * tanDelta) + 1)

		#unit vectors
        phatx = BAx / magBA
        phaty = BAy / magBA
        rhatx = phaty
        rhaty = -phatx

		#robot position
        Rx = Bx + phatx * b * sinDelta + rhatx * b * cosDelta
        Ry = By + phaty * b * sinDelta + rhaty * b * cosDelta

		#robot rotation
        if By-Ry != 0:
            theta = beta - math.atan((Bx - Rx) / (By - Ry))
        else:
            theta = beta - math.pi/2
        print("position is (" + str(Rx) + "," + str(Ry) + ") at angle " + str(theta))
        return [Rx,Ry,theta]
    else:
        Rotate(-1)
        return getPositionAndRotation()

def sgn(t):
	if t == 0:
		return 0
	else:
		return t / math.fabs(t)
		
def goToPosition(x1,y1):
	print("-going to (" + str(x1) + "," + str(y1) + ")")
	pos = getPositionAndRotation()
	#start info
	x0 = pos[0]
	y0 = pos[1]
	theta = pos[2]
	#derived info
	deltay = y1 - y0
	deltax = x1 - x0
	#angle calculation
	rotateAngle = theta + math.atan(deltay / deltax) + (sgn(deltax) * math.pi / 2)
	Rotate(rotateAngle)
	#large angle error correction
	if rotateAngle < math.pi / 4:
		dist = math.sqrt(deltax * deltax + deltay * deltay)
		Forward(dist)
		#large distance error correction
		if dist > 1.5:
			print("distance correction")
			goToPosition(x1,y1)
	else:
		print("angle correction")
		goToPosition(x1,y1)
		
def GetWallMarkerX(markid):
    if markid in range(7,14):
        return 8
    elif markid in range(21,28):
        return 0
    elif markid in range(0,7):
        return (markid + 1)
    elif markid in range(14,21):
        return (21 - markid)
    elif markid in COLUMN:
		#north
        if markid in range(28,32):
            return 4 + columnModifyX(markid - 28)
		#east
        if markid in range(32,36):
            return 6 + columnModifyX(markid - 32)
		#south
        if markid in range(36,40):
            return 4 + columnModifyX(markid - 36)
		#west
        if markid in range(40,44):
            return 2 + columnModifyX(markid - 40)
    else:
        return errorMarkerDistance

def columnModifyX(t):
	if t == 0:
		return 0
	elif t == 1:
		return columnWidth / 2
	elif t == 2:
		return 0
	elif t == 3:
		return -columnWidth / 2
		
def GetWallMarkerY(markid):
    if markid in range(0,7):
        return 0
    elif markid in range(14,21):
        return 8
    elif markid in range(7,14):
        return (markid - 6)
    elif markid in range(21,28):
        return (28 - markid)
    elif markid in COLUMN:
		#north
        if markid in range(28,32):
            return 2 + columnModifyY(markid - 28)
		#east
        if markid in range(32,36):
            return 4 + columnModifyY(markid - 32)
		#south
        if markid in range(36,40):
            return 6 + columnModifyY(markid - 36)
		#west
        if markid in range(40,44):
            return 4 + columnModifyY(markid - 40)
    else:
        return errorMarkerDistance

def columnModifyY(t):
	if t == 0:
		return -columnWidth / 2
	elif t == 1:
		return 0
	elif t == 2:
		return columnWidth / 2
	elif t == 3:
		return 0

def armFrontClose():
    print("front")
    RightArm.position = 0.6
    print("1close")
    LeftArm.position = -1.0
    print("2close")
    time.sleep(0.1)

def armFrontOpen():
    print("front")
    RightArm.position = -0.5
    print("1open")
    LeftArm.position = 0.0
    print("2open")
    time.sleep(0.1)

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
moveToDesiredZone(zone)