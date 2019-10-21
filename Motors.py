#Motor Movement Code

import time
import RPi.GPIO as GPIO # for GPIO control
from threading import Thread, Lock # Threading to move all motors at increments of 1 simultaneously
import Adafruit_PCA9685 # Adafruit library for the 16-channel PWM control

# lock a thread when setting the motor angle at each increment
cur_angle_mutex = Lock()
i2c_mutex = Lock()

#initialize the adafruit library to default i2c adress 0x40
pwm = Adafruit_PCA9685.PCA9685()
pwm.set_pwm_freq(60) #set the pwm frequency to 60, good for motors

# Servo pulse based tested for the motors 0 - 100
servo_min = 128  # Min pulse length out of 4096 ~0.5
servo_max = 620  # Max pulse length out of 4096 ~2.5

move_delay = 0.0005 #delay in seconds (0.5ms) between increment of movement
step_delay = 0.001 #delay 1ms between different stances

#start the robot at 90 degrees of the motor
"""   
side view of the robot with motors at 90 ddegrees
                  _____
        |o---o---o|---|o---o---o|
        |                       |       "o" is the motors  
        |                       |

top-down view of the robot with motors at 90 ddegrees

        --o-o---o|----|o---o-o--
                 |    |                 "o" is the motors
        --o-o---o|----|o---o-o--
"""

#the following is how many degrees to offset each 
# angles to get the closest values to 90 degrees
# each leg has 3 motors 
leg1_offset = [11, -6, -4]
leg2_offset = [-13, -4, 4]
leg3_offset = [4, 5, -5]
leg4_offset = [0, -4, -5]

#following angles are the angles for each each stance
# parallel is when the legs are parallel to each other and to the body 
# lateral is when they are "opened out"
front_lateral = 40
front_parallel = 90
front_lateral_add = -30

back_lateral = 140
back_parallel = 90
back_lateral_add = 30

#for the legs and when they get lifted up
footup = 0
footdown = 60
footstand = 110
footsit = 20

#small pincer adjustment to help when lifting the leg and compensating and 
# keeping distance to body correct when moving and shifting body
pincer_up = 130
pincer_down = 120
pincer_stand = 70
pincer_sit = 160

#set the legs to being on the floor as a start
leg1_footdown = footdown
leg2_footdown = footdown
leg3_footdown = footdown
leg4_footdown = footdown

#start formation is the one where the formation starts with the right side being 
# parallel and the left side having the legs set to the lateral position
"""
The "leg_formation = 1" stance
       \         
        \o _______ o_____
          |       |
         o|_______|o_____
        /
       /
"""
leg_formation = 1

#stores all the current angle of the motors, that was set for them
# when incremented this keeps the incremented angle
channel_cur = [90,90,90,90,90,90,90,90,90,90,90,90]

#test function ran when this file is the main one
# test out if the stances work
# __main__
def main():
    begin()
    pwm.set_pwm(12,0, 374)
    time.sleep(2)
    
    left()
     
    stand()
    time.sleep(4)
    
    shake()
    time.sleep(4)
    
    forward()
    forward()
    forward()
    time.sleep(4)
    
    pwm.set_pwm(12,0,497)
    time.sleep(2)
    left()
    pwm.set_pwm(12,0,374)
    time.sleep(1)
    for i in range (8):
        forward()

#-----------
#Aways lift the leg in a parallel side.
#-----------

#only ran at the beginning and sets the robot stance to the first one 
#leg_formation = 1
def begin():
    global leg_formation

    leg1(front_parallel,footdown,pincer_down) #leftside
    leg2(back_parallel,footdown,pincer_down)

    leg3(back_lateral,footdown,pincer_down)#rightside
    leg4(front_lateral,footdown,pincer_down)

    leg_formation = 1
    
