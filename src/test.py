from ultralytics import YOLO


MODEL_PATH = "yolo11n.pt"

model = YOLO(MODEL_PATH)
model.to('cuda')


detections = model(0, stream=True)

print(detections)

while(True):
    pass


