import cv2
import json
from pdcam.grid import GridReference, find_grid_transform
import pytest_benchmark


def test_benchmark(benchmark):
    image = cv2.imread('tests/data/qr1.jpg')
    with open('tests/data/cal.json') as f:
        refdata = json.loads(f.read())
    reference = GridReference.from_dict(refdata)
    benchmark(find_grid_transform, reference, image)
    