"""
This is the zone filtering utilities for the camera detection zones

Zones are stored as normalized polygons [[x, y], ...] from ranges 0.0-1.0

The detection boxes come in as pixel coordinates [x1, y1, x2, y2]
"""

from typing import List


def _point_in_polygon(px: float, py: float, polygon: List[List[float]]) -> bool:

    #making use of the ray-casting algorithm to check if a point (px, py) in inside a polygon :(

    length = len(polygon)
    inside_polygon = False
    j = length - 1

    for i in range(length):
        xi, yi = polygon[i]
        xj, yj = polygon[j]

        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside_polygon = not inside_polygon

        j = i


    
    return inside_polygon




def bbox_in_zone(bbox_xyxy: List[float], polygon: List[List[float]], frame_width: int, frame_height: int) -> bool:

    #return true if the centre of the boundary box falls inside the zone polygon


    x1, y1, x2, y2 = bbox_xyxy
    cx = ((x1 + x2) / 2) / frame_width #normalizes to 0-1
    cy = ((y1 + y2) / 2) / frame_height #also normalizes to 0-1


    return _point_in_polygon(cx, cy, polygon)





def filter_detections_by_zones(detections: List, zones: List[List[float]], frame_width: int, frame_height: int) -> list:


    #filtering YOLO detections to only those whose centre falls inside at least one zone
    #if no zones are defined, all detections can pass through


    if not zones:
        return detections #no zone has been configured -> so we can pass everything
    

    filtered = []

    for det in detections:
        bbox_xywh = det

        x, y, w, h = bbox_xywh
        bbox_xyxy = [x, y, x + w, y + h]

        for zone in zones:
            if bbox_in_zone(bbox_xyxy, zone, frame_width, frame_height):
                filtered.append(det)

                break #inside at least one zone, so keep and move on


    return filtered
