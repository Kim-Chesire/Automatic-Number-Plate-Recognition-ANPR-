import cv2
import imutils
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import cm

import easyocr


import pandas as pd
import os.path
from local_utils import detect_lp
from tensorflow.keras.models  import model_from_json
from tensorflow.keras.models import load_model as load_keras_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from os.path import splitext,basename
from PIL import Image, ImageChops
import math
from scipy import spatial

import streamlit as st 
import requests
import io
import base64

import pickle 
from pathlib import Path
import streamlit_authenticator as stauth
import hashlib







     
#-----------------------------  CACHE DATABASE    -----------------------------------
database_faces=[]

# -----------------------------------------------------------------------------------

# ------------------------- FACE DETECTION and Face ID with database images ---------
        
#perform face detection with the help of faceplusAPI 
def dofaceplusAPI(image):
    original_image = image
    http_url = 'https://api-us.faceplusplus.com/facepp/v3/detect'
    key = "LXCYl-Fuc_erkrCY_iQfhYEYfttcXn4P"
    secret = "WY6zwvR8wZ42wX621cGvIIo-JC8YN5NS"
    
    #conver the numpy array into an Image type object
    h , w , c = image.shape
    image = np.reshape(image,(h,w,c))
    image = Image.fromarray(image, 'RGB')

    #convert image to bytes as api requests are in that format
    buf = io.BytesIO()
    image.save(buf,format = 'JPEG')
    byte_im = base64.b64encode(buf.getvalue())
    
    payload = {
                'api_key': key, 
                'api_secret': secret, 
                'image_base64':byte_im,
                }
    
    try:
        # send request to API and get detection information
        res = requests.post(http_url, data=payload)
        json_response = res.json()

        
        # get face info and draw bounding box 
        # st.write(json_response["faces"])
        for faces in json_response["faces"]:
            # get coordinate, height and width of fece detection
            x , y , w , h = faces["face_rectangle"].values()
            
            # Note: x<->y coordinate interchange during cropping 
            face = original_image[x:x+h,y:y+w]
            
            # Compare cropped face with faces present in the database
            match = check_face(face)
            percentage=match*100
            # select color for matched faces
            if percentage>95: 
                color = (0, 255, 0)
            else: 
                color = (255, 0 , 0)
                
            # Draw bounding box 
            cv2.rectangle(original_image, (y , x), (y+w, x+h),color,2)
            match = str(round(percentage,2))
            cv2.putText(original_image , match ,(y , x),fontFace=cv2.FONT_HERSHEY_COMPLEX, fontScale=1, color=(0, 95, 255))
            
            
            
    except Exception as e:
        print('Error:')
        print(e) 
    
    # Display image with detections
    original_image= cv2.cvtColor(original_image ,cv2.COLOR_BGR2RGB )
    return original_image


# Compare detected faces with faces present in the database
def check_face(face):
    # Compare Faces detected with images present in the database 
    http_url = 'https://api-us.faceplusplus.com/facepp/v3/detect'
    key = "LXCYl-Fuc_erkrCY_iQfhYEYfttcXn4P"
    secret = "WY6zwvR8wZ42wX621cGvIIo-JC8YN5NS"
    
    max_Similariy = 0
    for image in database_faces:
        original_img = image
        # perform face detection on the faces in database 
        #conver the numpy array into an Image type object
        image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
        
        h , w , c = image.shape
        image = np.reshape(image,(h,w,c))
        image = Image.fromarray(image, 'RGB')

        #convert image to bytes as api requests are in that format
        buf = io.BytesIO()
        image.save(buf,format = 'JPEG')
        byte_im = base64.b64encode(buf.getvalue())
        
        # perform face detection 
        payload = {
            'api_key': key, 
            'api_secret': secret, 
            'image_base64':byte_im,
            }
        
        try:
            # send request to API and get detection information
            res = requests.post(http_url, data=payload)
            json_response = res.json()

            # get face info and draw bounding box 
            # st.write(json_response["faces"])
            
            for faces in json_response["faces"]:
                # get coordinate, height and width of fece detection
                x , y , w , h = faces["face_rectangle"].values()
                
                # Note: x<->y coordinate interchange during cropping 
                faces = original_img[x:x+h,y:y+w]
                
                
                # Resize detected image and database image to be of same size 
                height = 200
                width = 200
                dim = (height, width)
                face = cv2.resize(face , dim)
                faces = cv2.resize(faces , dim)
                
                # st.image(face)
                # st.image(faces)
                
                face1 = np.array(face)
                face1 = face1.flatten()
                face1 = face1/255

                    
                face2 = np.array(faces)
                face2 = face2.flatten()
                face2 = face2/255
                
                sim = -1 * (spatial.distance.cosine(face1, face2) - 1)
                                
                if sim >max_Similariy:
                    max_Similariy = sim              
                
        except Exception as e:
            print('Error:')
            print(e) 
            
    return max_Similariy


