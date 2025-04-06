export interface Zone {
  points: number[][];
  name: string;
  active: boolean;
}

export interface Config {
  loitering_threshold: number;
  pacing_threshold: number;
  intrusion_zones: Zone[];
  zones_enabled: boolean;
  confidence_threshold: number;
  audio_alerts: boolean;
  camera_source: string;
  quiet_period_start: string;
  quiet_period_end: string;
  quiet_period_enabled: boolean;
}

export interface Alert {
  id: string;
  type: string;
  track_id: number;
  timestamp: number;
  location: number[];
  suspicion_score: number;
  duration?: number;
  direction_changes?: number;
  zone_id?: number;
  zone_name?: string;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
}
