from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import cv2
import asyncio
import json
import time
import os
import threading
import numpy as np
from typing import List, Dict, Optional, Any
import base64
from pydantic import BaseModel
import uuid

# Import SecurityAnalyzer with proper error handling
try:
    from detect_and_track import SecurityAnalyzer
    USE_REAL_ANALYZER = True
    print("Successfully imported SecurityAnalyzer")
except Exception as e:
    print(f"Error importing SecurityAnalyzer: {e}")
    USE_REAL_ANALYZER = False

    # Creating a dummy SecurityAnalyzer for testing
    class SecurityAnalyzer:
        def __init__(self, config):
            self.config = config
            print("Dummy SecurityAnalyzer initialized")

        def update_config(self, config):
            self.config = config
            print("Dummy SecurityAnalyzer config updated")

        def process_frame(self, frame):
            # Just return the original frame and no alerts
            return frame, []

# Define data models
class Alert(BaseModel):
    id: str
    type: str
    track_id: int
    timestamp: float
    location: List[float]
    suspicion_score: float = 0.0
    duration: Optional[float] = None
    direction_changes: Optional[int] = None
    zone_id: Optional[int] = None
    zone_name: Optional[str] = None

class Zone(BaseModel):
    points: List[List[float]]
    name: str
    active: bool = True

class Config(BaseModel):
    loitering_threshold: float = 10.0
    pacing_threshold: int = 3
    intrusion_zones: List[Zone] = []
    zones_enabled: bool = True
    confidence_threshold: float = 0.5
    audio_alerts: bool = True
    camera_source: str = "0"  # Can be a number (webcam) or path to video file
    quiet_period_start: str = "22:00"  # Start quiet period (24-hour format)
    quiet_period_end: str = "06:00"    # End quiet period (24-hour format)
    quiet_period_enabled: bool = False  # Enable/disable quiet period

# Create FastAPI app
app = FastAPI(title="AI Security Guard API")

# Add CORS middleware to allow cross-origin requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a directory for saved alert clips
os.makedirs("alert_clips", exist_ok=True)

# Create a shared state for the app
class AppState:
    def __init__(self):
        self.analyzer = None
        self.camera = None
        self.active_connections: List[WebSocket] = []
        self.alerts: List[Alert] = []
        self.current_frame = None
        self.processing_active = False
        self.config = Config().dict()
        self.video_thread = None

app_state = AppState()

# Register a new WebSocket connection
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    app_state.active_connections.append(websocket)
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            try:
                message = json.loads(data)

                # Handle config updates
                if "config" in message:
                    app_state.config.update(message["config"])
                    if app_state.analyzer:
                        app_state.analyzer.update_config(app_state.config)

                    # Broadcast config update to all clients
                    await broadcast_message({"config_updated": app_state.config})

                # Handle camera source change
                if "camera_source" in message:
                    await restart_camera(message["camera_source"])

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        app_state.active_connections.remove(websocket)

# Broadcast message to all connected clients
async def broadcast_message(message):
    for connection in app_state.active_connections:
        try:
            await connection.send_json(message)
        except:
            # Remove disconnected clients
            try:
                app_state.active_connections.remove(connection)
            except:
                pass

# Broadcast new alert to all connected clients
async def broadcast_alert(alert: Alert):
    await broadcast_message({"new_alert": alert.dict()})

# Initialize or restart the camera
async def restart_camera(source):
    source_val = source
    try:
        # If source is a string but represents a number, convert to int
        if isinstance(source, str) and source.isdigit():
            source_val = int(source)
    except:
        pass

    # Stop existing processing
    if app_state.processing_active:
        app_state.processing_active = False
        if app_state.camera:
            app_state.camera.release()
        if app_state.video_thread and app_state.video_thread.is_alive():
            app_state.video_thread.join(timeout=1.0)

    # Update config
    app_state.config["camera_source"] = source

    # Start new camera
    app_state.camera = cv2.VideoCapture(source_val)
    if not app_state.camera.isOpened():
        await broadcast_message({"error": f"Failed to open camera source: {source}"})
        return False

    # Create or update analyzer
    try:
        if not app_state.analyzer:
            app_state.analyzer = SecurityAnalyzer(app_state.config)
        else:
            app_state.analyzer.update_config(app_state.config)
    except Exception as e:
        await broadcast_message({"error": f"Failed to initialize SecurityAnalyzer: {e}"})
        app_state.analyzer = SecurityAnalyzer(app_state.config) if not USE_REAL_ANALYZER else None
        return False

    # Start processing thread
    app_state.processing_active = True
    app_state.video_thread = threading.Thread(
        target=process_video_frames,
        daemon=True
    )
    app_state.video_thread.start()

    await broadcast_message({"camera_changed": source})
    return True