#the function sets the stance to the leg_formation  = 1
# specific stance is reset to it here
def set_to_rest():
    global leg_formation  
    #if the leg_formation is already at 1, do nothing
    if (leg_formation == 1):
        pass
        
    # if the leg formation is at 2, then reset it using following motion
    elif (leg_formation == 2):
        #sets the leg 3 to lateral
        leg3(back_parallel,footup, pincer_up)
        time.sleep(0.1)
        leg3(back_lateral, footdown, pincer_down)
        time.sleep(0.1)
        
        #sets leg 4 to lateral
        leg4(front_parallel, footup, pincer_up)
        time.sleep(0.1)
        leg4(front_lateral, footdown, pincer_down) 
        time.sleep(0.1)
        
        #sets the leg 1 to parallel
        leg1(front_lateral, footup, pincer_up)
        time.sleep(0.1)
        leg1(front_parallel, footdown, pincer_down)
        time.sleep(0.1)
        
        #sets the leg 2 to parallel
        leg2(back_lateral, footup, pincer_up)
        time.sleep(0.1)
        leg2(back_parallel, footdown, pincer_down)
        time.sleep(0.1)
        
        
    #if the leg formation is at 3 or 4 (stand or sit), then perform the following changes
    elif (leg_formation == 3 or leg_formation == 4):
        #set the legs to the current angle, while leaving making the legs be in the rest position
        t1 = Thread(target=leg1, args=(channel_cur[0], footdown, pincer_down, 3))
        t2 = Thread(target=leg2, args=(channel_cur[3], footdown, pincer_down, 3))
        t3 = Thread(target=leg3, args=(channel_cur[6], footdown, pincer_down, 3))
        t4 = Thread(target=leg4, args=(channel_cur[9], footdown, pincer_down, 3))
        
        t1.start()
        t2.start()
        t3.start()
        t4.start()
        
        t1.join()
        t2.join()
        t3.join()
        t4.join()
        # after they have been moved to the legs on the floor angles 
        # start changing the position of the legs to match the leg_formation = 1
        
        time.sleep(0.1)
        
        #sets leg 1 to parallel
        leg1(channel_cur[0], footup, pincer_up)
        time.sleep(step_delay)
        leg1(front_parallel,footdown,pincer_down) #leftside
        time.sleep(step_delay)
        
        #sets leg 2 to parallel
        leg2(channel_cur[3], footup, pincer_up)
        time.sleep(step_delay)
        leg2(back_parallel,footdown,pincer_down)
        time.sleep(step_delay)
        
        #sets leg 3 to lateral
        leg3(channel_cur[6], footup, pincer_up)
        time.sleep(step_delay)
        leg3(back_lateral,footdown,pincer_down)#rightside
        time.sleep(step_delay)
        
        #sets leg 4 to lateral
        leg4(channel_cur[9], footup, pincer_up)
        time.sleep(step_delay)
        leg4(front_lateral,footdown,pincer_down)
        
    #sets leg_formation variable to 1
    leg_formation = 1
    time.sleep(0.5)
    
    
# this function sets the robot to a standing poition
def stand():
    global leg_formation 
    
    # spreads the legs 1 by one to lateral position then it extends them to
    #  put the robot at a higher position
    if (leg_formation == 1):
        leg1(front_parallel,footup,pincer_up)
        time.sleep(step_delay)
        #sets leg 1 to lateral
        leg1(front_lateral,footup,pincer_up)
        time.sleep(step_delay)

        leg1(front_lateral,footdown,pincer_down)
        time.sleep(step_delay)

        #sets leg to to lateral
        leg2(back_parallel,footup,pincer_up)
        time.sleep(step_delay)

        leg2(back_lateral,footup,pincer_up)
        time.sleep(step_delay)

        leg2(back_lateral,footdown,pincer_down)
        time.sleep(0.5)
        
    # same thing as the other one but if the leg was in the leg_frormation = 2
    elif (leg_formation == 2):
        #sets leg 3 to lateral
        leg3(back_parallel,footup,pincer_up)
        time.sleep(step_delay)

        leg3(back_lateral,footup,pincer_up)
        time.sleep(step_delay)

        leg3(back_lateral,footdown,pincer_down)
        time.sleep(step_delay)

        #sets leg 4 to lateral
        leg4(front_parallel,footup,pincer_up)
        time.sleep(step_delay)

        leg4(front_lateral,footup,pincer_up)
        time.sleep(step_delay)

        leg4(front_lateral,footdown,pincer_down)
        time.sleep(0.5)
    
    # use threading to move them all at the same time , extending the legs all at 
    # once so they wont lose balance by being set 1 at a time
    t1 = Thread(target=leg1, args=(front_lateral, footstand, pincer_stand, 3))
    t2 = Thread(target=leg2, args=(back_lateral, footstand, pincer_stand, 3))
    t3 = Thread(target=leg3, args=(back_lateral, footstand, pincer_stand, 3))
    t4 = Thread(target=leg4, args=(front_lateral, footstand, pincer_stand, 3))
    
    t1.start()
    t2.start()
    t3.start()
    t4.start()
    
    t1.join()
    t2.join()
    t3.join()
    t4.join()
    
    # set the leg_formation to 3, for standing
    leg_formation = 3

