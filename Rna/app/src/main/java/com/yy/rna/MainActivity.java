package com.yy.rna;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;

import android.Manifest;
import android.content.Intent;
import android.graphics.Outline;
import android.graphics.Rect;
import android.graphics.YuvImage;
import android.hardware.Camera;
import android.media.MediaPlayer;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;
import android.os.StrictMode;
import android.util.Log;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.View;
import android.view.ViewOutlineProvider;
import android.widget.Toast;

import com.yy.rna.databinding.ActivityMainBinding;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.net.URLDecoder;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class MainActivity extends AppCompatActivity implements SurfaceHolder.Callback {

    ActivityMainBinding binding;
    private Camera mCamera;
    private SurfaceView mPreview;
    JSONArray actionArray;
    int index;
    MediaPlayer mediaPlayer;
    long lastTime =0;
    WebSocketUtils webSocketUtils;

    @Override
    protected void onDestroy() {
        super.onDestroy();
        try {
            if (mediaPlayer != null) {
                mediaPlayer.stop();
                mediaPlayer.release();
                mediaPlayer = null;
            }

        } catch (Exception e) {

        }


    }






    void getPos() {
        StrictMode.ThreadPolicy policy = new StrictMode
                .ThreadPolicy
                .Builder()
                .permitAll()
                .build(); //放入主线程
        StrictMode.setThreadPolicy(policy);
        OkHttpClient client = new OkHttpClient().newBuilder().build();

        RequestBody body = new MultipartBody.Builder().setType(MultipartBody.FORM)
                .addFormDataPart("uuid","123")
                .build();
        Request request = new Request.Builder()
                .url("http://192.168.10.9:7000/api/detecting/Create")
                .method("POST", body)
                .build();
        try {
            Response response = client.newCall(request).execute();
            String result = response.body().string();
            if (new JSONObject(result).getString("rCode").equals("200")) {
                actionArray=new JSONObject(result).getJSONArray("actionArray");

                showAction();
            }
        } catch (IOException | JSONException e) {
            Toast.makeText(this,"发生异常",Toast.LENGTH_SHORT).show();
            e.printStackTrace();
        }
    }


    void showAction() {

        JSONObject posJob = null;
        try {
            posJob = actionArray.getJSONObject(index);
            binding.message.setText(posJob.getString("message"));
            binding.current.setText(index + "/" + (actionArray.length()) );

            mediaPlayer.reset();
            mediaPlayer.setDataSource("http://192.168.10.9:7000/getAudio/"+posJob.getString("audio"));
            mediaPlayer.prepare();
            mediaPlayer.start();

            index++;
        } catch (JSONException | IOException e) {
            e.printStackTrace();
        }
    }





    public  String  DecodeUtf8(String txt) {
        String decodedText="";
        try {
            decodedText = URLDecoder.decode(txt, "UTF-8");
        } catch (UnsupportedEncodingException e) {
            e.printStackTrace();
        }
        return decodedText;
    }



    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding= ActivityMainBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());
        mediaPlayer  = new MediaPlayer();

        ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE}, 1);
        getPos();
        webSocketUtils=WebSocketUtils.getInstance(this);
        webSocketUtils.onMessage(new WebSocketUtils.onMessage() {
            @Override
            public void onMessage(String message) {
                String getMsg = DecodeUtf8(message);
                runOnUiThread(new Runnable() {
                    @Override
                    public void run() {

                        try {
                            JSONObject job = new JSONObject(getMsg);
                            binding.serverMsg.setText(job.getString("rDesc"));
                            if (job.getString("rCode").equals("200")) {
                                mediaPlayer.reset();
                                mediaPlayer.setDataSource("http://192.168.10.9:7000/getAudio/success");
                                mediaPlayer.prepare();
                                mediaPlayer.start();
                                showAction();

                            } else if (job.getString("rCode").equals("201")){

                                binding.current.setText(3 + "/" + 3);
                                mediaPlayer.reset();
                                mediaPlayer.setDataSource("http://192.168.10.9:7000/getAudio/finish");
                                mediaPlayer.prepare();
                                mediaPlayer.start();
                                startActivity(new Intent(MainActivity.this,AuthActivity.class));
                                finish();


                            }
                        } catch (JSONException | IOException e) {
                            e.printStackTrace();
                        }
                    }
                });


            }
        });


        mPreview = binding.surfaceView;
        mPreview.getHolder().addCallback(this);


    }


    public void UploadImgFile(File imgFile) throws IOException, JSONException {
        File compressFile = ImageUtil.compressAndRoateimage(imgFile,100);
        byte[] bytes = new byte[(int) compressFile.length()];
        FileInputStream fis = null;
        fis = new FileInputStream(compressFile);
        fis.read(bytes);
        JSONObject job =new JSONObject();
        job.put("uuid","123");
        job.put("img",Base64Utils.encode(bytes));
        webSocketUtils.send(job.toString());
        imgFile.delete();
        compressFile.delete();

    }







    public void surfaceCreated(SurfaceHolder holder) {
        try {
            // 打开相机
            mCamera = Camera.open(findFrontFacingCamera());

            mCamera.setDisplayOrientation(90);//将预览旋转90度
            if (mCamera != null) {
                // 设置预览显示
                mCamera.setPreviewDisplay(holder);
            }


            mCamera.setPreviewCallback(new Camera.PreviewCallback() {
                @Override
                public void onPreviewFrame(byte[] data, Camera camera) {
                    try {
                        if (lastTime == 0 || System.currentTimeMillis() - lastTime >= 2000) {
                            // 假设预览大小已经通过某种方式获取，例如从 Camera.Parameters
                            Camera.Parameters parameters = camera.getParameters();
                            Camera.Size previewSize = parameters.getPreviewSize();

                            YuvImage yuvImage = new YuvImage(data, parameters.getPreviewFormat(), previewSize.width, previewSize.height, null);


                            ByteArrayOutputStream out = new ByteArrayOutputStream();
                            yuvImage.compressToJpeg(new Rect(0, 0, previewSize.width, previewSize.height), 80, out);

                            File outputFile = File.createTempFile("temp", ".jpg");
                            FileOutputStream fos = new FileOutputStream(outputFile);
                            fos.write(out.toByteArray());
                            fos.close();

                            UploadImgFile(outputFile);

                            lastTime = System.currentTimeMillis();
                        }
                    } catch (IOException | JSONException e) {
                        e.printStackTrace();
                    }
                }
            });


        } catch (Exception e) {
            e.printStackTrace();
        }
    }


    public void surfaceChanged(SurfaceHolder holder, int format, int width, int height) {
        if (mCamera != null) {
            Camera.Parameters parameters = mCamera.getParameters();

            // 获取支持的预览大小列表
            List<Camera.Size> previewSizes = parameters.getSupportedPreviewSizes();

            // 选择最佳预览大小
            Camera.Size bestPreviewSize = null;
            int minDiff = Integer.MAX_VALUE;
            int targetRatio = width * height;

            for (Camera.Size size : previewSizes) {
                // 计算当前预览大小与SurfaceHolder尺寸的宽高比差异
                int diff = Math.abs(size.width * size.height - targetRatio);

                // 如果差异更小，则更新最佳预览大小
                if (diff < minDiff) {
                    bestPreviewSize = size;
                    minDiff = diff;
                }
            }

            if (bestPreviewSize != null) {
                // 设置预览大小
                parameters.setPreviewSize(bestPreviewSize.width, bestPreviewSize.height);

                // 注意：这里您可能还需要调整SurfaceView的LayoutParams，
                // 但通常建议在布局文件中或通过其他方式预先设置好SurfaceView的大小，
                // 以避免在预览过程中修改大小导致的闪烁或其他问题。

                // 应用参数
                mCamera.setParameters(parameters);
                mCamera.startPreview();
            }
        }
    }


    public void surfaceDestroyed(SurfaceHolder holder) {
        if (mCamera != null) {
            mCamera.stopPreview();
            mCamera.release();
            mCamera = null;
        }
    }

    private int findFrontFacingCamera() {
        int cameraId = -1;
        int numberOfCameras = Camera.getNumberOfCameras();
        for (int i = 0; i < numberOfCameras; i++) {
            Camera.CameraInfo info = new Camera.CameraInfo();
            Camera.getCameraInfo(i, info);
            if (info.facing == Camera.CameraInfo.CAMERA_FACING_FRONT) {
                cameraId = i;
                break;
            }
        }
        return cameraId;
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (mCamera != null) {
            mCamera.release();
            mCamera = null;
        }
    }









    @Override
    public void onPointerCaptureChanged(boolean hasCapture) {

    }
}