# Upload images in to database which will be used for ID purpose 
def upload_database_faces():

    uploaded_files = st.file_uploader("Choose database images", type="jpg",accept_multiple_files=True)
    if uploaded_files is not None:
        for uploaded_file in uploaded_files:
            # Convert the file to an opencv image.
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            opencv_image = cv2.imdecode(file_bytes, 1)
            database_faces.append(opencv_image)
        return True
    else:
        return False
    
              
# ----------------------------------------------------------------------------------

 #USER AUTHENTICATION---
#names = ["SecurityGuard1", "SecurityGuard2"]
#usernames = ["SecurityGuard1", "SecurityGuard2"]

# load hashed passwords
#file_path = Path(__file__).parent / "hashed_pw.pkl"
#with file_path.open("rb") as file:
    #hashed_passwords = pickle.load(file)

#authenticator = stauth.Authenticate(names, usernames, hashed_passwords,
    #"dashboard", "abcdef", cookie_expiry_days=30)

#name, authentication_status, username = authenticator.login("Login", "main")

#if authentication_status == False:
    #st.error("Username/password is incorrect")

#if authentication_status == None:
   # st.warning("Please enter your username and password")

#if authentication_status:
firebaseConfig = {
    'apiKey': "AIzaSyDUhH5kaFObMYlcjPylLbY5FOeEU4mOhsE",
    'authDomain': "anpr-d6144.firebaseapp.com",
    'projectId': "anpr-d6144",
    'storageBucket': "anpr-d6144.appspot.com",
    'messagingSenderId': "113685971720",
    'appId': "1:113685971720:web:a6f4f83f3279310bf6a2bd",
    'measurementId': "G-5TN897NJ44"
  }
#Modules
import pyrebase
from datetime import datetime
#Configuration key
firebaseConfig = {
    'apiKey': "AIzaSyDUhH5kaFObMYlcjPylLbY5FOeEU4mOhsE",
    'authDomain': "anpr-d6144.firebaseapp.com",
    'projectId': "anpr-d6144",
    'databaseURL': "https://console.firebase.google.com/u/0/project/anpr-d6144/database/anpr-d6144-default-rtdb/data/~2F",
    'storageBucket': "anpr-d6144.appspot.com",
    'messagingSenderId': "113685971720",
    'appId': "1:113685971720:web:a6f4f83f3279310bf6a2bd",
    'measurementId': "G-5TN897NJ44"
  }
    
#Authentication  
def login():
    firebase = pyrebase.initialize_app(firebaseConfig)
    auth = firebase.auth()
    #database
    db = firebase.database()
    storage = firebase.storage()
    def login():
                st.sidebar.title("ANPR APP Login")

    #Authentication
    choice = st.sidebar.selectbox('login/Signup',['Login', 'Sign up'])
    email = st.sidebar.text_input('Please enter your email address')
    password = st.sidebar.text_input('Please enter your password')

    if choice == 'Sign up':
        name = st.sidebar.text_input('Please input your name',value='Default')
        submit = st.sidebar.button('Create my account')
        if submit:
            auth = auth.create_user_with_email_and_password(email,password)
            st.success('Your account is created successfully')
            st.balloons()
            #Sign in
            auth = auth.sign_in_with_email_and_password(email,password)
            email = "colinrop68@gmail.com" 
            user_id = user['ImdpmjDd53WAVoWqjEBqAevWNIT2']

    else:
        submit = st.sidebar.button('Sign in')
        if submit:
            user = auth.sign_in_with_email_and_password(email, password)
            email = "colinrop68@gmail.com" 
            user_id = user['ImdpmjDd53WAVoWqjEBqAevWNIT2']
            st.success("Logged in successfully!")
            st.error("Incorrect email or password")
        

    