#sets the robot to sitting position
#this is done by bringing all the legs closest to each other
# like it is being crumpled
def sit():
    global leg_formation 
    #depending on the current stance, set the legs to the position of them all being lateral
    if (leg_formation == 1):
        #LEG 1
        # lifts foot up from being parallel 
        leg1(front_parallel,footup,pincer_up)
        time.sleep(step_delay)
        # sets foot at lateral position while still being up
        leg1(front_lateral,footup,pincer_up)
        time.sleep(step_delay)
        # puts leg down at lateral
        leg1(front_lateral,footdown,pincer_down)
        time.sleep(step_delay)

        #LEG 2
        # lifts foot up from being parallel 
        leg2(back_parallel,footup,pincer_up)
        time.sleep(step_delay)
        # sets foot at lateral position while still being up
        leg2(back_lateral,footup,pincer_up)
        time.sleep(step_delay)
        # puts leg down at lateral
        leg2(back_lateral,footdown,pincer_down)
        time.sleep(0.5)
        
    if (leg_formation == 2):
        #LEG 3
        # lifts foot up from being parallel 
        leg3(back_parallel,footup,pincer_up)
        time.sleep(step_delay)
        # sets foot at lateral position while still being up
        leg3(back_lateral,footup,pincer_up)
        time.sleep(step_delay)
        # puts leg down at lateral
        leg3(back_lateral,footdown,pincer_down)
        time.sleep(step_delay)

        #LEG 4
        #lifts leg from parallel 
        leg4(front_parallel,footup,pincer_up)
        time.sleep(step_delay)
        #sets foot to lateral angle
        leg4(front_lateral,footup,pincer_up)
        time.sleep(step_delay)
        #puts foot down at lateral
        leg4(front_lateral,footdown,pincer_down)
        time.sleep(0.5)
    
    # make them all crumple together using threading
    t1 = Thread(target=leg1, args=(front_lateral, footsit, pincer_sit, 3))
    t2 = Thread(target=leg2, args=(back_lateral, footsit, pincer_sit, 3))
    t3 = Thread(target=leg3, args=(back_lateral, footsit, pincer_sit, 3))
    t4 = Thread(target=leg4, args=(front_lateral, footsit, pincer_sit, 3))
    
    t1.start()
    t2.start()
    t3.start()
    t4.start()
    
    t1.join()
    t2.join()
    t3.join()
    t4.join()
    
    # sets the formation to 
    leg_formation = 4
    
def shake():
    global leg_formation
    #uses the set to rest function to put robot at leg_formation = 1
    set_to_rest()
    
    #lifts leg up
    leg1(front_lateral, footup, pincer_stand)
    time.sleep(1)

    #shakes leg
    leg1(front_lateral, footup, pincer_stand+30, 5)
    time.sleep(0.5)
    leg1(front_lateral, footup, pincer_stand, 5)
    time.sleep(0.5)
    leg1(front_lateral, footup, pincer_stand+30, 5)
    time.sleep(0.5)
    leg1(front_lateral, footup, pincer_down, 5)
    time.sleep(2)
    leg1(front_parallel, footup, pincer_up)
    time.sleep(step_delay)
    #puts leg down after shaking pincer
    leg1(front_parallel, footdown, pincer_down)
    
