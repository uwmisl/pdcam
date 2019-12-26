import cv2
import numpy as np
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon

def template_polygons(layout, transform):
    MARGIN = 0.15
    polygons = {}
    for y in range(len(layout)):
        for x in range(len(layout[0])):
            if layout[y][x] is None:
                continue

            points = np.array([
                (x+MARGIN, y+MARGIN), 
                (x + 1 - MARGIN, y+MARGIN),
                (x + 1 - MARGIN, y + 1 - MARGIN),
                (x+MARGIN, y + 1 - MARGIN)
            ])
            points = cv2.perspectiveTransform(np.array([points]), transform)[0][:, 0:2]
            polygons[(x, y)] = points
    
    return polygons

def mark_template(img, layout, transform=None):
    if transform is None:
        transform = np.eye(3, 3)
    polygons = template_polygons(layout, transform)

    points = np.array(list(polygons.values()), dtype=np.int32)
    cv2.polylines(img, points, True, (0, 0, 255), 3)
    
def plot_template(ax, layout, highlights=None, transform=None):
    if transform is None:
        transform = np.eye(3, 3)
    if highlights is None:
        highlights = []
    normal_boxes = []
    highlight_boxes = []

    polygons = template_polygons(layout, transform)

    highlight_boxes = [Polygon(points) for coord, points in polygons.items() if coord in highlights]
    normal_boxes = [Polygon(points) for coord, points in polygons.items() if coord not in highlights]
    
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