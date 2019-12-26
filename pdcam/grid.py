"""Utilities for locating the electrode grid in an image
"""
import cv2
import logging
import itertools
import numpy as np
from pyzbar.pyzbar import decode
from pyzbar.wrapper import ZBarSymbol
from typing import List, Dict, Tuple


logger = logging.getLogger()


class ControlPoint(object):
    def __init__(self, grid_coord: Tuple[float, float], image_coord: Tuple[float, float]):
        self.grid = grid_coord
        self.image = image_coord

class GridReference(object):
    """Represents locations extracted from a reference image of an electrode 
    board, which relate electrode grid positions to QR code positions, and can
    be used to compute a transform to locate elctrode grid positions into any
    image in which the same QR codes have been found. 

    Arguments:
    """
    def __init__(self, qrcodes: List[List[int]], control_points: List[ControlPoint]):
        if not isinstance(qrcodes, list):
            raise ValueError("qrcodes should be a list")

        self.qrcodes = qrcodes
        self.control_points = control_points

    @staticmethod
    def from_dict(data):
        qrcodes = data['qr']
        control_points = [
            ControlPoint(tuple(p['grid']), tuple(p['image']))
            for p in data['electrodes']
        ]
        return GridReference(qrcodes, control_points)


def sort_qr_codes(qr_a, qr_b):
    """Sort QR codes in a consistent ordering based on their relative positions. 

    In general, when we find QR codes in an image, we don't expect them to be 
    returned in a consistent order. Additionally, the image coordinate may be 
    rotated from image to image. Here we match qr codes by trying all permutations
    of matches and taking the best fit. We assume that the QR codes are all
    aligned in similar directions; this is a constraint on QR code placement.
    """

    qr_a = np.array(qr_a)
    qr_b = np.array(qr_b)

    # Get unit vectors defining our common coordinate system in each image
    ux_a = np.array([0.0, 0.0])
    ux_b = np.array([0.0, 0.0])
    for qr in qr_a:
        ux_a += qr[1] - qr[0]
    for qr in qr_b:
        ux_b += qr[1] - qr[0]
    ux_a /= np.mean(ux_a)
    ux_b /= np.mean(ux_b)


    def displacements(qrcodes, ux):
        uy = np.array([ux[1], ux[0]])
        #uy_b = np.array([ux_b[1], ux_b[0]])
        displacements = []
        for i in range(1, len(qrcodes)):
            d = qrcodes[i][0] - qrcodes[0][0]
            d2 = np.array([np.dot(ux, d), np.dot(uy, d)])
            displacements.append(d2)
        return np.array(displacements)

    best_error = float("inf")
    best_permutation = []
    d_a = displacements(qr_a, ux_a)
    for perm in itertools.permutations(qr_b):
        d_perm = displacements(perm, ux_b)
        error = np.sum(np.square(d_perm - d_a))
        if error < best_error:
            best_error = error
            best_permutation = perm

    return qr_a.tolist(), [p.tolist() for p in list(best_permutation)]


def find_grid_transform(reference: GridReference, image):
    """Provide transform to move from electrode grid coordinates to pixel 
    coordinates in a new image. 

    Arguments:
    * reference: Control points and QR codes from a reference/calibration image
        of the electrode board
    * image: An image (numpy array) of the reference board with all QR codes visible
    """

    qrinfo = decode(image, symbols=[ZBarSymbol.QRCODE])

    if len(qrinfo) != len(reference.qrcodes):
        logger.warn("Found %d qrcodes, needed %d", len(qrinfo), len(reference.qrcodes))
        return None, qrinfo

    # Reduce the decoded QR struct to list of corner lists, and match the order to the 
    # reference QR order based on their geometry
    refqr, dstqr = sort_qr_codes(reference.qrcodes, [q.polygon for q in qrinfo])

    def flatten(l):
        return [item for sublist in l for item in sublist]

    # Get transform from grid to reference image coordinates
    src_points = np.array([cp.grid for cp in reference.control_points])
    dst_points = np.array([cp.image for cp in reference.control_points])
    H0, _ = cv2.findHomography(src_points, dst_points)

    # Get transform from reference image to current image
    src_points = np.array([flatten(refqr)])
    dst_points = np.array([flatten(dstqr)])
    H1, _ = cv2.findHomography(src_points, dst_points)

    xform = np.dot(H1, H0)
    
    return xform, qrinfo
