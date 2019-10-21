# Import Libraries
import cv2
import time
import numpy
import snowboydecoder
import os

from multiprocessing import Process, Queue
from picamera import PiCamera
from picamera.array import PiRGBArray
from detection.engine import DetectionEngine
from PIL import Image
import RPi.GPIO as GPIO

# Import needed modules
import Tools
import Motors

# Import more Libraries
#from __future__ import division
import time
import RPi.GPIO as GPIO
from threading import Thread, Lock

##cur_angle_mutex = Lock()
##i2c_mutex = Lock()    

# Import the PCA9685 module for Motor Functions
import Adafruit_PCA9685

pwm = Adafruit_PCA9685.PCA9685()  #pwm object used to assign pwm signals to servos

# Configure min and max servo pulse lengths
servo_min = 150  # Min pulse length out of 4096
servo_max = 600  # Max pulse length out of 4096

pwm.set_pwm_freq(60)
pwm.set_pwm(12, 0, 374)
#  ANGLE(in degrees) * 2.73 + 128

cam_move = False

interrupted = False
model = "Tommy.pmdl"
detector = snowboydecoder.HotwordDetector(model, sensitivity=0.5)

CAM_WIDTH = 1280
CAM_HEIGHT = 720
#CAM_WIDTH = 640
#CAM_HEIGHT = 480

CWD_PATH = os.getcwd()   #gets current directory path
MODEL_PATH = os.path.join(CWD_PATH, 'models', 'detect.tflite')  #extends path to get model
LABEL_PATH = os.path.join(CWD_PATH, 'labels', 'coco_labels.txt') #extends path to get labelmap
spec_labels = [43, 46, 50]  #Items to detect [bottle, cup, bowl]

numbers = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]  #for speech-> text
finding = False

# Robot commands
cmd_dict = {
    "forward": Motors.forward,
    "backward": Motors.backward,
    "left": Motors.left,
    "right": Motors.right,
    "sit": Motors.sit,
    "stand": Motors.stand,
    "shake": Motors.shake,
    "bottle": 43,
    "cup": 46,
    "bowl": 50
}

# Takes in number in words and returns digits (1-10)
def word_to_number(num):
    if num in numbers:
        return (numbers.index(num)+1)
    else:
        return 0

#Flips the PyAudio interrupt flag 
def interrupt_callback():
    global interrupted
    return interrupted

#Called when robot is listening for instructions 
def callbackHandler():
    print("Speak")
    detector.terminate()
    phrase = Tools.get_phrase()
    q1.put(phrase)
    commands()
    audio_detection()

# Process - 2
# Is always listening for "Tommy" and will call the callbackHandler() when "Tommy" is heard
def audio_detection():
    print('Listening...')
    detector.start(detected_callback=callbackHandler,
               interrupt_check=interrupt_callback,
               sleep_time=0.03)
    detector.terminate()

# Function to read labels from text files.
def ReadLabelFile(filepath):
    f = open(filepath, 'r', encoding='utf-8')
    lines = f.readlines()
    ret = {}
    for line in lines:
        index = line.strip().split()[0]
        text = line.strip().split()[1:]
        str_text = " ".join(text)
        ret[int(index)] = str_text
    return ret

# Function that translates voice commands to actions
def commands():
    global finding
    if q1.empty():
        return 0
    else:
        phrase = str(q1.get())
        str_list = phrase.lower().split()
        
        # Returns an integer to be used in object_detection()
        if "bottle" in str_list:
            finding = True
            return cmd_dict["bottle"]
        elif "cup" in str_list:
            finding = True
            return cmd_dict["cup"]
        elif "bowl" in str_list:
            finding = True
            return cmd_dict["bowl"]

        # Direct Voice to Motors commands
        elif "forward" in str_list:
            finding = False
            for text_num in str_list:
                if text_num in numbers:
                    nums = int(word_to_number(text_num))
                    for i in range(nums):
                        #print(i)
                        cmd_dict["forward"]()
                    return 0
                elif text_num.isdigit():
                    text_num = int(text_num)
                    for i in range(text_num):
                        #print(i)
                        cmd_dict["forward"]()
                    return 0
            return cmd_dict["forward"]()

        elif "backward" in str_list:
            finding = False
            for text_num in str_list or text_num.isdigit():
                if text_num in numbers:
                    nums = word_to_number(text_num)
                    for i in range(nums):
                        cmd_dict["backward"]()
                    return 0
                elif text_num.isdigit():
                    text_num = int(text_num)
                    for i in range(text_num):
                        cmd_dict["backward"]()
                    return 0
            return cmd_dict["backward"]()
                    
        elif "left" in str_list:
            finding = False
            for text_num in str_list:
                if text_num in numbers or text_num.isdigit():
                    nums = word_to_number(text_num)
                    for i in range(nums):
                        cmd_dict["left"]()
                    return 0
                elif text_num.isdigit():
                    text_num = int(text_num)
                    for i in range(text_num):
                        cmd_dict["left"]()
                    return 0
            return cmd_dict["left"]()
                    
        elif "right" in str_list:
            finding = False
            for text_num in str_list:
                if text_num in numbers or text_num.isdigit():
                    nums = word_to_number(text_num)
                    for i in range(nums):
                        cmd_dict["right"]()
                    return 0
                elif text_num.isdigit():
                    text_num = int(text_num)
                    for i in range(text_num):
                        cmd_dict["right"]()
                    return 0
            return cmd_dict["right"]()
                    
        elif "sit" in str_list:
            finding = False
            return cmd_dict["sit"]()
        elif "stand" in str_list:
            finding = False
            return cmd_dict["stand"]()
        elif "shake" in str_list:
            finding = False
            return cmd_dict["shake"]()
        else:
            return 0


