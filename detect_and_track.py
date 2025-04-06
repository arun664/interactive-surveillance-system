# Install with pip (no C++ compilation needed)
# pip install supervision

from ultralytics import YOLO
import supervision as sv
import cv2
import numpy as np
import time
from deep_sort_realtime.deepsort_tracker import DeepSort
import json
from collections import defaultdict
from playsound import playsound
import threading
import os
from gtts import gTTS
import requests

# Alert log
alert_log = []

# Create a tracker that doesn't require C++ compilation
tracker = sv.ByteTrack()  # or sv.NorfairTracker()

class SecurityAnalyzer:
    def __init__(self, config=None):
        # Default configuration
        self.config = {
            "loitering_threshold": 10,  # seconds
            "pacing_threshold": 3,      # direction changes
            "intrusion_zones": [
                # Predefined zone with name and active status
                {
                    "points": [(100, 100), (400, 100), (400, 400), (100, 400)],
                    "name": "Default Zone",
                    "active": True
                }
            ],
            "zones_enabled": True,      # Toggle to enable/disable all zone detection
            "confidence_threshold": 0.5, # Detection confidence threshold
            "audio_alerts": True,       # Enable audio alerts
            "quiet_period_start": "22:00",  # Start quiet period (24-hour format)
            "quiet_period_end": "06:00",    # End quiet period (24-hour format)
            "quiet_period_enabled": False,  # Enable/disable quiet period
        }

        # Update with provided config
        if config:
            self.config.update(config)

        # Load YOLOv8 model once
        self.model = YOLO('yolov8n.pt')

        # Track data
        self.tracks = {}
        self.alerts = []
        self.last_alert_time = {}  # Prevent alert spam
        self.suspicion_scores = defaultdict(float)  # Track suspicion by ID

    def process_frame(self, frame):
        """Process a single frame for detection, tracking and analysis"""
        # Run YOLOv8 with tracking
        results = self.model.track(
            source=frame,
            persist=True,  # Remember tracks between frames
            classes=[0],   # Only track people (class 0)
            conf=self.config["confidence_threshold"]
        )

        # Store alerts generated in this frame
        frame_alerts = []

        if results and len(results) > 0:
            # Get tracked detections
            boxes = results[0].boxes

            # If we have valid tracking IDs
            if hasattr(boxes, 'id') and boxes.id is not None:
                current_time = time.time()

                # Process each tracked detection
                for i, box in enumerate(boxes):
                    if box.id is None:
                        continue

                    # Get track ID and position
                    track_id = int(box.id.item())
                    xyxy = box.xyxy[0].tolist()  # Get box in [x1,y1,x2,y2] format

                    # Calculate center point
                    x_center = (xyxy[0] + xyxy[2]) / 2
                    y_center = (xyxy[1] + xyxy[3]) / 2

                    # Initialize or update track
                    if track_id not in self.tracks:
                        self.tracks[track_id] = {
                            'positions': [(x_center, y_center)],
                            'timestamps': [current_time],
                            'last_direction': None,
                            'direction_changes': 0
                        }
                        self.suspicion_scores[track_id] = 0.0
                    else:
                        track = self.tracks[track_id]

                        # Update position and time
                        track['positions'].append((x_center, y_center))
                        track['timestamps'].append(current_time)

                        # Limit history for memory efficiency
                        if len(track['positions']) > 100:
                            track['positions'] = track['positions'][-100:]
                            track['timestamps'] = track['timestamps'][-100:]

                        # Calculate direction for pacing detection
                        if len(track['positions']) >= 2:
                            prev_x = track['positions'][-2][0]
                            curr_direction = "right" if x_center > prev_x + 5 else "left" if x_center < prev_x - 5 else track['last_direction']

                            if track['last_direction'] is not None and curr_direction != track['last_direction']:
                                track['direction_changes'] += 1

                            track['last_direction'] = curr_direction

                    # Run behavior analysis - get any alerts
                    alerts = self.analyze_behaviors(track_id, current_time)
                    frame_alerts.extend(alerts)

                # Decay suspicion scores slightly over time
                for track_id in list(self.suspicion_scores.keys()):
                    self.suspicion_scores[track_id] *= 0.99

                # Annotate frame with tracking info and alerts
                annotated_frame = self.annotate_frame(frame, results[0], frame_alerts)
                return annotated_frame, frame_alerts

        return frame, frame_alerts

    def send_telegram_alert(self, alert_data):
        try:
            bot_token = '7652787142:AAG8S_ayLwYCAUNCxwwrePJ9m5x2rbHqQBE'
            chat_id = '938547627'

        # System/Camera name
            system_name = "🛡️ Hackathon Security Bot"

            alert_type = alert_data.get("type", "unknown").upper()
            track_id = alert_data.get("track_id", "N/A")
            suspicion_score = alert_data.get("suspicion_score", 0.0)
            location = alert_data.get("location", (0, 0))
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert_data.get("timestamp", time.time())))
            zone_id = alert_data.get("zone_id", None)
            behaviors = alert_data.get("behaviors", [])

        # Compose message
            message = f"{system_name}\n\n"
            message += f"🚨 *{alert_type} Detected!*\n"
            message += f"🆔 Track ID: `{track_id}`\n"
            message += f"📍 Location: `{location}`\n"
            if zone_id is not None:
                message += f"🗺️ Zone ID: `{zone_id}`\n"
            if behaviors:
                message += f"🧠 Behaviors: {', '.join(behaviors)}\n"
            message += f"📈 Suspicion Score: `{suspicion_score:.1f}`\n"
            message += f"🕒 Time: {timestamp}"

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }

            response = requests.post(url, data=payload)
            if response.status_code != 200:
                print("Telegram alert failed:", response.text)

        except Exception as e:
            print(f"Telegram alert error: {e}")

    def is_quiet_period(self):
        """Check if current time is in the configured quiet period"""
        if not self.config.get("quiet_period_enabled", False):
            return False

        start_str = self.config.get("quiet_period_start", "22:00")
        end_str = self.config.get("quiet_period_end", "06:00")

        # Parse time strings
        try:
            from datetime import datetime, time
            now = datetime.now().time()
            start_hours, start_minutes = map(int, start_str.split(":"))
            end_hours, end_minutes = map(int, end_str.split(":"))

            start_time = time(start_hours, start_minutes)
            end_time = time(end_hours, end_minutes)

            # Handle overnight periods (e.g., 22:00 to 06:00)
            if start_time > end_time:
                return now >= start_time or now <= end_time
            else:
                return start_time <= now <= end_time
        except Exception as e:
            print(f"Error checking quiet period: {e}")
            return False

    def analyze_behaviors(self, track_id, current_time):
        """Analyze tracked person for suspicious behaviors"""
        track = self.tracks[track_id]
        alerts = []
        behaviors_detected = []

        # Check if in quiet period - suppress all alerts
        if self.is_quiet_period():
            return alerts

        # Avoid alert spam - don't alert on same ID within 10 seconds
        if track_id in self.last_alert_time and current_time - self.last_alert_time[track_id] < 10:
            return alerts

        # Check for loitering
        loitering_detected = False
        if len(track['timestamps']) > 5:
            duration = track['timestamps'][-1] - track['timestamps'][0]
            if duration > self.config['loitering_threshold']:
                # Check if movement is minimal
                recent_positions = np.array(track['positions'][-10:])
                if len(recent_positions) >= 2:
                    x_var = np.var([p[0] for p in recent_positions])
                    y_var = np.var([p[1] for p in recent_positions])

                    # If variance is low in both x and y, person is relatively stationary
                    if x_var < 500 and y_var < 500:  # Adjust thresholds based on your camera
                        loitering_detected = True
                        behaviors_detected.append("loitering")
                        # Increase suspicion score
                        self.suspicion_scores[track_id] += 2.0

                        alert_data = {
                            "type": "loitering",
                            "track_id": track_id,
                            "timestamp": current_time,
                            "location": track['positions'][-1],
                            "duration": duration,
                            "suspicion_score": self.suspicion_scores[track_id]
                        }
                        alerts.append(alert_data)
                        self.send_telegram_alert(alert_data)

        # Check for pacing
        pacing_detected = False
        if track['direction_changes'] >= self.config['pacing_threshold']:
            pacing_detected = True
            behaviors_detected.append("pacing")
            # Increase suspicion score
            self.suspicion_scores[track_id] += 1.5

            alert_data = {
                "type": "pacing",
                "track_id": track_id,
                "timestamp": current_time,
                "location": track['positions'][-1],
                "direction_changes": track['direction_changes'],
                "suspicion_score": self.suspicion_scores[track_id]
            }
            alerts.append(alert_data)
            track['direction_changes'] = 0  # Reset counter

        # Check for zone intrusion
        if self.config['zones_enabled'] and len(self.config['intrusion_zones']) > 0:
            current_point = track['positions'][-1]

            for zone_idx, zone in enumerate(self.config['intrusion_zones']):
                # Skip inactive zones
                if not zone.get('active', True):
                    continue

                # Convert zone format if necessary (handle both old and new formats)
                zone_points = zone['points'] if isinstance(zone, dict) else zone

                if self.point_in_polygon(current_point, zone_points):
                    behaviors_detected.append("zone_intrusion")
                    # Increase suspicion score
                    self.suspicion_scores[track_id] += 3.0

                    # Get zone name
                    zone_name = zone.get('name', f"Zone {zone_idx+1}") if isinstance(zone, dict) else f"Zone {zone_idx+1}"

                    alert_data = {
                        "type": "zone_intrusion",
                        "track_id": track_id,
                        "timestamp": current_time,
                        "location": current_point,
                        "suspicion_score": self.suspicion_scores[track_id],
                        "zone_id": zone_idx,
                        "zone_name": zone_name
                    }
                    alerts.append(alert_data)
                    break  # Only report the first zone intrusion

        # Check for high risk combination of behaviors
        if len(behaviors_detected) > 1 or self.suspicion_scores[track_id] >= 5.0:
            # Create high risk alert
            alert_data = {
                "type": "high_risk",
                "track_id": track_id,
                "timestamp": current_time,
                "location": track['positions'][-1],
                "behaviors": behaviors_detected,
                "suspicion_score": self.suspicion_scores[track_id]
            }
            alerts.append(alert_data)

            # Play high risk sound alert
            if self.config["audio_alerts"]:
                self.play_audio_alert("high_risk")
        elif alerts and self.config["audio_alerts"]:
            # Play individual behavior alert
            self.play_audio_alert(alerts[0]["type"])

        # If any alerts were generated, update last alert time
        if alerts:
            self.last_alert_time[track_id] = current_time
            self.alerts.extend(alerts)

        return alerts

    def play_audio_alert(self, alert_type):
        """Play MP3 audio alert with multiple fallback methods"""
        # Use MP3 files directly
        sound_file = f"sounds/{alert_type}_alert.mp3"

        if not os.path.exists(sound_file):
            print(f"Warning: Sound file {sound_file} not found")
            return

        print(f"Playing alert sound: {alert_type}")

        try:
            def play_with_playsound(sound_path):
                from playsound import playsound
                playsound(sound_path)

            threading.Thread(target=play_with_playsound, args=(sound_file,), daemon=True).start()
            return
        except Exception as e:
            print(f"playsound failed: {e}")

        # System command (most compatible)
        try:
            if os.name == 'nt':  # Windows
                os.system(f'start "" "{sound_file}"')
            elif os.name == 'posix':  # macOS/Linux
                if os.path.exists('/usr/bin/afplay'):  # macOS
                    os.system(f'afplay "{sound_file}" &')
                else:  # Linux
                    os.system(f'mpg123 "{sound_file}" &')
            return
        except Exception as e:
            print(f"System command failed: {e}")

        print("All audio playback methods failed")

    def point_in_polygon(self, point, polygon):
        """Check if a point is inside a polygon"""
        x, y = point
        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def annotate_frame(self, frame, result, alerts):
        """Draw tracking info and alerts on frame"""
        # Draw detection boxes and tracking IDs
        annotated_frame = result.plot()

        # Draw alert info
        for alert in alerts:
            alert_type = alert["type"]
            location = alert["location"]
            track_id = alert["track_id"]
            suspicion_score = alert.get("suspicion_score", 0)

            # Convert to pixel coordinates
            x, y = int(location[0]), int(location[1])

            # Set color based on suspicion score
            if suspicion_score >= 5.0:
                color = (0, 0, 255)  # Red for high suspicion
            elif suspicion_score >= 3.0:
                color = (0, 165, 255)  # Orange for medium suspicion
            else:
                color = (0, 255, 255)  # Yellow for low suspicion

            # Draw alert indicator
            cv2.circle(annotated_frame, (x, y), 20, color, -1)
            cv2.putText(
                annotated_frame,
                f"{alert_type.upper()}: ID {track_id} ({suspicion_score:.1f})",
                (x - 10, y - 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
            )

        # Draw active intrusion zones
        if self.config['zones_enabled']:
            for i, zone in enumerate(self.config['intrusion_zones']):
                # Skip inactive zones
                if isinstance(zone, dict) and not zone.get('active', True):
                    continue

                # Convert zone format if necessary
                zone_points = zone['points'] if isinstance(zone, dict) else zone

                # Convert to numpy array for drawing
                if len(zone_points) > 2:  # Need at least 3 points to form a polygon
                    points = np.array(zone_points, dtype=np.int32)

                    # Get zone name
                    zone_name = zone.get('name', f"Zone {i+1}") if isinstance(zone, dict) else f"Zone {i+1}"

                    # Draw zone polygon
                    cv2.polylines(annotated_frame, [points], True, (0, 255, 0), 2)
                    # Add zone label at the top-left corner of the zone
                    cv2.putText(
                        annotated_frame,
                        zone_name,
                        (points[0][0], points[0][1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        1
                    )

        # Indicate quiet period if active
        if self.is_quiet_period():
            cv2.putText(
                annotated_frame,
                "QUIET PERIOD ACTIVE - ALERTS SUPPRESSED",
                (10, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
            )

        # Draw suspicion scores for all tracked objects
        y_offset = 30
        cv2.putText(
            annotated_frame,
            "Suspicion Scores:",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
        )

        for track_id, score in sorted(
            self.suspicion_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]:  # Show top 5 scores
            y_offset += 25
            cv2.putText(
                annotated_frame,
                f"ID {track_id}: {score:.1f}",
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (0, 0, 255) if score >= 5.0 else
                (0, 165, 255) if score >= 3.0 else
                (0, 255, 255),
                2
            )

        return annotated_frame

    def get_recent_alerts(self, limit=10):
        """Get the most recent alerts"""
        return self.alerts[-limit:]

    def update_config(self, new_config):
        """Update the analyzer configuration"""
        self.config.update(new_config)
        return self.config

# Function to run detection on video
def run_security_analyzer(video_source=0, output_file=None, config=None):
    """Run the security analyzer on a video source"""
    analyzer = SecurityAnalyzer(config)
    cap = cv2.VideoCapture(video_source)

    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Setup output writer if needed
    writer = None
    if output_file:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

    # Process video frames
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # Process frame
        processed_frame, alerts = analyzer.process_frame(frame)

        # Display real-time alerts
        if alerts:
            for alert in alerts:
                print(f"ALERT: {alert['type']} detected for ID {alert['track_id']} (Suspicion: {alert.get('suspicion_score', 0):.1f})")

        # Write frame to output if needed
        if writer:
            writer.write(processed_frame)

        # Display the frame
        cv2.imshow('Security Monitor', processed_frame)

        # Break on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Cleanup
    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()

    return analyzer.get_recent_alerts()

# Example usage when script is run directly
if __name__ == "__main__":
    # Ensure sounds directory exists
    os.makedirs("sounds", exist_ok=True)

    # Example configuration
    config = {
        "loitering_threshold": 5,
        "pacing_threshold": 4,
        "intrusion_zones": [
            [(100, 100), (300, 100), (300, 300), (100, 300)]  # Example zone
        ],
        "zones_enabled": True,
        "confidence_threshold": 0.4,
        "audio_alerts": True,
        "quiet_period_start": "22:00",
        "quiet_period_end": "06:00",
        "quiet_period_enabled": False,
    }

    # Create alert sounds using text-to-speech
    alerts = {
        "loitering": "Warning! Loitering detected.",
        "pacing": "Warning! Suspicious pacing behavior detected.",
        "zone_intrusion": "Alert! Intrusion into restricted zone.",
        "high_risk": "High risk behavior detected! Security response required."
    }

    for alert_type, text in alerts.items():
        tts = gTTS(text=text, lang='en')
        tts.save(f"sounds/{alert_type}_alert.mp3")

    # Run the analyzer
    alerts = run_security_analyzer(
        video_source=0,  # Use webcam
        output_file="security_footage.mp4",  # Save output
        config=config
    )

    # Display all alerts that were generated
    print(f"Generated {len(alerts)} alerts:")
    for alert in alerts:
        print(alert)

    # Load YOLOv8 model
    model = YOLO("yolov8n.pt")

    # Open video stream
    cap = cv2.VideoCapture(0)

    # Simple detection loop
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Run YOLOv8 detection
        results = model(frame)

        # Filter for 'person' class (class id = 0)
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                if cls == 0:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])

                    # Draw box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"Person {conf:.2f}", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Show result
        cv2.imshow("Security Feed", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
