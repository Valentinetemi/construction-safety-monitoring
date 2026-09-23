from ultralytics import YOLO


class PersonDetector:
    def __init__(self, model_name="yolo11n.pt", confidence=0.5):
        self.model = YOLO(model_name)
        self.confidence = confidence

    def detect(self, frame):
        results = self.model(frame, verbose=False)[0]

        detections = []

        for box in results.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            # COCO class 0 = person
            if class_id != 0 or confidence < self.confidence:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            detections.append(
                {
                    "bbox": (x1, y1, x2, y2),
                    "confidence": confidence,
                }
            )

        return detections