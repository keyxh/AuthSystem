package com.yy.rna;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Matrix;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;

public class ImageUtil {

    public static File compressAndRoateimage(File imageFile, int quality) {
        BitmapFactory.Options options = new BitmapFactory.Options();
        options.inJustDecodeBounds = true;
        BitmapFactory.decodeFile(imageFile.getAbsolutePath(), options);

        int originalWidth = options.outWidth;
        int originalHeight = options.outHeight;
        options.inSampleSize = calculateInSampleSize(options, originalWidth, originalHeight);
        options.inJustDecodeBounds = false;
        Bitmap orginbitmap = BitmapFactory.decodeFile(imageFile.getAbsolutePath(), options);

        Matrix matrix = new Matrix();
        matrix.postRotate(-90);

        Bitmap bitmap = Bitmap.createBitmap(orginbitmap, 0, 0, orginbitmap.getWidth(), orginbitmap.getHeight(), matrix, true);



        File compressedFile = new File(imageFile.getParentFile(), "compressed_" + imageFile.getName());



        OutputStream os = null;
        try {
            os = new FileOutputStream(compressedFile);
            bitmap.compress(Bitmap.CompressFormat.JPEG, quality, os);
        } catch (IOException e) {
            e.printStackTrace();
        } finally {
            if (os != null) {
                try {
                    os.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
            // 回收Bitmap内存
            if (bitmap != null && !bitmap.isRecycled()) {
                bitmap.recycle();
            }
        }

        return compressedFile;
    }

    // 这是一个辅助方法，用于计算inSampleSize
    public static int calculateInSampleSize(BitmapFactory.Options options, int reqWidth, int reqHeight) {
        // 源图片的高度和宽度
        final int height = options.outHeight;
        final int width = options.outWidth;
        int inSampleSize = 1;

        if (height > reqHeight || width > reqWidth) {
            final int halfHeight = height / 2;
            final int halfWidth = width / 2;

            // 计算最大的inSampleSize值，它是2的幂并且小于或等于任何一边
            while ((halfHeight / inSampleSize) >= reqHeight && (halfWidth / inSampleSize) >= reqWidth) {
                inSampleSize *= 2;
            }
        }

        return inSampleSize;
    }











}
