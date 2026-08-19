import cv2 as cv
import numpy as np
from config import verifier

print("Verifier initialized.")
img = np.zeros((320, 320, 3), dtype=np.uint8)
verifier.detector.setInputSize((320, 320))
_, faces = verifier.detector.detect(img)
print("Detector worked, faces:", faces)
