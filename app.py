from flask import Flask, render_template, Response
import cv2
import numpy as np

app = Flask(__name__)
# Thay đổi 0 thành đường dẫn của file video nếu bạn không sử dụng webcam
cap = cv2.VideoCapture(0)

# Đọc mô hình YOLOv3 và các tệp cấu hình
net = cv2.dnn.readNet("yolo/yolov3.weights", "yolo/yolov3.cfg")
with open("yolo/coco.names", "r") as f:
    classes = f.read().strip().split("\n")

# Hàm phát hiện đối tượng
def detect_objects(frame):
    height, width = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (220, 220), swapRB=True, crop=False)
    net.setInput(blob)
    layer_names = net.getUnconnectedOutLayersNames()
    detections = net.forward(layer_names)
    boxes = []
    confidences = []
    class_ids = []

    for output in detections:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:  # Ngưỡng tin cậy
                box = detection[0:4] * np.array([width, height, width, height])
                (centerX, centerY, w, h) = box.astype("int")
                x = int(centerX - (w / 2))
                y = int(centerY - (h / 2))
                boxes.append([x, y, int(w), int(h)])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    idxs = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

    if len(idxs) > 0:
        for i in idxs.flatten():
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])

            color = [int(c) for c in np.random.uniform(0, 255, 3)]
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            text = "{}: {:.4f}".format(classes[class_ids[i]], confidences[i])
            cv2.putText(frame, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    return frame

# Hàm sinh frame cho video stream
def generate_frames():
    frame_id = 0
    while True:
        success, frame = cap.read()
        if not success:
            break

        frame_id += 1
        if frame_id % 2 == 0:  # Chỉ xử lý mỗi khung hình thứ hai
            frame = detect_objects(frame)

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/')
def index():
    return render_template('Intro.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
