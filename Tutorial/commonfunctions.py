import cv2
import numpy as np

img = cv2.imread("Resources/lena.png")

# Convert to grayscale
imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Blur the image.
imgBlur = cv2.GaussianBlur(imgGray,(7, 7), 0) # Kernel size has to be odd numbers

# Edge detection
imgCanny = cv2.Canny(img, 100, 100)
#imgCanny = cv2.Canny(img, 150, 200) # Increase threshold to reduce # of edges

# Dialation (make lines thicker)
kernel = np.ones((5,5), np.uint8) # 5x5 matric of 255bit unsigned ints.
imgDialation = cv2.dilate(imgCanny, kernel, iterations=1)

# Erosion (make lines thinner)
imgEroded = cv2.erode(imgDialation, kernel, iterations=1)

cv2.imshow("Gray Image", imgGray)
cv2.imshow("Blur Image", imgBlur)
cv2.imshow("Canny Image", imgCanny)
cv2.imshow("Dialation Image", imgDialation)
cv2.imshow("Eroded Image", imgEroded)

cv2.waitKey(0)