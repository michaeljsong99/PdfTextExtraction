import cv2
import numpy as np

img = cv2.imread("Resources/cards.jpg")

# We try to get King of Spades and "flatten" it.
cv2.imshow("Image", img)

# We need to get the 4 points of the corner of the King of spades. (already given)
pts1 = np.float32([[111, 219], [287, 188], [154, 482], [352, 440]])
# Need to define what each point is.
width,height = 250, 350 # a playing card is usually 2.5 x 3.5
pts2 = np.float32([[0,0], [width, 0], [0, height], [width, height]])

# Transform our image.
matrix = cv2.getPerspectiveTransform(pts1, pts2)
imgOutput = cv2.warpPerspective(img, matrix,(width, height))

cv2.imshow("Output", imgOutput)

cv2.waitKey(0)