def forward():
    global leg_formation
    if (leg_formation == 3 or leg_formation == 4):
        set_to_rest()

    #print (leg_formation)
    
    if(leg_formation == 1):
        #lift leg1
        leg1(front_parallel,footup,pincer_up)
        time.sleep(step_delay)
        #set leg1 to lateral position
        leg1(front_lateral,footup,pincer_up)
        time.sleep(step_delay)
        #set leg1 down 
        leg1(front_lateral,footdown,pincer_down)
        time.sleep(step_delay)

        #send leg2 to lateral, and leg4 to parallel, keep leg3 in lateral with angle fix 
        # as the body of the robot will scooch forward and the angle of the leg for the pincer to 
        # be in the exact same position on the ground when it has moved
        t2 = Thread(target=leg2, args=(back_lateral,footdown,pincer_down))
        t3 = Thread(target=leg3, args=(back_lateral+back_lateral_add,footdown,pincer_down))
        t4 = Thread(target=leg4, args=(front_parallel,footdown,pincer_down))

        t2.start()
        t3.start()
        t4.start()

        t2.join()
        t3.join()
        t4.join()
  
        #set leg3 and bring to parallel position after the robot moves forward
        #lift leg 3
        leg3(back_lateral+back_lateral_add,footup,pincer_up)
        time.sleep(step_delay)
        #move leg3 to parallel position 
        leg3(back_parallel,footup,pincer_up)
        time.sleep(step_delay)
        #set leg3 down
        leg3(back_parallel,footdown,pincer_down)
        time.sleep(step_delay)

        #now right side legs are parallel and left side legs are lateral
        #this will put the robot at leg_formation = 2

    #same thing as in leg_formation = 1 but just the opposit side of the robot and its legs
    if (leg_formation == 2):
        #lift leg4
        leg4(front_parallel,footup,pincer_up)
        time.sleep(step_delay)
        #move leg4 to lateral position
        leg4(front_lateral,footup,pincer_up)
        time.sleep(step_delay)
        #set leg4 down
        leg4(front_lateral,footdown,pincer_down)
        time.sleep(step_delay)

        # sending leg3 to lateral, and leg1 to parallel to move it forward
        #leg 2 has a small compensation angle to keep robot foot same spot on ground and movement smooth
        t3 = Thread(target=leg3, args=(back_lateral,footdown,pincer_down))
        t2 = Thread(target=leg2, args=(back_lateral+back_lateral_add,footdown,pincer_down))
        t1 = Thread(target=leg1, args=(front_parallel,footdown,pincer_down))
        t3.start()
        t2.start()
        t1.start()
        
        t3.join()
        t2.join()
        t1.join()
        time.sleep(step_delay)

        #lift leg2 and bring to parallel position after the robot moves
        leg2(back_lateral+back_lateral_add,footup,pincer_up)
        time.sleep(step_delay)
        #move leg2 to lateral position
        leg2(back_parallel,footup,pincer_up)
        time.sleep(step_delay)
        #bring leg2 down
        leg2(back_parallel,footdown,pincer_down)
        time.sleep(step_delay)

        #now left side legs are parallel and right side legs are lateral
        # and the robot is in the the leg_formation = 1

    #set the leg_formation variables to correct value
    if(leg_formation == 1):
        leg_formation = 2
    elif(leg_formation == 2):
        leg_formation = 1

