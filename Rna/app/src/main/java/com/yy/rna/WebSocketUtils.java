package com.yy.rna;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.util.Log;
import android.widget.Toast;


import org.json.JSONException;
import org.json.JSONObject;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.WebSocket;
import okhttp3.WebSocketListener;
import okio.ByteString;

public class WebSocketUtils {

    static WebSocketUtils webSocketUtils;
    static OkHttpClient client;
    static Context context;
    public  static  WebSocket webSocket;

    private onMessage onMessage;




    public static WebSocketUtils getInstance(Context mcontext){
        if (context != mcontext) context  = mcontext;

        if (webSocketUtils!=null) {
            return webSocketUtils;
        } else {
            webSocketUtils = new WebSocketUtils();
        }

        return webSocketUtils;
    }



    public  void close() {
        if (webSocket==null) return;
        webSocket.close(0,"");
    }

    public  void send(String text) {
        if (webSocket==null) return;
        webSocket.send(text);
    }


    private WebSocketUtils() {
        client=null;

        client = new OkHttpClient.Builder()
                .readTimeout(25, TimeUnit.SECONDS)//设置读取超时时间
                .writeTimeout(25, TimeUnit.SECONDS)//设置写的超时时间
                .connectTimeout(3, TimeUnit.SECONDS)//设置连接超时时间
                .build();

        WebSocketCreate();

    }





    public interface onMessage{
        void onMessage(String Message);
    }
    public void onMessage(onMessage onMessage) {
        this.onMessage = onMessage;
    }








    public static void WebSocketCreate() {

        String url = "ws://192.168.10.9:7001?uuid=123";



        Request request = new Request.Builder().get().url(url).build();
        webSocket =  client.newWebSocket(request, new WebSocketListener() {
            @Override
            public void onOpen(WebSocket webSocket, Response response) {
                super.onOpen(webSocket, response);

            }

            @Override
            public void onMessage(WebSocket webSocket, String text) {
                super.onMessage(webSocket, text);
                webSocketUtils.onMessage.onMessage(text);








            }

            @Override
            public void onMessage(WebSocket webSocket, ByteString bytes) {
                super.onMessage(webSocket, bytes);
            }

            @Override
            public void onClosing(WebSocket webSocket, int code, String reason) {
                super.onClosing(webSocket, code, reason);

                ((Activity)context).runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        Toast.makeText(context,"断开连接，活体检测结束",Toast.LENGTH_LONG).show();
                    }
                });
                ((Activity)context).finish();

            }

            @Override
            public void onClosed(WebSocket webSocket, int code, String reason) {
                super.onClosed(webSocket, code, reason);

                ((Activity)context).runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        Toast.makeText(context,"断开连接，活体检测结束",Toast.LENGTH_LONG).show();
                    }
                });
                ((Activity)context).finish();
            }

            @Override
            public void onFailure(WebSocket webSocket, Throwable t,  Response response) {
                super.onFailure(webSocket, t, response);

                ((Activity)context).runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        Toast.makeText(context,"断开连接，活体检测结束",Toast.LENGTH_LONG).show();
                    }
                });
                t.printStackTrace();
                ((Activity)context).finish();


            }
        });



}

}
