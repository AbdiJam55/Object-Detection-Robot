import os
import cv2
import pyaudio
import speech_recognition as sr

r = sr.Recognizer()  #create speech recognition object

#This function takes audio data and converts it from speech --> string text
def get_phrase():
    response = { "Phrase" : None,
             "Success": True,
             "Error" : None }
    audio = None
    with sr.Microphone() as source: # choosing the microphone as audio input source
        try:
            #duration - how long to take for adjustments for listening threshold
            r.adjust_for_ambient_noise(source, duration = 0.5)
            # timeout - time used to wait for input (1 sec)
            # phase_time_limit - whole time limit
            audio = r.listen(source, timeout = 1, phrase_time_limit=2)
        except sr.WaitTimeoutError:
            response["Success"] = False
            response["Error"] = "Timed out, no Audio"
            
        # If audio data was picked up by the microphone this will run   
        if audio is not None: 
            try:
                response["Phrase"] = r.recognize_google(audio)
            except sr.RequestError:
                response["Success"] = False
                response["Error"] = "Could not request results from Google"
            except sr.UnknownValueError:
                response["Error"] = "Google could not understand audio"
    print(response["Phrase"])  # For Debugging
    return response["Phrase"]

#converts inputted angle values to pwm
def angle_to_pwm(angle):
    return int((angle*2.73) + 128)

#  ------- This distance computation method was NOT used ---------
# ----------------------------------------------------------------
def object_rect(image):
    # convert the image to grayscale, blur it, and detect edges
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(gray, 35, 125)
    # find the contours in the edged image and keep the largest one
    # The images are set up so that the largest is the object rectangle
    contours = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnt = contours[1]
    c = max(cnt, key = cv2.contourArea)
    # compute the bounding box rectangle region
    area = cv2.minAreaRect(c)
    # returns the object rectangle's width
    return area[1][0]

def distance_to_camera(knownWidth, focalLength, perWidth):
    return (knownWidth*focalLength) / perWidth
# ----------------------------------------------------------------   
