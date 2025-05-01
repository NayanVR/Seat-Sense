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

async def get_occupancy():
    global occupancy_data
    return str(occupancy_data)

VIDEO_PATH = os.path.join(BASE_DIR, 'static/video.mp4')

async def process_video_on_loop():
    global occupancy_data

    while True:
        cap = cv2.VideoCapture(VIDEO_PATH)
        
        if not cap.isOpened():
            logger.error(f"Failed to open video file at {VIDEO_PATH}")
            await asyncio.sleep(2)
            continue

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break  # End of video reached; restart loop

            # Convert frame to grayscale and save temporarily for processing
            temp_frame_path = os.path.join(BASE_DIR, 'static/temp_frame.png')
            # gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            cv2.imwrite(temp_frame_path, frame)

            # Run your existing occupancy detection logic
            occupancy = compute_occupancy(temp_frame_path)

            # Group and sort occupancy data
            grouped_sorted_occupancy_data = {}
            for seat, status in occupancy.items():
                row = seat[0]
                seat_number = seat[1:]
                if row not in grouped_sorted_occupancy_data:
                    grouped_sorted_occupancy_data[row] = {}
                grouped_sorted_occupancy_data[row][seat_number] = status

            occupancy_data = {
                row: dict(sorted(seats.items(), key=lambda x: int(x[0])))
                for row, seats in sorted(grouped_sorted_occupancy_data.items())
            }

            await manager.broadcast(str(occupancy_data))
            await asyncio.sleep(2)

        cap.release()
        await asyncio.sleep(1)  # Wait before restarting the video

async def compute_occupancy_periodically():
    global occupancy_data
    while True:
        occupancy = compute_occupancy(os.path.join(BASE_DIR, f"static/{np.random.randint(1, 7)}.png"))
        # Group and sort the occupancy data by row and seat number in one step
        grouped_sorted_occupancy_data = {}
        for seat, status in occupancy.items():
            row = seat[0]  # Extract the row label (e.g., 'A', 'B', etc.)
            seat_number = seat[1:]  # Extract the seat number as a string
            if row not in grouped_sorted_occupancy_data:
                grouped_sorted_occupancy_data[row] = {}
            grouped_sorted_occupancy_data[row][seat_number] = status

        # Sort rows alphabetically and seat numbers numerically
        occupancy_data = {
            row: dict(sorted(seats.items(), key=lambda x: int(x[0])))  # Sort seat numbers numerically
            for row, seats in sorted(grouped_sorted_occupancy_data.items())  # Sort rows alphabetically
        }

        await manager.broadcast(str(occupancy_data))
        await asyncio.sleep(2)

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