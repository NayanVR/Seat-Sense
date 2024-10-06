import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

def compute_ssim(empty_gray, aligned_filled_gray, x, y, w, h):
    region_labeled = empty_gray[y:y+h, x:x+w]
    region_filled = aligned_filled_gray[y:y+h, x:x+w]

    # Determine the smaller side of the region and set an appropriate win_size
    min_dim = min(region_labeled.shape[0], region_labeled.shape[1])

    # Set win_size to the maximum of 3 and an odd number <= min_dim
    win_size = min(min_dim, 7)  # Max win_size can be 7
    if win_size % 2 == 0:
        win_size -= 1  # Ensure it's odd

    score, diff = ssim(region_labeled, region_filled, full=True, win_size=win_size)
    return score

def edge_detection_roi(image, x, y, w, h):
    region = image[y:y+h, x:x+w]
    edges = cv2.Canny(region, 200, 300)

    customFilter = np.array([[-1,2,-1],[-1,2,-1],[-1,2,-1]])
    edges = cv2.filter2D(src=edges, kernel=customFilter, ddepth=-1);

    return edges

def orb_align_image(source_gray, target_gray):
    orb = cv2.ORB_create(5000)
    keypoints1, descriptors1 = orb.detectAndCompute(source_gray, None)
    keypoints2, descriptors2 = orb.detectAndCompute(target_gray, None)

    # Match features.
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(descriptors1, descriptors2)

    # Sort them in the order of their distance.
    matches = sorted(matches, key=lambda x: x.distance)

    # Extract location of good matches
    src_pts = np.float32([keypoints1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([keypoints2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

    # Compute homography matrix to align the images
    matrix, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)

    # Align the source image with respect to the target image
    aligned_target_gray = cv2.warpPerspective(target_gray, matrix, (source_gray.shape[1], source_gray.shape[0]))

    return aligned_target_gray