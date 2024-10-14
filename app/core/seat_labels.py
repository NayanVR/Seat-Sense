import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_bounding_boxes():
    with open(os.path.join(BASE_DIR, "static/seat_labels.json")) as f:
        data = json.load(f)

    bounding_boxes = {}
    
    for annotation in data['annotations']:
        # Get the bounding box (x, y, width, height)
        bbox = [int(point) for point in annotation['bbox']]
        attributes = annotation['attributes']

        label = attributes['Label']

        bounding_boxes[label] = bbox

    return bounding_boxes

bounding_boxes = get_bounding_boxes()