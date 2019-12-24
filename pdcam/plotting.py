import cv2
import numpy as np
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon

def plot_template(ax, layout, highlights=None, transform=None):
    if transform is None:
        transform = np.eye(3, 3)
    if highlights is None:
        highlights = []
    # Create list for all the error patches
    normal_boxes = []
    highlight_boxes = []
    # Loop over data points; create box from errors at each point
    MARGIN = 0.15
    for y in range(len(layout)):
        for x in range(len(layout[0])):
            points = np.array([
                (x+MARGIN, y+MARGIN), 
                (x + 1 - 2*MARGIN, y+MARGIN),
                (x + 1 - 2*MARGIN, y + 1 - 2*MARGIN),
                (x+MARGIN, y + 1 - 2*MARGIN)
            ])
            points = cv2.perspectiveTransform(np.array([points]), transform)[0][:, 0:2]

            #rect = Rectangle((x0, y0), x1 - x0, y1 - y0) 
            #rect = Rectangle((x+MARGIN, y+MARGIN), 1 - 2*MARGIN, 1-2*MARGIN)
            #print(points)
            rect = Polygon(points)
            electrode_num = layout[y][x]
            if electrode_num is None: 
                continue
            elif (x, y) in highlights:
                highlight_boxes.append(rect)
            else:
                normal_boxes.append(rect)
    
    normal_pc = PatchCollection(normal_boxes, facecolor='b', alpha=1.0,
                         edgecolor='b')
    highlight_pc = PatchCollection(highlight_boxes, facecolor='r', alpha=1.0,
                         edgecolor='r')
    
    ax.add_collection(normal_pc)
    ax.add_collection(highlight_pc)

    ax.update_datalim([[0, 0], [len(layout[0]), len(layout)]])
    ax.axis('equal')
    ax.autoscale()
    return

def mark_qr_code(img, polygon):
    p = polygon
    cv2.line(img, (p[0].x, p[0].y), (p[1].x, p[1].y), (0, 0, 255), 2)
    cv2.line(img, (p[1].x, p[1].y), (p[2].x, p[2].y), (0, 0, 255), 2)
    cv2.line(img, (p[2].x, p[2].y), (p[3].x, p[3].y), (0, 0, 255), 2)
    cv2.line(img, (p[3].x, p[3].y), (p[0].x, p[0].y), (0, 0, 255), 2)
    cv2.circle(img, (p[0].x, p[0].y), 3, (0, 255, 0), 3)