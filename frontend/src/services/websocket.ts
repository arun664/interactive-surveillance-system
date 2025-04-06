import { Alert, Config } from "../types";

type WebSocketCallbacks = {
  onNewAlert?: (alert: Alert) => void;
  onConfigUpdate?: (config: Config) => void;
  onCameraChange?: (source: string) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: string) => void;
};

export class WebSocketService {
  private socket: WebSocket | null = null;
  private callbacks: WebSocketCallbacks = {};
  private reconnectTimer: NodeJS.Timeout | null = null;
  private url: string;

  constructor(baseUrl: string) {
    this.url = `ws://${baseUrl.replace(/^https?:\/\//, "")}/ws`;
  }

  public connect(): void {
    if (this.socket) return;

    this.socket = new WebSocket(this.url);

    this.socket.onopen = () => {
      console.log("WebSocket connected");
      if (this.callbacks.onConnect) this.callbacks.onConnect();

      // Clear any reconnect timer
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Handle different message types
        if (data.new_alert && this.callbacks.onNewAlert) {
          this.callbacks.onNewAlert(data.new_alert);
        } else if (data.config_updated && this.callbacks.onConfigUpdate) {
          this.callbacks.onConfigUpdate(data.config_updated);
        } else if (data.camera_changed && this.callbacks.onCameraChange) {
          this.callbacks.onCameraChange(data.camera_changed);
        } else if (data.error && this.callbacks.onError) {
          this.callbacks.onError(data.error);
        }
      } catch (err) {
        console.error("Error parsing WebSocket message:", err);
      }
    };

    this.socket.onclose = () => {
      console.log("WebSocket disconnected");
      if (this.callbacks.onDisconnect) this.callbacks.onDisconnect();

      // Schedule reconnect
      this.socket = null;
      this.reconnectTimer = setTimeout(() => {
        this.connect();
      }, 5000);
    };

    this.socket.onerror = (error) => {
      console.error("WebSocket error:", error);
      if (this.callbacks.onError)
        this.callbacks.onError("WebSocket connection error");
    };
  }

  public disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  public sendMessage(message: unknown): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    } else {
      console.warn("Cannot send message, WebSocket is not connected");
    }
  }

  public updateConfig(config: Config): void {
    this.sendMessage({ config });
  }

  public setCallbacks(callbacks: WebSocketCallbacks): void {
    this.callbacks = callbacks;
  }

  public isConnected(): boolean {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }
}

// Create a singleton instance
let websocketService: WebSocketService | null = null;

export const getWebSocketService = (
  baseUrl: string = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
): WebSocketService => {
  if (!websocketService) {
    websocketService = new WebSocketService(baseUrl);
  }
  return websocketService;
};