#---------------------------- Number Plate Detection --------------------------------
st.sidebar.title("ANPR Dashboard")
page = st.sidebar.selectbox("Select a page", ["Homepage","Number Plate Recognition", "Vehicle records"])

# Define the function to display the homepage
def show_homepage():
    st.title("ANPR Dashboard")
    st.write("Number Plate Extraction")
    st.write("With this tool, you can upload an image of a vehicle and extract the number plate from the image.")
    st.write("To get started, select 'Number Plate Recognition' from the sidebar and upload an image.")
    footer = """
    ---
    © 2023 KABU ANPR App
    """

    st.markdown(footer)

def show_numberplate():
    st.title("Number Plate Recognition")
    st.write("Upload an image to perform Number plate extraction.")
    # Update ANPR using Numberplaterecognition
    # Define the function to display the statistics page
def show_stats():
    st.title("Vehicle data")
    st.write("View the vehicle records")
    
    data = pd.read_csv("vehicle_records.csv")
    
    # Display the data in a table
    st.write(data)
    
    # Compute and display some basic statistics about the data
    st.write("Basic Statistics:")



# Define the function to display the license plate recognition page

def numberplateRecognizer(image):
    original_image = image
    #conver the numpy array into an Image type object
    h , w , c = image.shape
    image = np.reshape(image,(h,w,c))
    image = Image.fromarray(image, 'RGB')

    #convert image to bytes as api requests are in that format
    buf = io.BytesIO()
    image.save(buf,format = 'JPEG')
    byte_im = buf.getvalue()
    
    response = requests.post(
        'https://api.platerecognizer.com/v1/plate-reader/',
        # data=dict(regions='hk'),  # Optional
        files=dict(upload=byte_im),
        headers={'Authorization': 'Token f184ad4cc54df68357e7873baea13a1d596ad6e4'}
    )
    json_response = response.json()
    # for key, value in json_response.items():
    #     st.write(key, "->", value)
    
    #Find number of number plate present in the image
    number_plates = len(json_response['results'])
    st.subheader("Total Number Plates Detected in this image:{}".format(number_plates))

    st.subheader("Number Plate Information")
    # get number plate and borders from the image
    for plate in json_response['results']:
        #Get numberplate and borders
        car_plate = plate['plate']
        xmin , ymin , xmax , ymax = plate['box'].values()
        
        #crop number plate and show borders
        numberplate_crop = image.crop((xmin , ymin , xmax , ymax))
        st.image(numberplate_crop)
        st.write("Number Plate Digits: {}".format(car_plate))
        
        # Draw Borders and show numberplate on image
        cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax),(255,0,0),5)
        cv2.putText(original_image , car_plate ,(xmin , ymin),fontFace=cv2.FONT_HERSHEY_TRIPLEX, fontScale=1, color=(0, 255, 0))
        
        
    original_image= cv2.cvtColor(original_image ,cv2.COLOR_BGR2RGB )
    # display number above number plate
    st.image(original_image)

#-----------------------------------------------------------------------------------

# Streamlit Main app

def main():
    st.title("Automatic Number Plate Recognition")
    #st.subheader("")
    
    uploaded_file = st.file_uploader("Choose a image file", type="jpg")
    if uploaded_file is not None:
        # Convert the file to an opencv image.
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        original =  cv2.imdecode(file_bytes, 1)
        opencv_image = cv2.imdecode(file_bytes, 1)
        display = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2RGB)
        # Display Image after loading in streamlit
        st.image(display)
        
        
        #st.subheader("Do Number plate extraction")
        #upload database image for matching 
        if upload_database_faces():
        
            if len(database_faces) !=0:
                original_image = dofaceplusAPI(opencv_image)
                st.image(original_image)
                
        
        # If button is clicked then it will perform Number Plate extraction and OCR 
        if st.button("Extract Number Plate"):
            numberplateRecognizer(original)
# Display the appropriate page based on the user's selection
if page == "Homepage":
    show_homepage()
elif page == "Vehicle records":
    show_stats()
else:
    show_numberplate()
                   
    if  __name__ == "__main__":
        main()