# Process - 1
# Does the Object Detection
def object_detection():
    global finding  #Flag which is set if the object detection sequence will be used
    # The below flags are in such a sequence so that the robot can perform its object detection
    cam_move = True  
    turning = True
    not_straight = False

    #Creating, Initializing and configuring PiCamera object
    cam = PiCamera()
    cam.resolution = (CAM_WIDTH, CAM_HEIGHT)
    #cam.resolution = (CAM_WIDTH, CAM_HEIGHT)
    cam.framerate = 20  #set steady framerate at video-port based image captures
    #use_video_port is regulated by using an acceptable FPS
    rawCapture = PiRGBArray(cam, size=(CAM_WIDTH, CAM_HEIGHT))
    time.sleep(0.1) #Giving Camera some time to prepare

    #Camera is originally set to 374pwm or 90 degrees
    new_pwm = 374
    
    #Center Point
    centerX, centerY = int(CAM_WIDTH/2), int(CAM_HEIGHT/2)
    
    #Initialize the Detection Engine and get Labelmap
    engine = DetectionEngine(MODEL_PATH)
    labels = ReadLabelFile(LABEL_PATH)
    
    detect = 46  #Starts of with detecting a cup
    
    #Loop runs for each "img" taken by PiCamera continuously which is a VideoStream
    for img in cam.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        # Convert img to numpy array for OpenCV image processing
        frame = img.array
        
        #frame = cv2.cvtColor(cv2_im,cv2.COLOR_BGR2RGB)
        #cv2.putText(frame, "FPS: {:.2f}".format(FPS), (10,30), font,0.8,(255,0,0))
        img = Image.fromarray(frame) #convert numpy array to image object for detection engine

        # "Detect" changes when new object is to be found using voice command (ex: find water bottle)
        change_object = commands()
        if change_object in spec_labels:
            detect = change_object
            print(detect)
        
        # Being frame inferencing using the image object (img)
        # Threshold - minimum confidence threshold for detected objects so higher equates to better accuracy
        # top_k - max number of detected objects to return
        frame_infer = engine.DetectWithImage(img, threshold=0.4, top_k=5, keep_aspect_ratio=True, relative_coord=False)
        
        # Loop over the results for whenever anything that is recognizable is detected by the engine
        for infer in frame_infer:
                
            if infer.label_id == detect:
                # Extract the bounding box and convert 4 integer list
                box = infer.bounding_box.flatten().tolist()
                box = [int(b) for b in box]
                box_width = box[2] - box[0]
                #box_height = box[3] - box[1]
                #area = box_width * box_height
                
                #Draw rectangle around object and put object name with score of accuracy on camera window
                cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 3)
                text = labels[infer.label_id] +": " + str(int(infer.score*100)) + "%"
                cv2.putText(frame, text, (box[0], box[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

                #print(area)
                #print(box_width)
                #servo.angle = servo.angle + 5
                #print(servo.angle)
                
                #------------------------------------------------------------------------------------------------------------
                # This section is used to position the camera so the the bounding box surround object is approx centered                
                width_pos = abs(box[0] - centerX)
                centered = abs((box_width/2) - width_pos)
                diff = centerX-(box_width/2)
                if box[0] <= centerX and new_pwm <= 537 and centered >= 80 and finding and cam_move:
                    new_pwm = new_pwm + 15
                    #print("Look Left "+ str(new_pwm))
                elif box[0] >= diff and new_pwm >= 210 and centered >= 80 and finding and cam_move:
                    new_pwm = new_pwm - 15
                    #print("Look Right "+ str(new_pwm))
                pwm.set_pwm(12, 0, new_pwm)
                #------------------------------------------------------------------------------------------------------------

                # ------------------------------------------------------------------------------------------------------------
                # This section checks if the object happens to already be centered and it also sets/resets
                # the cam_move flag which is used to position the camera
                if new_pwm > 292 and new_pwm < 415 and not cam_move:
                    not_straight = True
                        
                if centered <= 80 and finding:
                    cam_move = False
                    #print("cam stopped")
                elif centered >= 80 and finding:
                    cam_move = True
                    #print("cam can now move")
                # ------------------------------------------------------------------------------------------------------------
                
                # ------------------------------------------------------------------------------------------------------------
                # This section is used to determine how to turn the robot with respect to camera position
                # (ex: camera left -> bot turns left). If the camera has not turned the robot will not turn
                if new_pwm >= 160 and new_pwm <= 251 and not cam_move and turning and finding:
                    print ("right 2")
                    Motors.right()
                    Motors.right()
                    turning = False
                    new_pwm = 374
                    pwm.set_pwm(12,0,374)
                elif new_pwm >251 and new_pwm < 292 and not cam_move and turning and finding:
                    print ("rightwing")
                    Motors.right()
                    turning = False
                    new_pwm = 374
                    pwm.set_pwm(12,0,374)
                    
                elif new_pwm <= 578 and new_pwm >= 497 and not cam_move and turning and finding:
                    print ("left 2")
                    Motors.left()
                    Motors.left()
                    turning = False
                    new_pwm = 374
                    pwm.set_pwm(12,0,374)
                    
                elif new_pwm < 497 and new_pwm > 415 and not cam_move and turning and finding:
                    print ("leftwing")
                    Motors.left()
                    turning = False
                    new_pwm = 374
                    pwm.set_pwm(12,0,374)
                    
                elif not_straight and turning and finding:
                    #print("straight walk")
                    turning = False
                # ------------------------------------------------------------------------------------------------------------

                # ------------------------------------------------------------------------------------------------------------
                # This section is used to determine how far to move the robot forward to the object is has detected
                if not turning and box_width <= 550 and detect == 50 and finding:
                    for i in range ((int)((550 - box_width)/65)):
                        Motors.forward()
                    finding = False
                    turning = True
                    cam_move = True
                    not_straight = False
                    
                elif not turning and box_width <= 700 and detect == 46 and finding:
                    for i in range ((int)((700 - box_width)/100)):
                       Motors.forward()
                    finding = False
                    turning = True
                    cam_move = True
                    not_straight = False
                elif not turning and box_width <= 450 and detect == 43 and finding:
                    for i in range ((int)((450 - box_width)/70)):
                        Motors.forward()
                    Motors.forward()
                    finding = False
                    turning = True
                    cam_move = True
                    not_straight = False
                # ------------------------------------------------------------------------------------------------------------

        # Show the camera window on whichever graphical display device/software is connected              
        cv2.imshow("Object Detection", frame)

        # Clear the rawCapture PiCamera array for continuous usage
        rawCapture.truncate(0)
        
        # Needed to show the frames in the "VideoStream" as it is used for processing many GUI events
        cv2.waitKey(1)  # number must be at least greater than 0 for video
        
    cam.close()  #Release camera resources
    cv2.destroyAllWindows()  #Close all running OpenCV windows

     
#Runs only when executing this file as the main module
if __name__ == "__main__":
    num_processes = 0
    running = True
    p1 = Process(target=object_detection) #create Process-1 object
    q1 = Queue()  # Pipe for all Voice Commands
    p2 = Process(target=audio_detection) #create Process-2 object
    Motors.begin()  #Initialize Robot leg positions
    p1.start()  #start Process-1
    p2.start()  #start Process-2
    while running:
        # Take keyboard input of "c" to end Process-1 or "a" to end Process-2
        stop_char = input(""" Enter 'c' to quit Camera \n Enter 'a' to quit Audio \n """)
        if p1.is_alive() and stop_char == "c":
            print("Camera process terminated")
            num_processes = num_processes + 1
            p1.terminate()
        elif p2.is_alive() and stop_char == 'a':
            print("Audio process terminated")
            num_processes = num_processes + 1
            p2.terminate()
        # When both processes are terminated, leaving this inputstream loop
        if num_processes >= 2:
            running = False
    print("All Processes are closed")
    
