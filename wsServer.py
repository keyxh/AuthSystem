import pos
import sqlite3


import asyncio  
import websockets  
import json
from urllib.parse import urlparse, parse_qs  
import json
from urllib.parse import quote
from urllib.parse import unquote
from PIL import Image  
import os



clients_by_uuid = {}  
pending_messages = {} 
  
async def register_client(websocket, path):   #传base64图片，当前进度，

    parsed_url = urlparse(path)  
    query_params = parse_qs(parsed_url.query)  
    uuid = query_params.get('uuid', [None])[0]  
    print("new Connect get Parm uuid =" + uuid )

    clients_by_uuid[uuid] = websocket  
    


    try:  

        async for message in websocket:  
            db = sqlite3.connect('fas.db')  
            cursor = db.cursor()
            data = json.loads(message) 
            uuid = data["uuid"]
            if not data["img"]: 
                await send_message_to_user(uuid,  quote(json.dumps({"rCode": "422", "rDesc": "没有传输图片字段"}, ensure_ascii=False)))  
                continue 
            
            
            strimg = pos.save_base64_image(data["img"])
            if not strimg:
                await send_message_to_user(uuid, quote(json.dumps({"rCode": "422", "rDesc": "保存图片失败"}, ensure_ascii=False)))  
                continue 

            Image.open(strimg).transpose(Image.FLIP_LEFT_RIGHT).save(strimg)   #因为用的cameraapi1，处理太麻烦了，只能在python处理了
            


            cursor.execute("SELECT * FROM fas WHERE uuid = ?"  , (uuid,))
            result = cursor.fetchone()
            if not  result:  
                await send_message_to_user(uuid, quote(json.dumps({"rCode": "422", "rDesc": "数据查找失败"}, ensure_ascii=False)))  
                continue
            
            try:
                mo,le,re = pos.procFrame(strimg)
            except:
                await send_message_to_user(uuid, quote(json.dumps({"rCode": "404", "rDesc": "没有找到人脸"}, ensure_ascii=False)))  
                continue

                
            
            


            posJson =  json.loads(unquote(result[1]))[int(result[3])] #解析当前的job
      
            if (posJson["l_eye_o"]==1) == le and (posJson["r_eye_o"]==1) == re  and (posJson["mouse_o"]==1)== mo:
                newIndex = int(result[3])+1
                if(newIndex)==3:
                    cursor.execute("UPDATE fas SET FaceImg = ? WHERE uuid = ?"  ,(strimg, uuid))
                    db.commit()
                    await send_message_to_user(uuid, quote(json.dumps({"rCode": "201", "rDesc": "人脸识别完成"}, ensure_ascii=False)))

                else:
                    cursor.execute("UPDATE fas SET current = ? WHERE uuid = ?"  ,(newIndex, uuid))
                    db.commit()
                    os.remove(strimg)
                    await send_message_to_user(uuid, quote(json.dumps({"rCode": "200", "rDesc": "人脸验证成功","index":result[3]}, ensure_ascii=False)))   
                   



            else:
                addition = "当前:"
                addition+="左眼:睁 " if(le) else "左眼:闭 "
                addition+="右眼:睁 " if(re) else "右眼:闭 "
                addition+="嘴:张开 " if(mo) else "嘴:闭上 "

                os.remove(strimg)

                await send_message_to_user(uuid, quote(json.dumps({"rCode": "400", "rDesc": "人脸验证失败:" + addition}, ensure_ascii=False)))  

            



            #print(f"Received message from {uuid}: {message}")  
    except websockets.exceptions.ConnectionClosed:  
        pass  # 连接正常关闭  
    finally:  
        # 当客户端断开连接时，从字典中移除它  
        if uuid in clients_by_uuid:  
            del clients_by_uuid[uuid]  
            print(f"Client {uuid} disconnected.")  
  
async def send_message_to_user(uuid, message):  
    global db
    try:  
        if uuid in clients_by_uuid:  
            websocket = clients_by_uuid[uuid]  
            await websocket.send(message)  

        else:  
            # 如果连接不存在，将消息添加到待发送消息字典中  
            if uuid not in pending_messages:  
                pending_messages[uuid] = []  
            pending_messages[uuid].append(message)  
            print(f"No active connection for user {uuid}. Message queued for later delivery.")  
    except Exception as e:  
        # 如果发送失败（例如，因为网络问题），也将消息添加到待发送消息字典中  
        print(f"Failed to send message to {uuid}: {e}")  
        if uuid not in pending_messages:  
            pending_messages[uuid] = []  
        pending_messages[uuid].append(message) 




  
async def main():  

    async with websockets.serve(register_client, "0.0.0.0", 7001):  
        print("Server started at ws://0.0.0.0:7001")  
        await asyncio.Future()  
  


if __name__ == "__main__":  
    global db
    db = sqlite3.connect('fas.db')  
    cursor = db.cursor()  
    cursor.execute('''CREATE TABLE IF NOT EXISTS fas(uuid TEXT NOT NULL,posJson Text NOT NULL,current Text NOT NULL)'''  )  
    db.commit()  


    asyncio.run(main())


