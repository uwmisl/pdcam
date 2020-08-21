# pdcam

Captures video from camera on Raspberry PI, locates electrode grid in the frame,
and makes video + alignment data available via HTTP.

# Installation

`python setup.py install`

## Running tests

`pip install -e ".[testing]"`
`pytest`

## Dependencies

### OpenCV

I've tested with OpenCV v4. YMMV with v3 or v2.

# Usage

## Live image server

`pdcam server --reference ref.json`

Some available routes:

`/latest` or `/latest?markup=1`
`/video` or `/video?markup=1`
`/transform`

## Reference measurement

The electrode grid is located based on AprilTag fiducials placed on the board.
The location of the fiducials relative to the board can be measured by taking
an image of the board, and manually marking a series of control points with:

`pdcam measure image.jpg output.json`

The reference data stored in `output.json` can then be used later to locate
the electrode grid in another image captured from some arbitrary pose, as long
as the tags are detectable.

This is useful when taping paper fiducials onto a v3 electrode board, for example. 
When using electrode board v4, the fiducials are included in the PCB design, so 
they are known. A calibration for this board is included in `board_v4.json`. 

## Sample python code to find a transform

```python
import cv2
import json
from pdcam.grid import find_grid_transform, GridReference

with open('reference.json') as f:
    ref = GridReference.from_dict(json.loads(f.read()))

image = cv2.imread('image.jpg')
# transform is a 3x3 homography matrix that transforms from electrode grid to pixel coordinates
# fiducials is a list of grid.Fiducial objects with `label` and `corners` attributes
transform, fiducials = find_grid_transform(ref, image)
```

# Benchmarks

`find_grid_transform` takes 175ms on a raspbery pi 4.
