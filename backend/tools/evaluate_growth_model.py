"""Evaluate the growth segmentation model against LabelMe polygon annotations.

The script runs the application detector on annotated images, compares predicted
mask polygons with human polygons, and writes machine-readable reports.
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.models.ai.yolo_detector import YOLODetector


DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[1] / "app" / "models" / "ai" / "best.pt"
DEFAULT_ANNOTATED_DIR = Path(r"D:\文件\易找的文件\智慧渔业\图片标注\11~19标注完")
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "reports" / "growth-model-eval"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
DEFAULT_LABELS = {"fish", "fish_measurable"}
CM_PER_PIXEL = 0.1


@dataclass
class Annotation:
    index: int
    label: str
    polygon: list[list[float]]


@dataclass
class Prediction:
    index: int
    confidence: float
    bbox: list[float]
    length_px: float
    polygon: list[list[float]]


@dataclass
class Match:
    gt_index: int
    pred_index: int
    iou: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate the growth YOLO segmentation model with LabelMe annotations."
    )
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--annotated-dir", type=Path, default=DEFAULT_ANNOTATED_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--iou-threshold", type=float, default=0.5)
    parser.add_argument(
        "--labels",
        nargs="*",
        default=sorted(DEFAULT_LABELS),
        help="LabelMe labels that count as fish annotations.",
    )
    parser.add_argument(
        "--save-overlays",
        action="store_true",
        help="Save visual overlays with ground truth and predictions.",
    )
    return parser.parse_args()


def load_labelme_annotations(json_path: Path, allowed_labels: set[str]) -> list[Annotation]:
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    annotations: list[Annotation] = []
    for shape in payload.get("shapes", []):
        label = str(shape.get("label", ""))
        points = shape.get("points", [])
        if label not in allowed_labels or len(points) < 3:
            continue
        annotations.append(
            Annotation(
                index=len(annotations),
                label=label,
                polygon=[[float(x), float(y)] for x, y in points],
            )
        )
    return annotations


def image_to_base64(image_path: Path) -> str:
    return base64.b64encode(image_path.read_bytes()).decode("utf-8")


def run_detector(detector: YOLODetector, image_path: Path) -> tuple[list[Prediction], float]:
    started = time.perf_counter()
    result = detector.detect(image_to_base64(image_path))
    elapsed_ms = (time.perf_counter() - started) * 1000

    image_meta = result["image"]
    image_width = float(image_meta["width"])
    image_height = float(image_meta["height"])
    predictions: list[Prediction] = []

    for raw in result["detections"]:
        normalized_polygon = raw.get("mask_polygons") or []
        pixel_polygon = [
            [float(point[0]) * image_width, float(point[1]) * image_height]
            for point in normalized_polygon
            if len(point) >= 2
        ]
        predictions.append(
            Prediction(
                index=len(predictions),
                confidence=float(raw.get("confidence", 0)),
                bbox=[float(value) for value in raw.get("bbox", [])],
                length_px=float(raw.get("length", 0)),
                polygon=pixel_polygon,
            )
        )
    return predictions, elapsed_ms


def polygon_to_mask(polygon: list[list[float]], shape: tuple[int, int]) -> np.ndarray:
    mask = np.zeros(shape, dtype=np.uint8)
    if len(polygon) < 3:
        return mask
    points = np.array(polygon, dtype=np.float32).round().astype(np.int32)
    cv2.fillPoly(mask, [points], 1)
    return mask


def mask_iou(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    intersection = np.logical_and(mask_a, mask_b).sum()
    union = np.logical_or(mask_a, mask_b).sum()
    if union == 0:
        return 0.0
    return float(intersection / union)


def compute_iou_matrix(
    annotations: list[Annotation],
    predictions: list[Prediction],
    image_shape: tuple[int, int],
) -> np.ndarray:
    matrix = np.zeros((len(annotations), len(predictions)), dtype=np.float32)
    gt_masks = [polygon_to_mask(annotation.polygon, image_shape) for annotation in annotations]
    pred_masks = [polygon_to_mask(prediction.polygon, image_shape) for prediction in predictions]

    for gt_index, gt_mask in enumerate(gt_masks):
        for pred_index, pred_mask in enumerate(pred_masks):
            matrix[gt_index, pred_index] = mask_iou(gt_mask, pred_mask)
    return matrix


def greedy_match(iou_matrix: np.ndarray, iou_threshold: float) -> list[Match]:
    candidates: list[tuple[float, int, int]] = []
    for gt_index in range(iou_matrix.shape[0]):
        for pred_index in range(iou_matrix.shape[1]):
            iou = float(iou_matrix[gt_index, pred_index])
            if iou >= iou_threshold:
                candidates.append((iou, gt_index, pred_index))

    matches: list[Match] = []
    used_gt: set[int] = set()
    used_pred: set[int] = set()
    for iou, gt_index, pred_index in sorted(candidates, reverse=True):
        if gt_index in used_gt or pred_index in used_pred:
            continue
        used_gt.add(gt_index)
        used_pred.add(pred_index)
        matches.append(Match(gt_index=gt_index, pred_index=pred_index, iou=iou))
    return matches


def safe_mean(values: list[float]) -> float:
    return float(statistics.mean(values)) if values else 0.0


def find_image_for_annotation(json_path: Path) -> Path | None:
    for suffix in IMAGE_SUFFIXES:
        candidate = json_path.with_suffix(suffix)
        if candidate.exists():
            return candidate
    return None


def evaluate_image(
    detector: YOLODetector,
    image_path: Path,
    json_path: Path,
    allowed_labels: set[str],
    iou_threshold: float,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[Annotation], list[Prediction], list[Match]]:
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Failed to read image: {image_path}")
    height, width = image.shape[:2]

    annotations = load_labelme_annotations(json_path, allowed_labels)
    predictions, elapsed_ms = run_detector(detector, image_path)
    predictions_with_masks = [prediction for prediction in predictions if len(prediction.polygon) >= 3]
    iou_matrix = compute_iou_matrix(annotations, predictions_with_masks, (height, width))
    matches = greedy_match(iou_matrix, iou_threshold)
    matched_gt = {match.gt_index for match in matches}
    matched_pred = {match.pred_index for match in matches}
    best_iou_by_gt = (
        [float(iou_matrix[gt_index].max()) for gt_index in range(len(annotations))]
        if predictions_with_masks
        else [0.0 for _ in annotations]
    )

    row = {
        "image": image_path.name,
        "gt_count": len(annotations),
        "pred_count": len(predictions),
        "pred_mask_count": len(predictions_with_masks),
        "matched_count": len(matches),
        "false_positive_count": len(predictions_with_masks) - len(matched_pred),
        "false_negative_count": len(annotations) - len(matched_gt),
        "precision": len(matches) / len(predictions_with_masks) if predictions_with_masks else 0.0,
        "recall": len(matches) / len(annotations) if annotations else 0.0,
        "mean_match_iou": safe_mean([match.iou for match in matches]),
        "mean_best_iou_by_gt": safe_mean(best_iou_by_gt),
        "mean_confidence": safe_mean([prediction.confidence for prediction in predictions]),
        "mean_length_px": safe_mean([prediction.length_px for prediction in predictions]),
        "mean_length_cm": safe_mean([prediction.length_px * CM_PER_PIXEL for prediction in predictions]),
        "latency_ms": elapsed_ms,
    }

    match_rows = [
        {
            "image": image_path.name,
            "gt_index": match.gt_index,
            "pred_index": match.pred_index,
            "iou": match.iou,
            "pred_confidence": predictions_with_masks[match.pred_index].confidence,
            "pred_length_px": predictions_with_masks[match.pred_index].length_px,
        }
        for match in matches
    ]
    return row, match_rows, annotations, predictions_with_masks, matches


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def draw_overlay(
    image_path: Path,
    output_path: Path,
    annotations: list[Annotation],
    predictions: list[Prediction],
    matches: list[Match],
) -> None:
    image = cv2.imread(str(image_path))
    if image is None:
        return

    matched_gt = {match.gt_index for match in matches}
    matched_pred = {match.pred_index for match in matches}

    for annotation in annotations:
        color = (0, 200, 0) if annotation.index in matched_gt else (0, 0, 255)
        points = np.array(annotation.polygon, dtype=np.float32).round().astype(np.int32)
        cv2.polylines(image, [points], True, color, 2)
        x, y = points[0]
        cv2.putText(image, f"GT {annotation.index}", (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    for prediction in predictions:
        color = (255, 200, 0) if prediction.index in matched_pred else (255, 0, 0)
        points = np.array(prediction.polygon, dtype=np.float32).round().astype(np.int32)
        cv2.polylines(image, [points], True, color, 2)
        if len(points):
            x, y = points[0]
            cv2.putText(
                image,
                f"P {prediction.index} {prediction.confidence:.2f}",
                (int(x), int(y) + 16),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), image)


def summarize(rows: list[dict[str, Any]], match_rows: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    gt_total = sum(int(row["gt_count"]) for row in rows)
    pred_mask_total = sum(int(row["pred_mask_count"]) for row in rows)
    matched_total = sum(int(row["matched_count"]) for row in rows)
    precision = matched_total / pred_mask_total if pred_mask_total else 0.0
    recall = matched_total / gt_total if gt_total else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0

    return {
        "model": str(args.model),
        "annotated_dir": str(args.annotated_dir),
        "confidence_threshold": args.conf,
        "iou_threshold": args.iou_threshold,
        "labels": args.labels,
        "image_count": len(rows),
        "gt_total": gt_total,
        "pred_total": sum(int(row["pred_count"]) for row in rows),
        "pred_mask_total": pred_mask_total,
        "matched_total": matched_total,
        "false_positive_total": sum(int(row["false_positive_count"]) for row in rows),
        "false_negative_total": sum(int(row["false_negative_count"]) for row in rows),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "mean_match_iou": safe_mean([float(row["iou"]) for row in match_rows]),
        "mean_best_iou_by_gt": safe_mean([float(row["mean_best_iou_by_gt"]) for row in rows]),
        "mean_confidence": safe_mean([float(row["mean_confidence"]) for row in rows]),
        "mean_latency_ms": safe_mean([float(row["latency_ms"]) for row in rows]),
        "mean_pred_count_per_image": safe_mean([float(row["pred_count"]) for row in rows]),
        "mean_gt_count_per_image": safe_mean([float(row["gt_count"]) for row in rows]),
    }


def main() -> None:
    args = parse_args()
    allowed_labels = set(args.labels)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    detector = YOLODetector(str(args.model))
    detector.model.conf = args.conf

    per_image_rows: list[dict[str, Any]] = []
    all_match_rows: list[dict[str, Any]] = []
    json_paths = sorted(args.annotated_dir.glob("*.json"))
    if not json_paths:
        raise FileNotFoundError(f"No LabelMe JSON files found in {args.annotated_dir}")

    for json_path in json_paths:
        image_path = find_image_for_annotation(json_path)
        if image_path is None:
            print(f"[skip] No image found for {json_path.name}")
            continue

        row, match_rows, annotations, predictions, matches = evaluate_image(
            detector=detector,
            image_path=image_path,
            json_path=json_path,
            allowed_labels=allowed_labels,
            iou_threshold=args.iou_threshold,
        )
        per_image_rows.append(row)
        all_match_rows.extend(match_rows)
        print(
            f"[eval] {image_path.name}: gt={row['gt_count']} pred={row['pred_count']} "
            f"matched={row['matched_count']} meanIoU={row['mean_match_iou']:.3f} "
            f"latency={row['latency_ms']:.1f}ms"
        )

        if args.save_overlays:
            draw_overlay(
                image_path=image_path,
                output_path=args.output_dir / "overlays" / image_path.name,
                annotations=annotations,
                predictions=predictions,
                matches=matches,
            )

    summary = summarize(per_image_rows, all_match_rows, args)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_csv(args.output_dir / "per_image.csv", per_image_rows)
    write_csv(args.output_dir / "matches.csv", all_match_rows)

    print("\nSummary")
    print(f"  Images: {summary['image_count']}")
    print(f"  Ground truth fish: {summary['gt_total']}")
    print(f"  Predicted masks: {summary['pred_mask_total']}")
    print(f"  Matched: {summary['matched_total']}")
    print(f"  Precision: {summary['precision']:.3f}")
    print(f"  Recall: {summary['recall']:.3f}")
    print(f"  F1: {summary['f1']:.3f}")
    print(f"  Mean matched IoU: {summary['mean_match_iou']:.3f}")
    print(f"  Mean latency: {summary['mean_latency_ms']:.1f}ms")
    print(f"  Report directory: {args.output_dir}")


if __name__ == "__main__":
    main()
