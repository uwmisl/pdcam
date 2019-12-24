# pdcam

Captures video from camera on Raspberry PI, locates electrode grid in the frame,
and makes video + alignment data available via HTTP. 

## Dependencies

### OpenCV
I've tested with v4. YMMV with v3 or v2. 

### pyzbar fork

As of this writing, this applicatin will *NOT WORK* with the latest release of
pyzbar on Pypi, because it does not preserve the order of the QR corners, which
is needed to determine the QR code orientatin. See this PR:
https://github.com/NaturalHistoryMuseum/pyzbar/pull/39. In the meantime, you can
install from the master branch of https://github.com/sushil-bharati/pyzbar:

`pip install git+https://github.com/sushil-bharati/pyzbar`

You will also need libzbar:

e.g. `brew install zbar` or `apt-get install libzbar-dev`

## Usage

The electrode grid is located based on two QR codes placed on the board. 
The location of the QR codes relative to the board has to be measured by taking
an image of the board, and manually marking a series of control points with: 

`pdcam measure image.jpg output.json`

The reference data stored in `output.json` can then be used later to locate 
the electrode grid in another image captured from some arbitrary pose, as long
as the QR codes are detectable.

### Sample transform computatin

```python
import cv2
import json
from pdcam.grid import find_grid_transform, GridReference

with open('reference.json') as f:
    ref = GridReference.from_dict(json.loads(f.read()))

image = cv2.imread('image.jpg')
# transform is a 3x3 homography matrix
# qrcodes is a list of the decoded QR codes as returned by pyzbar decode
transform, qrcodes = find_grid_transform(ref, image)
```