# the same as the forward function but going backwards
def backward():
    global leg_formation
    
    if (leg_formation == 3 or leg_formation == 4):
        set_to_rest()
    
    if(leg_formation == 1):
        #lift leg2
        leg2(back_parallel,footup,pincer_up)
        time.sleep(step_delay)
        #move leg2 to lateral position
        leg2(back_lateral,footup,pincer_up)
        time.sleep(step_delay)
        #bring leg2 down 
        leg2(back_lateral,footdown,pincer_down)
        time.sleep(step_delay)

        #send leg1 to lateral, and leg3 to parallel,
        t1 = Thread(target=leg1, args=(front_lateral,footdown,pincer_down))
        t3 = Thread(target=leg3, args=(back_parallel,footdown,pincer_down))
        t4 = Thread(target=leg4, args=(front_lateral+front_lateral_add,footdown,pincer_down))

        t1.start()
        t3.start()
        t4.start()

        t1.join()
        t3.join()
        t4.join()
  

        #lift leg4 and bring to parallel position

        #lift
        leg4(front_lateral+front_lateral_add,footup,pincer_up)
        time.sleep(step_delay)
        #move leg3 to parallel position
        leg4(front_parallel,footup,pincer_up)
        time.sleep(step_delay)
        #bring leg3 down
        leg4(front_parallel,footdown,pincer_down)
        time.sleep(step_delay)

        #now right side legs are parallel and left side legs are lateral

        

    if (leg_formation == 2):
        #lift leg3
        leg3(back_parallel,footup,pincer_up)
        time.sleep(step_delay)
        #move leg3 to lateral position
        leg3(back_lateral,footup,pincer_up)
        time.sleep(step_delay)
        #bring leg4 down
        leg3(back_lateral,footdown,pincer_down)
        time.sleep(step_delay)

        
        t4 = Thread(target=leg4, args=(front_lateral,footdown,pincer_down))
        t2 = Thread(target=leg2, args=(back_parallel,footdown,pincer_down))
        t1 = Thread(target=leg1, args=(front_lateral+front_lateral_add,footdown,pincer_down))
        t4.start()
        t2.start()
        t1.start()
        
        t4.join()
        t2.join()
        t1.join()
        time.sleep(step_delay)

        #lift leg1 and bring to parallel position
        leg1(front_lateral+front_lateral_add,footup,pincer_up)
        time.sleep(step_delay)
        #move leg1 to lateral position
        leg1(front_parallel,footup,pincer_up)
        time.sleep(step_delay)
        #bring leg1 down
        leg1(front_parallel,footdown,pincer_down)
        time.sleep(step_delay)

        #now left side legs are parallel and right side legs are lateral


    if(leg_formation == 1):
        leg_formation = 2
    elif(leg_formation == 2):
        leg_formation = 1

# function to turn the robot left
# this function was supposed to be able to take in specific angles from the amount the camera rotated 
# and to rotate the same amount as it so that it could accurately walk towards the recognized object
# was not implemented due to time
def left():
    global leg_formation
    # if the robot is either standng or sitting, set them to rest position first
    if (leg_formation == 3 or leg_formation == 4):
        set_to_rest()
    
    #if the robot is in the leg_formation = 1
    if(leg_formation == 1):
        #lift leg1
        leg2(back_parallel,footup,pincer_up)
        time.sleep(step_delay)
        #move leg1 to lateral position
        leg2(back_lateral,footup,pincer_up)
        time.sleep(step_delay)

        #send leg2 to lateral, and leg4 to parallel, keep leg3 in lateral
        #this performs the rotating action after all the legs have been placed in the correct
        t1 = Thread(target=leg1, args=(front_lateral,footdown,pincer_down))
        t3 = Thread(target=leg3, args=(back_lateral+back_lateral_add,footdown,pincer_down))
        t4 = Thread(target=leg4, args=(front_parallel,footdown,pincer_down))

        t1.start()
        t3.start()
        t4.start()

        #bring leg1 down
        leg2(back_lateral,footdown,pincer_down)
        time.sleep(step_delay)

        t1.join()
        t3.join()
        t4.join()


        #lift leg3 and bring to parallel position

        #lift
        leg3(back_lateral+back_lateral_add,footup,pincer_up)
        time.sleep(step_delay)
        #move leg3 to parallel position
        leg3(back_parallel,footup,pincer_up)
        time.sleep(step_delay)
        #bring leg3 down
        leg3(back_parallel,footdown,pincer_down)
        time.sleep(step_delay)

        #now right side legs are parallel and left side legs are lateral

        

    if (leg_formation == 2):
        #lift leg4
        leg4(front_parallel,footup,pincer_up)
        time.sleep(step_delay)
        #move leg4 to lateral position
        leg4(front_lateral,footup,pincer_up)
        time.sleep(step_delay)

        # sending leg3 to lateral, and leg1 to parallel
        t3 = Thread(target=leg3, args=(back_lateral,footdown,pincer_down))
        t2 = Thread(target=leg2, args=(back_parallel,footdown,pincer_down))
        t1 = Thread(target=leg1, args=(front_lateral+front_lateral_add,footdown,pincer_down))
        t3.start()
        t2.start()
        t1.start() 

        #bring leg4 down
        leg4(front_lateral,footdown,pincer_down)

        t3.join()
        t2.join()
        t1.join()
        time.sleep(step_delay)

        #lift leg1 
        leg1(front_lateral+front_lateral_add,footup,pincer_up)
        time.sleep(step_delay)
        #move leg1 to prallel position
        leg1(front_parallel,footup,pincer_up)
        time.sleep(step_delay)
        #bring leg1 down
        leg1(front_parallel,footdown,pincer_down)
        time.sleep(step_delay)

        #now left side legs are parallel and right side legs are lateral
        # after the robot finishes moving


    # leg_formation toggles between 1 and 2
    if(leg_formation == 1):
        leg_formation = 2
    elif(leg_formation == 2):
        leg_formation = 1


