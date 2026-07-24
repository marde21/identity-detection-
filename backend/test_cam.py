import cv2
import config

print(f"Testing camera index {config.CAMERA_INDEX}...")
cap = cv2.VideoCapture(config.CAMERA_INDEX)
if not cap.isOpened():
    print("Failed to open camera.")
else:
    ret, frame = cap.read()
    if ret:
        print(f"Successfully read frame of shape {frame.shape}")
    else:
        print("Opened camera, but failed to read frame.")
    cap.release()
