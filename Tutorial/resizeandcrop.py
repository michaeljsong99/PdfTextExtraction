import cv2
import numpy as np

# Note that the origin (0,0) of the image is at the top-left corner.

img = cv2.imread("Resources/lambo.png")
# Get the size of the image
print(img.shape)

# Resize image.
imgResize = cv2.resize(img, (300, 200)) # width and height
print(imgResize.shape)

# Cropping an image.
imgCropped = img[0:200, 200:500] # while cropping, it is height,width - not width, height as above!

cv2.imshow("Image", img)
cv2.imshow("Image Resize", imgResize)
cv2.imshow("Image Cropped", imgCropped)
cv2.waitKey(0)