# same as left but the robot will be turning right here
def right():
    global leg_formation
    
    if (leg_formation == 3 or leg_formation == 4):
        set_to_rest()
    
    if(leg_formation == 1):
        #lift leg1
        leg1(front_parallel,footup,pincer_up)
        time.sleep(step_delay)
        #move leg1 to lateral position
        leg1(front_lateral,footup,pincer_up)
        time.sleep(step_delay)

        #send leg2 to lateral, and leg4 to lateral+, and leg3 parallel
        t2 = Thread(target=leg2, args=(back_lateral,footdown,pincer_down))
        t3 = Thread(target=leg3, args=(back_parallel,footdown,pincer_down))
        t4 = Thread(target=leg4, args=(front_lateral+front_lateral_add,footdown,pincer_down))

        t2.start()
        t3.start()
        t4.start()

        #bring leg1 down
        leg1(front_lateral,footdown,pincer_down)
        time.sleep(step_delay)

        t2.join()
        t3.join()
        t4.join()


        #lift leg4 and bring to parallel position

        #lift leg 4
        leg4(front_lateral+front_lateral_add,footup,pincer_up)
        time.sleep(step_delay)
        #move leg4 to parallel position
        leg4(front_parallel,footup,pincer_up)
        time.sleep(step_delay)
        #bring leg4 down
        leg4(front_parallel,footdown,pincer_down)
        time.sleep(step_delay)

        #now right side legs are parallel and left side legs are lateral
        # after the robot moves

        
    if (leg_formation == 2):
        #lift leg3
        leg3(back_parallel,footup,pincer_up)
        time.sleep(step_delay)
        #move leg4 to lateral position
        leg3(back_lateral,footup,pincer_up)
        time.sleep(step_delay)

        # sending leg1 to lateral, and leg4 to lateral and leg2 to lateral+
        t1 = Thread(target=leg1, args=(front_parallel,footdown,pincer_down))
        t4 = Thread(target=leg4, args=(front_lateral,footdown,pincer_down))
        t2 = Thread(target=leg2, args=(back_lateral+back_lateral_add,footdown,pincer_down))
        t1.start()
        t4.start()
        t2.start() 

        #bring leg3 down
        leg3(back_lateral,footdown,pincer_down)

        t1.join()
        t4.join()
        t2.join()
        time.sleep(step_delay)

        #lift leg2
        leg2(back_lateral+back_lateral_add,footup,pincer_up)
        time.sleep(step_delay)
        #move leg1 to prallel position
        leg2(back_parallel,footup,pincer_up)
        time.sleep(step_delay)
        #bring leg1 down
        leg2(back_parallel,footdown,pincer_down)
        time.sleep(step_delay)

        #now left side legs are parallel and right side legs are lateral
        # after the robot moves

    # toggles between leg_formation 1 and 2
    if(leg_formation == 1):
        leg_formation = 2
    elif(leg_formation == 2):
        leg_formation = 1


