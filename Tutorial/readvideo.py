import cv2

# Read in and display a video.
cap = cv2.VideoCapture("Resources/test_video.mp4")

while True:
    success, img = cap.read()
    cv2.imshow("Video", img)
    # Add a keyboard key to break out of the loop.
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break