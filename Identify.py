import cv2
import dlib
import numpy as np
from random import randint
import os
import json
import traceback
from imutils import face_utils





from paddleocr import PaddleOCR
 
# 识别身份证
def findIdcardResult(img_path): #穿路径


    global ocr
    results = ocr.ocr(img_path, cls=True)
    
    results_data = results[0]


    info_dict = {"Name": "", "Nationality": "", "Address": "", "Birthday": "", "Idnumber": "", "Gender": ""}

    for item in results_data:
        text = item[1][0]
        confidence = item[1][1]  
    
        if "姓名" in text:
            info_dict["Name"] = text.replace("姓名", "").strip()
        elif "民族" in text:
            info_dict["Nationality"] = text.replace("民族", "").strip()
        elif "出生" in text:
            info_dict["Birthday"] = text.replace("出生", "").strip()
        elif len(text) == 18 and text.isdigit():  
            info_dict["Idnumber"] = text
        elif "男" in text or "女" in text:  
            info_dict["Gender"] = text.replace("性别", "").strip()
        else:
            if not any(keyword in text for keyword in ["姓名", "民族", "出生", "公民身份号码", "性别"]):  # 更新关键字列表
                info_dict["Address"] += text.replace("住址","").strip() + " "

    info_dict["Address"] = " ".join(info_dict["Address"].split())
    return info_dict





def DrawFaceinIdCard(image_path, cnt=0, output_directory="output"):
    # 确保输出目录存在
    if not os.path.exists(output_directory):os.makedirs(output_directory)
    if not os.path.exists(image_path):return json.dumps({"rCode": "906", "rDesc": "图片不存在，保存失败:" + str(image_path)}, ensure_ascii=False)

    img = cv2.imread(image_path)
    
    try:
        detections = detector(img, 1)
    except Exception as ex:
        return json.dumps({"rCode": "901", "rDesc": "身份证处理失败 - 检测器错误"}, ensure_ascii=False)

    if detections:
        # 获取人脸框的坐标
        face = detections[0]
        top, bottom, left, right = face.top(), face.bottom(), face.left(), face.right()
        height, width = bottom - top + 60, right - left + 40
        

        img_cropped = img[top-40:top+height, left-15:left+width]
        while True:
            No = randint(0, 1000000)
            output_path = os.path.join(output_directory, f"{No}.jpg")
            if not os.path.exists(output_path): break

        try:
            cv2.imwrite(output_path, img_cropped)
            #return json.dumps({"rCode": "200","rDesc": "success","No":str(No),"rData":findIdcardResult(image_path)}, ensure_ascii=False)
            return json.dumps({"rCode": "200", "rDesc": "身份证提取头像处理成功", "No": str(No)}, ensure_ascii=False)
        except Exception as ex:
            traceback.print_exc()
            
            return json.dumps({"rCode": "901", "rDesc": "身份证处理失败 - 写入错误"}, ensure_ascii=False)
    else:
        if cnt < 3:
            img_transformed = cv2.flip(cv2.transpose(img), 0)
            cv2.imwrite(image_path, img_transformed)
            return DrawFaceinIdCard(image_path, cnt+1, output_directory)
        else:
            return json.dumps({"rCode": "901", "rDesc": "身份证处理失败 - 未找到人脸"}, ensure_ascii=False)





def DrawFaceinPic(image_path, output_directory='output'):
    global detector


    img = cv2.imread(image_path)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        
    dlib_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    faces = detector(dlib_img, 1)
    
    if len(faces) > 1:
        return json.dumps({"rCode": "902","rDesc": "拍照的人脸过多，请对准自身人脸"}, ensure_ascii=False)
    
    if len(faces) == 0:
        return json.dumps({"rCode": "903","rDesc": "未检测到拍照有人脸"}, ensure_ascii=False)
    
    for i, face_rect in enumerate(faces):
        x, y, w, h = face_rect.left(), face_rect.top(), face_rect.width(), face_rect.height()
        face = img[y:y+h, x:x+w]

        No=0
        while os.path.exists(os.path.join(output_directory, f"{No}.jpg")): No  = randint(0,1000000)
        output_path = os.path.join(output_directory, f"{No}.jpg")
        cv2.imwrite(output_path, face)

        return json.dumps({"rCode": "200","rDesc": "实拍提取人像处理成功","No":str(No)}, ensure_ascii=False)




def face_descriptor(img_path): #获取脸部描述
    global detector,predictor,facerec

    img = cv2.imread(img_path)
    if img is None: return np.array([])  # 返回空数组
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)
    if len(faces) != 1:  return np.array([])  # 当没有检测到人脸或检测到多张脸时，返回空数组
    shape = predictor(gray, faces[0])
    face_descriptor = facerec.compute_face_descriptor(img, shape)
    return np.array(face_descriptor)









def compare_faces(descriptor1, descriptor2, threshold=0.4):#对比人头
    distance = np.linalg.norm(descriptor1 - descriptor2)
    return distance <= threshold


def Recognition(idCard_No,Face_No,output_directory="output"): #接口函数


    code,desc = "",""
    idCard_path = os.path.join(output_directory, f"{idCard_No}.jpg")
    Face_path = os.path.join(output_directory, f"{Face_No}.jpg")

    if not os.path.exists(idCard_path) or not os.path.exists(Face_path):
        code,desc = "404","路径不存在"

    elif not compare_faces(face_descriptor(idCard_path),face_descriptor(Face_path)):
        code,desc = "904","人脸验证失败"
    else:
        code,desc = "200","人脸验证成功"

    if os.path.exists(idCard_path): os.remove(idCard_path) 
    if os.path.exists(Face_path): os.remove(Face_path) 

    return json.dumps({"rCode": code,"rDesc": desc}, ensure_ascii=False)
    









global detector,predictor,facerec,ocr
ocr = PaddleOCR(use_angle_cls=False , lang="ch")
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("model/shape_predictor_68_face_landmarks.dat")  
facerec = dlib.face_recognition_model_v1("model/dlib_face_recognition_resnet_model_v1.dat")  