# Function to process video frames (runs in a separate thread)
def process_video_frames():
    while app_state.processing_active:
        if app_state.camera is None:
            time.sleep(0.1)
            continue

        success, frame = app_state.camera.read()
        if not success:
            # Try to restart camera after a brief pause
            time.sleep(1.0)
            app_state.camera = cv2.VideoCapture(app_state.config["camera_source"])
            continue

        # Process frame with analyzer
        try:
            if app_state.analyzer:
                processed_frame, new_alerts = app_state.analyzer.process_frame(frame)

                # Update current frame for streaming
                app_state.current_frame = processed_frame

                # Handle new alerts
                if new_alerts:
                    for alert_data in new_alerts:
                        # Generate unique ID
                        alert_id = str(uuid.uuid4())

                        # Add ID to alert data
                        alert_data["id"] = alert_id

                        # Create Alert object
                        alert = Alert(**alert_data)

                        # Add to alert list
                        app_state.alerts.append(alert)

                        # Broadcast alert to all clients
                        asyncio.run(broadcast_alert(alert))
            else:
                app_state.current_frame = frame
        except Exception as e:
            print(f"Error processing frame: {e}")
            app_state.current_frame = frame

        # Brief sleep to prevent CPU overload
        time.sleep(0.01)

# Generate frames for video streaming
def generate_frames():
    while app_state.processing_active:
        if app_state.current_frame is not None:
            # Convert frame to JPEG
            ret, buffer = cv2.imencode('.jpg', app_state.current_frame)
            frame = buffer.tobytes()

            # Yield the frame in the format expected by a multipart response
            yield (b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        # Brief sleep to control frame rate
        time.sleep(0.033)  # ~30 FPS

# API routes

@app.get("/")
async def root():
    return {"message": "AI Security Guard API is running"}

@app.get("/stream")
async def video_feed():
    """Stream video feed from the camera"""
    if not app_state.processing_active:
        await restart_camera(app_state.config["camera_source"])

    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/frame")
async def get_current_frame():
    """Get the current frame as a JPEG image"""
    if app_state.current_frame is None:
        raise HTTPException(status_code=404, detail="No frame available")

    # Convert frame to JPEG
    ret, buffer = cv2.imencode('.jpg', app_state.current_frame)
    frame_bytes = buffer.tobytes()

    return Response(content=frame_bytes, media_type="image/jpeg")

@app.get("/frame_base64")
async def get_frame_base64():
    """Get the current frame as a base64 encoded JPEG"""
    if app_state.current_frame is None:
        raise HTTPException(status_code=404, detail="No frame available")

    # Convert frame to JPEG
    ret, buffer = cv2.imencode('.jpg', app_state.current_frame)
    frame_bytes = buffer.tobytes()

    # Convert to base64
    base64_frame = base64.b64encode(frame_bytes).decode('utf-8')

    return {"frame": f"data:image/jpeg;base64,{base64_frame}"}

@app.get("/config")
async def get_config():
    """Get the current configuration"""
    return app_state.config

@app.post("/config")
async def update_config(config: Config):
    """Update the configuration"""
    app_state.config = config.dict()
    if app_state.analyzer:
        app_state.analyzer.update_config(app_state.config)

    return app_state.config

@app.post("/camera/{source}")
async def change_camera(source: str):
    """Change the camera source"""
    success = await restart_camera(source)
    if success:
        return {"message": f"Camera changed to {source}"}
    else:
        raise HTTPException(status_code=400, detail=f"Failed to change camera to {source}")

@app.get("/alerts")
async def get_alerts(limit: int = 20, offset: int = 0):
    """Get alerts with pagination"""
    total = len(app_state.alerts)
    alerts = app_state.alerts[offset:offset+limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "alerts": [alert.dict() for alert in alerts]
    }

@app.get("/alerts/{alert_id}")
async def get_alert(alert_id: str):
    """Get a specific alert by ID"""
    for alert in app_state.alerts:
        if alert.id == alert_id:
            return alert

    raise HTTPException(status_code=404, detail=f"Alert with ID {alert_id} not found")

@app.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str):
    """Delete a specific alert"""
    for i, alert in enumerate(app_state.alerts):
        if alert.id == alert_id:
            del app_state.alerts[i]
            return {"message": f"Alert {alert_id} deleted"}

    raise HTTPException(status_code=404, detail=f"Alert with ID {alert_id} not found")

@app.delete("/alerts")
async def clear_alerts():
    """Clear all alerts"""
    app_state.alerts = []
    return {"message": "All alerts cleared"}

@app.post("/start")
async def start_processing():
    """Start video processing"""
    if app_state.processing_active:
        return {"message": "Processing already active"}

    success = await restart_camera(app_state.config["camera_source"])
    if success:
        return {"message": "Processing started"}
    else:
        raise HTTPException(status_code=500, detail="Failed to start processing")

@app.post("/stop")
async def stop_processing():
    """Stop video processing"""
    if not app_state.processing_active:
        return {"message": "Processing already stopped"}

    app_state.processing_active = False
    if app_state.camera:
        app_state.camera.release()
        app_state.camera = None

    if app_state.video_thread and app_state.video_thread.is_alive():
        app_state.video_thread.join(timeout=1.0)

    return {"message": "Processing stopped"}

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    # Start with default camera
    await restart_camera(app_state.config["camera_source"])

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    app_state.processing_active = False
    if app_state.camera:
        app_state.camera.release()

    if app_state.video_thread and app_state.video_thread.is_alive():
        app_state.video_thread.join(timeout=1.0)

# Serve static files (e.g., saved clips)
app.mount("/clips", StaticFiles(directory="alert_clips"), name="clips")

# Run the API server
if __name__ == "__main__":
    print("Starting AI Security Guard API...")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)