# based on the servo direction from 0-180 physocally on the robot
# (motor rotations for the servos based on how they were installed in the robot could have 
# 180 be the direction of 0 for the same part on the opposite end for a differen leg)

# 180 is the positive direction based on how the robot was designed
def setServo(channel,angle):
    # if the angle is greater than 180 or less than 0 set it to 180 and 0 respectively
    if(angle<0):
        angle = 0
    elif(angle>180):
        angle = 180
    
    # Lock the thread whe setting the angle pwm to the motor then release the thread
    # 128 + 2.73*angle so 0 degrees in pwm + 128 (128 is the lowest aka 0 degrees in pwm)
    i2c_mutex.acquire()
    pwm.set_pwm(channel,0,(int)((angle*2.73)+128))
    i2c_mutex.release()

# 180 is the negative direction based on how the robot was designed 0 is 180 and 180 is 0
def setServo_invert(channel,angle):
    # if the angle is greater than 180 or less than 0 set it to 180 and 0 respectively
    if(angle<0):
        angle = 0
    elif(angle>180):
        angle = 180

    # Lock the thread whe setting the angle pwm to the motor then release the thread
    # negative value of the pwm added to 620 (620 is the value of 180 in pwm) so the pwm of lower
    # angles will correspond to (180 - 0) as (0 - 180) 
    i2c_mutex.acquire()
    pwm.set_pwm(channel,0,(int)((angle*-2.73)+620))
    i2c_mutex.release()

    
# Leg 1 is the set of motors from the channel_cur at position (0 - 2)
# the shoulder motor the leg motor and the pincer motor
def leg1(angle1,angle2,angle3, delay_multiplier = 1):
    # add the offsets of each motor to get their true values in the real world
    angle1 = angle1+leg1_offset[0]
    angle2 = angle2+leg1_offset[1]
    angle3 = angle3+leg1_offset[2]

    # while the angles don't match the designated angle, keep incrementing the angle till 
    # the desired angle is reached
    while(channel_cur[0] != angle1 or channel_cur[1] != angle2 or channel_cur[2] != angle3 ):
        ##ANGLE1
        # increment the angle if the desired angle is greater than current one 
        if angle1 > channel_cur[0]:
            channel_cur[0] = channel_cur[0] +1
            setServo_invert(0,channel_cur[0]) #this motor is inverted angle
        #decrement  the angle of the motor if the desired angle is less than the current motor angle
        elif angle1 < channel_cur[0]:
            channel_cur[0] = channel_cur[0] -1
            setServo_invert(0,channel_cur[0]) # ^^^ inverted motor angle

        ##ANGLE2
        # same as the angle 1, and the motor angle is also inverted 
        if angle2 > channel_cur[1]:
            channel_cur[1] = channel_cur[1] +1
            setServo_invert(1,channel_cur[1])
        elif angle2 < channel_cur[1]:
            channel_cur[1] = channel_cur[1] -1
            setServo_invert(1,channel_cur[1])

        ##ANGLE3
        # same thing, but this motor angle is unturned and the correct direction
        if angle3 > channel_cur[2]:
            channel_cur[2] = channel_cur[2] +1
            setServo(2,channel_cur[2])
        elif angle3 < channel_cur[2]:
            channel_cur[2] = channel_cur[2] -1
            setServo(2,channel_cur[2])

        time.sleep(move_delay*delay_multiplier)


        
