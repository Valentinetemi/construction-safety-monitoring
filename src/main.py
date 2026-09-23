import cv2

from detector import PersonDetector


VIDEO_SOURCE = 0

HAZARD_ZONE = (300, 180, 620, 470)


def point_inside_zone(point, zone):
    px, py = point
    x1, y1, x2, y2 = zone

    return x1 <= px <= x2 and y1 <= py <= y2


def draw_hazard_zone(frame):
    x1, y1, x2, y2 = HAZARD_ZONE

    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        (0, 0, 255),
        2,
    )

    cv2.putText(
        frame,
        "HAZARD ZONE",
        (x1, y1 - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 0, 255),
        2,
    )


def main():
    detector = PersonDetector()

    cap = cv2.VideoCapture(VIDEO_SOURCE)

    if not cap.isOpened():
        print("Could not open video source.")
        return

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        draw_hazard_zone(frame)

        detections = detector.detect(frame)

        for detection in detections:
            x1, y1, x2, y2 = detection["bbox"]

            # Bottom center approximates where the person's feet are.
            foot_point = (
                int((x1 + x2) / 2),
                y2,
            )

            inside_zone = point_inside_zone(
                foot_point,
                HAZARD_ZONE,
            )

            if inside_zone:
                color = (0, 0, 255)
                label = "PERSON - HAZARD ZONE"
            else:
                color = (0, 255, 0)
                label = "PERSON - SAFE"

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                color,
                2,
            )

            cv2.circle(
                frame,
                foot_point,
                6,
                color,
                -1,
            )

            cv2.putText(
                frame,
                label,
                (x1, max(30, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
            )

        cv2.imshow(
            "Construction Safety Monitoring",
            frame,
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()