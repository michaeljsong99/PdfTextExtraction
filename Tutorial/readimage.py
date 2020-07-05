import cv2

# Import and show a picture
img = cv2.imread("../Resources/lena.png")
cv2.imshow("Output", img)
cv2.waitKey(0) # infinite delay
