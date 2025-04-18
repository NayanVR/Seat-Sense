import asyncio
import os

import cv2
import numpy as np
from fastapi.logger import logger

from app.config import settings
from app.core.connection_manager import manager
from app.core.image_processing import (compute_ssim, edge_detection_roi,
                                       orb_align_image)
from app.core.seat_labels import bounding_boxes

occupancy_data = {}
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

async def compute_occupancy_periodically():
    global occupancy_data
    while True:
        occupancy_data = compute_occupancy(os.path.join(BASE_DIR, f"static/{np.random.randint(1, 7)}.png"))
        await manager.broadcast(str(occupancy_data))
        await asyncio.sleep(3)

def compute_occupancy(filled_image_path: np.ndarray, empty_image_path: np.ndarray = None) -> dict[str, bool]:
    try:
        if empty_image_path is None:
            empty_gray = cv2.imread(os.path.join(BASE_DIR, "static/empty-auditorium.png"), cv2.IMREAD_GRAYSCALE)
        else:
            empty_gray = cv2.imread(empty_image_path, cv2.IMREAD_GRAYSCALE)

        filled_gray = cv2.imread(filled_image_path, cv2.IMREAD_GRAYSCALE)
        aligned_filled_gray = orb_align_image(empty_gray, filled_gray)

        occupancy: dict[str, bool] = {}

        for label, (x, y, w, h) in bounding_boxes.items():
            region = aligned_filled_gray[y:y+h, x:x+w]
            edges = edge_detection_roi(region, 0, 0, w, h)

            if np.mean(edges) > settings.edge_threshold \
            and compute_ssim(empty_gray, aligned_filled_gray, x, y, w, h) < settings.ssim_threshold:
                occupancy[label] = 1
            else:
                occupancy[label] = 0

        return occupancy

    except Exception as e:
        logger.error(f"Error during occupancy detection: {e}")