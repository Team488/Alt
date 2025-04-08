import cv2
from inference import utils

img = cv2.imread("assets/testFrame.png")

letterboxed = utils.letterbox_image(img.copy(), target_size=(2000, 2000))

originalBox = [-1, 17, 600, 534]

cv2.rectangle(letterboxed, originalBox[:2], originalBox[2:], (255, 255, 0), 1)

unLetterBoxed = utils.rescaleBox(originalBox, img.shape, target_size=(2000, 2000))
cv2.rectangle(
    img,
    (int(unLetterBoxed[0]), int(unLetterBoxed[1])),
    (int(unLetterBoxed[2]), int(unLetterBoxed[3])),
    (255, 255, 0),
    1,
)


cv2.imshow("Original", img)
cv2.imshow("letterboxed", letterboxed)

cv2.waitKey(3)
