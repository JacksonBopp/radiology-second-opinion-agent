import cv2
import numpy as np

# Common lung window for chest CT, in Hounsfield units. Chest X-rays
# don't carry HU values but the same clip-and-scale approach applies
# to their raw intensities.
LUNG_WINDOW_CENTER = -600
LUNG_WINDOW_WIDTH = 1500


def apply_windowing(
    pixels: np.ndarray, window_center: float, window_width: float
) -> np.ndarray:
    """Clip pixel values to [center - width/2, center + width/2] and
    rescale to [0, 1]. This mirrors the window/level adjustment a
    radiologist would apply when reading a scan.
    """
    low = window_center - window_width / 2
    high = window_center + window_width / 2
    clipped = np.clip(pixels, low, high)
    return (clipped - low) / (high - low)


def normalize_pixels(pixels: np.ndarray) -> np.ndarray:
    """Min-max normalize an array to [0, 1] using its own range.
    Use this when no clinically meaningful window is known (e.g. an
    X-ray without HU calibration).
    """
    pixels = pixels.astype(np.float64)
    min_val, max_val = pixels.min(), pixels.max()
    if max_val == min_val:
        return np.zeros_like(pixels)
    return (pixels - min_val) / (max_val - min_val)


def to_uint8(pixels: np.ndarray) -> np.ndarray:
    """Convert a [0, 1]-normalized float array to uint8 [0, 255],
    the format most CV model preprocessing pipelines expect.
    """
    return np.clip(pixels * 255.0, 0, 255).astype(np.uint8)


def resize_image(
    pixels: np.ndarray, target_size: tuple[int, int] = (224, 224)
) -> np.ndarray:
    """Resize a 2D image array to (height, width) via area interpolation,
    which avoids aliasing when downsampling high-resolution scans.
    """
    height, width = target_size
    return cv2.resize(pixels, (width, height), interpolation=cv2.INTER_AREA)
