import numpy as np

from src.ingestion.preprocess import (
    apply_windowing,
    normalize_pixels,
    resize_image,
    to_uint8,
)


def test_normalize_pixels_scales_to_unit_range():
    pixels = np.array([[0, 50], [100, 25]], dtype=np.float64)
    normalized = normalize_pixels(pixels)

    assert normalized.min() == 0.0
    assert normalized.max() == 1.0


def test_normalize_pixels_handles_constant_array():
    pixels = np.full((4, 4), 7.0)
    normalized = normalize_pixels(pixels)

    assert (normalized == 0).all()


def test_apply_windowing_clips_and_scales():
    pixels = np.array([-2000, -600, 750, 5000], dtype=np.float64)
    windowed = apply_windowing(pixels, window_center=-600, window_width=1500)

    assert windowed[0] == 0.0
    assert windowed[-1] == 1.0
    assert windowed[1] == 0.5


def test_to_uint8_output_range():
    pixels = np.array([[0.0, 0.5], [1.0, 0.25]])
    out = to_uint8(pixels)

    assert out.dtype == np.uint8
    assert out.min() >= 0
    assert out.max() <= 255


def test_resize_image_changes_shape():
    pixels = np.random.rand(512, 512).astype(np.float32)
    resized = resize_image(pixels, target_size=(224, 224))

    assert resized.shape == (224, 224)
