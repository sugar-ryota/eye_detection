from django.shortcuts import render, redirect
from .models import Video
from .forms import VideoForm
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import cv2
import tempfile
from django.http import FileResponse
import os

def index(request):
    return render(request, './index.html')

def upload_video(request):
    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save(commit=False)
            file = request.FILES['video_file']

            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
            # cv2.VideoCaptureで読み込む
            cap = cv2.VideoCapture(temp_file.name)
            # video.save()
            # ファイルの処理を実行する場合はここに処理のコードを追加する

            # 保存する動画ファイル名と動画のパラメータを指定する
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter('output.mp4', fourcc, 30.0, (int(cap.get(3)), int(cap.get(4))))

            # フレームごとに処理する
            while cap.isOpened():
                # フレームを読み込む
                ret, image = cap.read()

                # フレームを読み込めなかった場合は終了
                if not ret:
                    break

                # カスケード分類器を使用して顔を検出
                face_cascade = cv2.CascadeClassifier('conceal_eye/cascade_files/haarcascade_frontalface_default.xml')
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                # 目の位置を検出して棒線で隠す
                for (x,y,w,h) in faces:
                    # 目の領域を検出
                    eyes = cv2.CascadeClassifier('conceal_eye/cascade_files/haarcascade_eye.xml')
                    eyes_roi = eyes.detectMultiScale(gray[y:y+h, x:x+w],minNeighbors=10)
                    
                    # 棒線を描画して目の領域を隠す
                    for (ex,ey,ew,eh) in eyes_roi:
                        roi = image[y+ey+int(1/4*eh):y+ey+int(1/4*eh)+int(1/2*eh), x+ex:x+ex+ew]
                        roi[:] = [0, 0, 0]

                # 描画したフレームを保存する
                out.write(image)
            return redirect('download_video')
            
    else:
        form = VideoForm()
    return render(request, 'upload.html', {'form': form})
    
def download_video(request):
    # 処理した動画をダウンロードするためのレスポンスを作成する
    with open('output.mp4', 'rb') as f:
        print('きた')
        response = HttpResponse(f.read(), content_type='video/mp4')
        response['Content-Disposition'] = f'attachment; filename="sample.mp4"'
    return response
