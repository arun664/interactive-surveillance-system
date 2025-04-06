import cv2
from ultralytics import YOLO
import threading
import time
from datetime import datetime


model = YOLO("yolov8n.pt")

video_source = 0
latest_detections = {}
is_running = False
lock = threading.Lock() 

# Divide the frame into spatial zones
ZONE_LEFT = "left"
ZONE_CENTER = "center"
ZONE_RIGHT = "right"

def capture_snapshot(file_path="frame_snapshots/latest.jpg"):
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(file_path, frame)
    cap.release()
    return file_path if ret else None


def get_position(x, width):
    if x < width / 3:
        return ZONE_LEFT
    elif x > 2 * width / 3:
        return ZONE_RIGHT
    else:
        return ZONE_CENTER

def _detection_loop():
    global is_running, latest_detections
    cap = cv2.VideoCapture(video_source, cv2.CAP_DSHOW)
    is_running = True
    frame_count = 0  # Add this above the loop

    while is_running:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)
        labels = results[0].names
        boxes = results[0].boxes.data.tolist()

        frame_objects = []
        frame_actions = []

        height, width = frame.shape[:2]

        for box in boxes:
            x1, y1, x2, y2, conf, cls_id = box
            cls_id = int(cls_id)
            label = labels[cls_id]
            frame_objects.append(label)

            cx = (x1 + x2) / 2
            position = get_position(cx, width)

            if label == "person":
                if (y2 - y1) < height / 4:
                    action = f"person is sitting in the {position}"
                else:
                    action = f"person is standing in the {position}"
                frame_actions.append(action)

            # Draw labels
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            cv2.putText(frame, f"{label} - {position}", (int(x1), int(y1) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Save detections safely
        with lock:
            latest_detections = {
                "objects": frame_objects,
                "actions": frame_actions
            }

            frame_count += 1
            if frame_count % 30 == 0:  # Save every ~30 frames (~1s at 30fps)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_path = f"frame_snapshots/frame_{timestamp}.jpg"
                cv2.imwrite(image_path, frame)

                # Log event
                log_detection_event(latest_detections, image_path)

        # Show video
        cv2.imshow("Live Detection", frame)
        if cv2.waitKey(25) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    is_running = False

def start_detection_loop():
    global is_running
    if is_running:
        stop_detection_loop()
        time.sleep(1)
    thread = threading.Thread(target=_detection_loop)
    thread.start()

def stop_detection_loop():
    global is_running
    is_running = False

def get_latest_detections():
    with lock:
        return latest_detections

def summarize_scene():
    with lock:
        data = latest_detections.copy()

    people = {
        "sitting": {"left": 0, "center": 0, "right": 0},
        "standing": {"left": 0, "center": 0, "right": 0}
    }
    objects = {}

    for action in data.get("actions", []):
        if "person is sitting" in action:
            if "left" in action:
                people["sitting"]["left"] += 1
            elif "center" in action:
                people["sitting"]["center"] += 1
            elif "right" in action:
                people["sitting"]["right"] += 1
        elif "person is standing" in action:
            if "left" in action:
                people["standing"]["left"] += 1
            elif "center" in action:
                people["standing"]["center"] += 1
            elif "right" in action:
                people["standing"]["right"] += 1

    for obj in data.get("objects", []):
        if obj not in ["person"]:
            objects[obj] = objects.get(obj, 0) + 1

    desc = []

    for pose in ["sitting", "standing"]:
        for zone in ["left", "center", "right"]:
            count = people[pose][zone]
            if count > 0:
                desc.append(f"{count} person{'s' if count > 1 else ''} {pose} in the {zone}")

    for obj, count in objects.items():
        desc.append(f"{count} {obj}{'s' if count > 1 else ''}")

    if not desc:
        return "No significant activity detected."

    return "Scene Summary: " + ", ".join(desc) + "."
