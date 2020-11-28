import numpy as np
import cv2
import imutils
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' #Disable debug information (Needs to be executed before importing tensorflow)
import tensorflow.keras
from PIL import Image, ImageOps
import threading
import random


#Importing position of the shelves from the file coordinates.txt
caselles = []
with open('coordinates.txt') as f:
    for line in f:
        x = line.strip().split("/")
        prelist = []
        for y in x:
            prelist.append(y.split(","))
        caselles.append(prelist)

tofulfill = [] #Definition of the alarm's state
def check(): #Defining the function that will do all the checkings
    # Should take a new photo from the camera every time. Now we are using photos already taken choosen in a random way.
    path = r"C:\Users\isaac\PycharmProjects\BonArea\images"
    filename = random.choice([
        x for x in os.listdir(path)
        if os.path.isfile(os.path.join(path, x))
    ])
    filename = path + '\\' + filename


    threading.Timer(5.0, check).start() #Check every 5 seconds (runs function every 5 minutes)
    #Using a model trained with tensorflow to check if theres an obstacle in front of the fridge. Model teached with teachablemachine.withgoogle.com

    # Load the model
    model = tensorflow.keras.models.load_model('keras_model.h5') #Imorting the model that tensorflow will use

    # Create the array of the right shape to feed into the keras model
    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)

    # Replace this with the path to your image
    image = Image.open(filename)

    #resize the image to a 224x224 with the same strategy as in TM2:
    #resizing the image to be at least 224x224 and then cropping from the center
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.ANTIALIAS)

    #turn the image into a numpy array
    image_array = np.asarray(image)

    # Normalize the image
    normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1

    # Load the image into the array
    data[0] = normalized_image_array

    # run the inference
    prediction = model.predict(data)
    if prediction[0][0] > prediction[0][1]:

        image = cv2.imread(filename)
        image = image[:1080, :1080] #Croping useless part of the image
        image = cv2.copyMakeBorder(image, 250, 250, 250, 250, cv2.BORDER_CONSTANT, value=[0, 0, 0]) #Adding a black border to the image
        image = imutils.rotate(image, -40) #Rotating the image 40º insdide de canvas
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV) #Coverting BGR workspace to HSV
        hsv_color1 = np.asarray([90, 5, 30]) #Color 1 in HSV
        hsv_color2 = np.asarray([120, 200, 255]) #Color 2 in HSV
        mask = cv2.inRange(hsv, hsv_color1, hsv_color2) #Create a mask selecting the colors between the range of the previous colors
        """"
        image[mask > 0] = (0, 0, 255)  #Applying the mask on the image
        cv2.imshow('image', image)
        cv2.waitKey(0)  # %%
        cv2.destroyAllWindows()
        #This commented block of code will show the results of the superposition of the mask, you can uncomment it to check it.
        """
        image[mask > 0] = (0, 0, 255)
        cv2.imwrite('output.jpg', image)
        count = 1 #Counter for the shelve number
        empty = [] #Will store the location of the empty shelves
        #This for checks if every shelve is empty analyzing the coordinates of coorinates.txt
        for x in caselles:
            retallada = mask[int(x[0][1]):int(x[1][1]), int(x[0][0]):int(x[1][0])]
            pixels = cv2.countNonZero(retallada)
            totals = retallada.size
            percentage = pixels / totals * 100 #Calculating the percentage that the masks represents on the canvas
            if percentage > 74: #If the percentage of the mask is more than 74% of the canvas the shelve will be considered empty
                empty.append(count)
            count += 1
        global tofulfill
        if len(empty) > 0:
            if empty != tofulfill: #If some shelve empty and status changed from previous check
                    print(f"Status changed, no stocks for: {empty}")
        else:
            if empty != tofulfill: #If shelves fulfilled and status changed from previous check
                print("Status changed, all stock fulfilled.")
        tofulfill = empty #Changing previous empty shelves to actual empty shelves
    else: #If the tensorflow model determined that there is an object in front of the fridge
        print("There's an obstacle in front of the refrigerator, waiting to take another image.")
check()