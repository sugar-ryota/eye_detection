from django.shortcuts import render, redirect
from .forms import VideoForm
from django.http import HttpResponse
import cv2
import tempfile
from django.urls import reverse
from urllib.parse import urlencode
import mediapipe as mp

def index(request):
    return render(request, './index.html')

def upload_video(request):
    if request.method == 'POST':
        # Mediapipeの初期化
        mp_drawing = mp.solutions.drawing_utils
        mp_holistic = mp.solutions.holistic
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

            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            # ファイルの処理を実行する場合はここに処理のコードを追加する

            # 保存する動画ファイル名と動画のパラメータを指定する
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter('output.mp4', fourcc, 30.0, (int(cap.get(3)), int(cap.get(4))))

            # 前のフレームの黒塗り座標を保持する変数
            previous_left_eye_top_left = None
            previous_left_eye_bottom_right = None
            previous_right_eye_top_left = None
            previous_right_eye_bottom_right = None

            with mp_holistic.Holistic(
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5) as holistic:

                # フレームごとに処理する
                while cap.isOpened():
                    # # フレームを読み込む
                    # ret, image = cap.read()

                    # # フレームを読み込めなかった場合は終了
                    # if not ret:
                    #     break

                    # # カスケード分類器を使用して顔を検出
                    # face_cascade = cv2.CascadeClassifier('conceal_eye/cascade_files/haarcascade_frontalface_default.xml')
                    # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    # faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                    # # 目の位置を検出して棒線で隠す
                    # for (x,y,w,h) in faces:
                    #     # 目の領域を検出
                    #     eyes = cv2.CascadeClassifier('conceal_eye/cascade_files/haarcascade_eye.xml')
                    #     eyes_roi = eyes.detectMultiScale(gray[y:y+h, x:x+w],minNeighbors=10)
                        
                    #     # 棒線を描画して目の領域を隠す
                    #     for (ex,ey,ew,eh) in eyes_roi:
                    #         roi = image[y+ey+int(1/4*eh):y+ey+int(1/4*eh)+int(1/2*eh), x+ex:x+ex+ew]
                    #         roi[:] = [0, 0, 0]

                    # # 描画したフレームを保存する
                    # out.write(image)
                    ret, frame = cap.read()

                    if not ret:
                        break

                    # Mediapipeを使用して顔の特徴点を検出
                    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = holistic.process(image)

                    if results.face_landmarks is not None:
                        landmarks = results.face_landmarks.landmark
                        # 特徴点の処理を行う

                        # 今回のフレームの黒塗り座標を更新
                        left_eye_top_left = [landmarks[225].x * frame_width, landmarks[225].y * frame_height]
                        left_eye_bottom_right = [landmarks[232].x * frame_width, landmarks[232].y * frame_height]
                        right_eye_top_left = [landmarks[441].x * frame_width, landmarks[441].y * frame_height]
                        right_eye_bottom_right = [landmarks[261].x * frame_width, landmarks[261].y * frame_height]

                        # 前のフレームの黒塗り座標を更新
                        previous_left_eye_top_left = left_eye_top_left
                        previous_left_eye_bottom_right = left_eye_bottom_right
                        previous_right_eye_top_left = right_eye_top_left
                        previous_right_eye_bottom_right = right_eye_bottom_right
                    else:
                        # results.face_landmarksがNoneの場合、前のフレームの座標を使用
                        if previous_left_eye_top_left is not None:
                            left_eye_top_left = previous_left_eye_top_left
                            left_eye_bottom_right = previous_left_eye_bottom_right
                            right_eye_top_left = previous_right_eye_top_left
                            right_eye_bottom_right = previous_right_eye_bottom_right

                    # 左眼の領域を塗りつぶす
                    cv2.rectangle(frame, (int(left_eye_top_left[0]), int(left_eye_top_left[1])),
                                (int(left_eye_bottom_right[0]), int(left_eye_bottom_right[1])), (0, 0, 0), -1)

                    # 右眼の領域を塗りつぶす
                    cv2.rectangle(frame, (int(right_eye_top_left[0]), int(right_eye_top_left[1])),
                                (int(right_eye_bottom_right[0]), int(right_eye_bottom_right[1])), (0, 0, 0), -1)

                    # 出力動画ファイルにフレームを書き込む
                    out.write(frame)
            redirect_url = reverse('download_video')
            parameters = urlencode({'title':video.title})
            url = f'{redirect_url}?{parameters}'
            return redirect(url)
            
    else:
        form = VideoForm()
    return render(request, 'upload.html', {'form': form})
    
def download_video(request):
    title = request.GET.get('title')
    # 処理した動画をダウンロードするためのレスポンスを作成する
    with open('output.mp4', 'rb') as f:
        print('きた')
        response = HttpResponse(f.read(), content_type='video/mp4')
        response['Content-Disposition'] = f'attachment; filename="{title}.mp4"'
    return response
