import numpy as np

from src.vision import CHEST_XRAY_LABELS, VisionModelBaseline, evaluate_multilabel
from src.vision.datasets import build_dataset_manifest
from src.vision.explainability import gradcam_heatmap
from src.vision.localization import segment_candidate_region
from src.vision.pipeline import analyze_image


def test_vision_pipeline_returns_findings_and_explainability():
    image = np.zeros((224, 224), dtype=np.uint8)
    image[70:150, 90:160] = 210

    result = analyze_image(image)

    assert result["model_name"] == "deterministic-vision-baseline"
    assert result["labels"] == CHEST_XRAY_LABELS
    assert len(result["probabilities"]) == len(CHEST_XRAY_LABELS)
    assert result["localization"]["bbox"][2] > 0
    assert result["explainability"]["heatmap_shape"] == [224, 224]
    assert isinstance(result["findings"], list)


def test_baseline_model_uncertainty_shape_matches_labels():
    model = VisionModelBaseline()
    image = np.full((224, 224), 0.45, dtype=np.float32)

    uncertainty = model.monte_carlo_uncertainty(image, samples=4)

    assert uncertainty.shape == (len(CHEST_XRAY_LABELS),)
    assert float(uncertainty.min()) >= 0.0


def test_localization_and_heatmap_are_normalized():
    image = np.zeros((64, 64), dtype=np.uint8)
    image[20:40, 20:40] = 255

    localization = segment_candidate_region(image, min_area_fraction=0.001)
    heatmap = gradcam_heatmap(image)

    assert localization["bbox"][2] > 0
    assert heatmap.shape == image.shape
    assert 0.0 <= float(heatmap.min()) <= float(heatmap.max()) <= 1.0


def test_evaluate_multilabel_reports_clinical_metrics():
    truth = np.array([[1, 0], [0, 1], [1, 1]])
    score = np.array([[0.9, 0.2], [0.1, 0.8], [0.7, 0.6]])

    metrics = evaluate_multilabel(truth, score, threshold=0.5)

    assert metrics["macro_auc"] == 1.0
    assert metrics["macro_sensitivity"] == 1.0
    assert metrics["macro_specificity"] == 1.0


def test_build_dataset_manifest_collects_images(tmp_path):
    image_path = tmp_path / "patient1.png"
    image_path.write_bytes(b"not-a-real-image-but-valid-manifest-entry")

    records = build_dataset_manifest(tmp_path, dataset_name="chexpert", split="train")

    assert len(records) == 1
    assert records[0].dataset == "chexpert"
    assert records[0].split == "train"
