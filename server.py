from fastapi import FastAPI, File, UploadFile, Response,Request
from fastapi.responses import FileResponse  

from typing import Optional
import Identify
import os
from fastapi import Form
import traceback

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.encoders import jsonable_encoder
import json
import os
import sqlite3
from random import randint

from urllib.parse import quote
from urllib.parse import unquote
import pyttsx3






app = FastAPI()




@app.post("/api/identify/Recognition")
async def Recognition(idCardNo: str = Form(...), FaceNo: str = Form(...)):
    if not idCardNo:
        return  Response(content= json.dumps({"rCode": "422", "rDesc": "没有上传处理过的身份证图片编号"}, ensure_ascii=False),media_type="application/json")  
    if not FaceNo:
        return Response(json.dumps({"rCode": "422", "rDesc": "没有上传处理过的人脸图片编号"}, ensure_ascii=False),media_type="application/json")  
    
    
    try:
        return  Response(Identify.Recognition(idCardNo, FaceNo),media_type="application/json")
    except Exception as e:
        traceback.print_exc()
        return Response(json.dumps({"rCode": "500", "rDesc": f"人脸识别过程中发生错误: {str(e)}"}),media_type="application/json")  
    





@app.post("/api/identify/DrawFaceinIdCard")
async def DrawFaceinIdCard(idCardFile: UploadFile):

    if not idCardFile: return Response(content=json.dumps({"rCode": "422", "rDesc": "没有上传图片"}, ensure_ascii=False), media_type="application/json")

    IdCardImg=""
    while True:
        IdCardImg = os.path.join("temp", f"{randint(0, 1000000)}.jpg")
        if not os.path.exists(IdCardImg): break


    try:
        with open(IdCardImg, "wb") as buffer: buffer.write(await idCardFile.read())

        return  Response(Identify.DrawFaceinIdCard(IdCardImg),media_type="application/json")
    except Exception as e:
        traceback.print_exc()
        return Response(content=json.dumps({"rCode": "500", "rDesc": f"抽取身份证人脸过程中出错: {str(e)}"}, ensure_ascii=False), media_type="application/json")






@app.post("/api/identify/DrawFaceinPic")
async def DrawFaceinPic(faceFile: UploadFile):
    if not faceFile:return  Response(content= json.dumps({"rCode": "422", "rDesc": "没有上传人脸图片路径"}, ensure_ascii=False),media_type="application/json") 

    faceImgPath=""
    while True:
        faceImgPath= os.path.join("temp", f"{randint(0, 1000000)}.jpg")
        if not os.path.exists(faceImgPath): break


    try:
        with open(faceImgPath, "wb") as buffer: buffer.write(await faceFile.read())
        return  Response(Identify.DrawFaceinPic(faceImgPath),media_type="application/json")
    except Exception as e:
        traceback.print_exc()
        return Response(json.dumps({"rCode": "500", "rDesc": f"抽取照片人脸错误: {str(e)}"}),media_type="application/json")  



#这里使用sqlite只是为了过度。。。理论要用redis
@app.post("/api/detecting/Create") #生成三个动作
async def CreateDecting(uuid: str = Form(...)):
    db = sqlite3.connect('fas.db')  
    cursor = db.cursor()  

    if not uuid: return Response(content=json.dumps({"rCode": "422", "rDesc": "没有图片"}, ensure_ascii=False), media_type="application/json")

    Jarray = []
    for i in range(0,2):

        l_eye_o,r_eye_o,mouse_o = randint(0,1),randint(0,1),randint(0,1)
        if l_eye_o==1 and r_eye_o==1 and mouse_o==1: 
            i-=1
            continue #这种情况只能是最后一个
        
        message = "请把整个头放入圆形椭圆中,并完成以下动作:\n"
        if l_eye_o==1 and r_eye_o==1:
            message+="张开双眼 "
        elif l_eye_o==1:
            message+="张开左眼，闭上右眼 "
        elif r_eye_o==1:
            message+="张开右眼，闭上左眼 "
        else:
            message+="闭上双眼 "

        if mouse_o==1:
            message+="张开嘴 "
        else:
            message+="闭上嘴 "


        fileName = str(l_eye_o)+str(r_eye_o)+str(mouse_o) 
        if not os.path.exists( "audio/" + fileName + ".mp3"):
            tts.save_to_file(message, "audio/" + fileName + ".mp3")
            tts.runAndWait()



        Jarray.append({"l_eye_o":l_eye_o,"r_eye_o":r_eye_o,"mouse_o":mouse_o,"message":message,"audio":fileName})






    Jarray.append({"l_eye_o":1,"r_eye_o":1,"mouse_o":1,"message":"请张开双眼,张开嘴","audio":"111"})


    
    cursor.execute("SELECT EXISTS(SELECT 1 FROM fas WHERE uuid = ?)"  , (uuid,))


    if cursor.fetchone()[0]: #有数据，就更新，没数据就创建
        cursor.execute("UPDATE fas SET posJson = ? WHERE uuid = ?"  ,(quote(json.dumps(Jarray)), uuid))
        cursor.execute("UPDATE fas SET current = ? WHERE uuid = ?"  ,(0, uuid))
        cursor.execute("UPDATE fas SET FaceImg = ? WHERE uuid = ?"  ,("", uuid))
    else:
        cursor.execute("INSERT INTO fas (uuid,posJson,Faceimg,current) VALUES (?, ?, ?, ?)",  (uuid, quote(json.dumps(Jarray)), "", "0"))  
        
    db.commit()
    return Response(content=json.dumps({ "rCode":200,"rDesc":"生成成功","actionArray":Jarray},ensure_ascii=False),media_type="application/json") 



@app.get("/getAudio/{No}")  
async def download_file(No: str):  
 

    return FileResponse(path="audio/" + No + ".mp3"  , filename=No+".mp3", media_type="application/octet-stream")




@app.post("/shutdown")
async def test_run(Key: str = Form(...)):
    if Key=="hello world":os._exit(0)
    return {"message": "Shutdown"} 

@app.get("/test_run")
async def test_run():
    return {"message": "Hello"}

if __name__ == "__main__":
    import uvicorn

    db = sqlite3.connect('fas.db')  
    cursor = db.cursor()  
    cursor.execute('''CREATE TABLE IF NOT EXISTS fas(uuid TEXT NOT NULL,posJson Text NOT NULL,Faceimg Text NOT NULL,current Text NOT NULL)'''  )  
    db.commit()  
    tts = pyttsx3.init()


    uvicorn.run(app, host="0.0.0.0", port=7000)