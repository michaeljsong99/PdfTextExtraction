import cv2

# Webcam object
cap = cv2.VideoCapture(0)

# Set size
cap.set(3, 640) # width
cap.set(4, 480) # height
cap.set(10, 100) # brightness

while True:
    success, img = cap.read()
    cv2.imshow("Video", img)
    # Add a keyboard key to break out of the loop.
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break