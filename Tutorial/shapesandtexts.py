import cv2
import numpy as np

# Black box (0 = black, 255 = white)
img = np.zeros((512, 512, 3), np.uint8)

# Color the whole image blue:
# img[:]= 255, 0, 0 # The colon is to color the entire selection

# Draw a green line from (0,0) to (300,300)
cv2.line(img,(0, 0), (300, 300), (0, 255, 0), 3)

# Draw a red rectangle and fill it.
cv2.rectangle(img, (0, 0), (250, 350), (0, 0, 255), cv2.FILLED)

# Draw a circle.
cv2.circle(img, (400, 50), 30, (255, 255, 0), 5)

# Put text on images.
cv2.putText(img, "LEBRON", (300, 200), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 150, 0), 1)

cv2.imshow("Image", img)
cv2.waitKey(0)