#same as leg 1, but motors of this leg are the ones at 3-5
def leg2(angle1,angle2,angle3, delay_multiplier = 1):
    angle1 = angle1+leg2_offset[0]
    angle2 = angle2+leg2_offset[1]
    angle3 = angle3+leg2_offset[2]

    while(channel_cur[3] != angle1 or channel_cur[4] != angle2 or channel_cur[5] != angle3 ):
    ##ANGLE1
        if angle1 > channel_cur[3]:
            channel_cur[3] = channel_cur[3] +1
            setServo_invert(3,channel_cur[3])
        elif angle1 < channel_cur[3]:
            channel_cur[3] = channel_cur[3] -1
            setServo_invert(3,channel_cur[3])

        ##ANGLE2
        if angle2 > channel_cur[4]:
            channel_cur[4] = channel_cur[4] +1
            setServo_invert(4,channel_cur[4])
        elif angle2 < channel_cur[4]:
            channel_cur[4] = channel_cur[4] -1
            setServo_invert(4,channel_cur[4])

        ##ANGLE3
        if angle3 > channel_cur[5]:
            channel_cur[5] = channel_cur[5] +1
            setServo(5,channel_cur[5])
        elif angle3 < channel_cur[5]:
            channel_cur[5] = channel_cur[5] -1
            setServo(5,channel_cur[5])

        time.sleep(move_delay*delay_multiplier)

    
#same as leg 1 and leg 2, but motors of this leg are the ones at 6-8
def leg3(angle1,angle2,angle3, delay_multiplier = 1):
    angle1 = angle1+leg3_offset[0]
    angle2 = angle2+leg3_offset[1]
    angle3 = angle3+leg3_offset[2]

    while(channel_cur[6] != angle1 or channel_cur[7] != angle2 or channel_cur[8] != angle3 ):
    ##ANGLE1
        if angle1 > channel_cur[6]:
            channel_cur[6] = channel_cur[6] +1
            setServo(6,channel_cur[6])
        elif angle1 < channel_cur[6]:
            channel_cur[6] = channel_cur[6] -1
            setServo(6,channel_cur[6])

        ##ANGLE2
        if angle2 > channel_cur[7]:
            channel_cur[7] = channel_cur[7] +1
            setServo_invert(7,channel_cur[7])
        elif angle2 < channel_cur[7]:
            channel_cur[7] = channel_cur[7] -1
            setServo_invert(7,channel_cur[7])

        ##ANGLE3
        if angle3 > channel_cur[8]:
            channel_cur[8] = channel_cur[8] +1
            setServo(8,channel_cur[8])
        elif angle3 < channel_cur[8]:
            channel_cur[8] = channel_cur[8] -1
            setServo(8,channel_cur[8])

        time.sleep(move_delay*delay_multiplier)

#same as leg 1, but motors of this leg are the ones at 9-11
def leg4(angle1,angle2,angle3, delay_multiplier = 1):
    angle1 = angle1+leg4_offset[0]
    angle2 = angle2+leg4_offset[1]
    angle3 = angle3+leg4_offset[2]

    while(channel_cur[9] != angle1 or channel_cur[10] != angle2 or channel_cur[11] != angle3 ):
    ##ANGLE1
        if angle1 > channel_cur[9]:
            channel_cur[9] = channel_cur[9] +1
            setServo(9,channel_cur[9])
        elif angle1 < channel_cur[9]:
            channel_cur[9] = channel_cur[9] -1
            setServo(9,channel_cur[9])

        ##ANGLE2
        if angle2 > channel_cur[10]:
            channel_cur[10] = channel_cur[10] +1
            setServo_invert(10,channel_cur[10])
        elif angle2 < channel_cur[10]:
            channel_cur[10] = channel_cur[10] -1
            setServo_invert(10,channel_cur[10])

        ##ANGLE3
        if angle3 > channel_cur[11]:
            channel_cur[11] = channel_cur[11] +1
            setServo(11,channel_cur[11])
        elif angle3 < channel_cur[11]:
            channel_cur[11] = channel_cur[11] -1
            setServo(11,channel_cur[11])

        time.sleep(move_delay*delay_multiplier)

#this only runs if this file is being run as the main file, as it is now and how it is currently set up, 
# this only tests some specific robot moves
if __name__ == '__main__':
    main()

