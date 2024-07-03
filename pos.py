import dlib
import cv2
from imutils import face_utils
import numpy as np

import base64
from random import randint
from PIL import Image  
import os
import io  
import traceback
import random
import string



# 加载面部检测与标志点预测模型
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("model/shape_predictor_68_face_landmarks.dat")



def save_base64_image(base64_image_data, upload_base_folder='temp/'):  
    try:
        image_bytes = base64.b64decode(base64_image_data)  
        image = Image.open(io.BytesIO(image_bytes))  
        random_filename = ''.join(random.choices(string.ascii_lowercase, k=10))  
        file_extension = image.format.lower()  
        full_path = f"{upload_base_folder}{random_filename}.{file_extension}"
        image.save(full_path)  
        return full_path 
    except:
        traceback.print_exc()
        return 




def is_mouth_open(shape,threshold = 70): #判断
    mouth_height = abs(shape[62][1] - shape[57][1])
    print(f"mouse_height={mouth_height}")
    return mouth_height > threshold



def is_eye_closed(shape, eye_start, eye_end,threshold = 0.25):
    eye_points = shape[eye_start:eye_end]
    A = np.linalg.norm(np.array(eye_points[1]) - np.array(eye_points[5])) #计算A区域
    B = np.linalg.norm(np.array(eye_points[2]) - np.array(eye_points[4])) #计算B区域
    C = np.linalg.norm(np.array(eye_points[0]) - np.array(eye_points[3])) #计算C区域
    ear = (A + B) / (2.0 * C)
    print(f"eyeClosed={ear}")
    return ear < threshold



def procFrame(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = detector(gray) #转人脸

    shape = face_utils.shape_to_np(predictor(gray, faces[0]))
    #原本设计，是是否张嘴，闭眼的。。。server逻辑写错了，对不上
    return is_mouth_open(shape),not is_eye_closed(shape, 36, 42),not is_eye_closed(shape, 42, 48) #返回三个参数，是否张嘴，是否睁开左眼，是否睁开右眼
