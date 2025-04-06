import { Alert, Config, ApiResponse } from "../types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const apiService = {
  async getConfig(): Promise<ApiResponse<Config>> {
    try {
      const response = await fetch(`${API_BASE_URL}/config`);
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      return { data };
    } catch (error) {
      console.error("Error fetching config:", error);
      return {
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  },

  async updateConfig(config: Config): Promise<ApiResponse<Config>> {
    try {
      const response = await fetch(`${API_BASE_URL}/config`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(config),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      return { data };
    } catch (error) {
      console.error("Error updating config:", error);
      return {
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  },

  async getAlerts(
    limit: number = 20,
    offset: number = 0
  ): Promise<
    ApiResponse<{
      alerts: Alert[];
      total: number;
      limit: number;
      offset: number;
    }>
  > {
    try {
      const response = await fetch(
        `${API_BASE_URL}/alerts?limit=${limit}&offset=${offset}`
      );
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      return { data };
    } catch (error) {
      console.error("Error fetching alerts:", error);
      return {
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  },

  async deleteAlert(
    alertId: string
  ): Promise<ApiResponse<{ message: string }>> {
    try {
      const response = await fetch(`${API_BASE_URL}/alerts/${alertId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      return { data };
    } catch (error) {
      console.error("Error deleting alert:", error);
      return {
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  },

  async clearAlerts(): Promise<ApiResponse<{ message: string }>> {
    try {
      const response = await fetch(`${API_BASE_URL}/alerts`, {
        method: "DELETE",
      });
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      return { data };
    } catch (error) {
      console.error("Error clearing alerts:", error);
      return {
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  },

  async changeCamera(
    source: string
  ): Promise<ApiResponse<{ message: string }>> {
    try {
      const response = await fetch(`${API_BASE_URL}/camera/${source}`, {
        method: "POST",
      });
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      return { data };
    } catch (error) {
      console.error("Error changing camera source:", error);
      return {
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  },

  async startProcessing(): Promise<ApiResponse<{ message: string }>> {
    try {
      const response = await fetch(`${API_BASE_URL}/start`, {
        method: "POST",
      });
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      return { data };
    } catch (error) {
      console.error("Error starting processing:", error);
      return {
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  },

  async stopProcessing(): Promise<ApiResponse<{ message: string }>> {
    try {
      const response = await fetch(`${API_BASE_URL}/stop`, {
        method: "POST",
      });
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      return { data };
    } catch (error) {
      console.error("Error stopping processing:", error);
      return {
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  },

  async updateZoneStatus(
    zoneName: string,
    active: boolean
  ): Promise<ApiResponse<Config>> {
    try {
      // First, get the current config
      const configResponse = await this.getConfig();
      if (configResponse.error || !configResponse.data) {
        throw new Error(
          configResponse.error || "Failed to get current configuration"
        );
      }

      const config = configResponse.data;

      // Update the specified zone's active status
      const updatedConfig: Config = {
        ...config,
        intrusion_zones: config.intrusion_zones.map((zone) =>
          zone.name === zoneName ? { ...zone, active } : zone
        ),
      };

      // Save the updated config
      return await this.updateConfig(updatedConfig);
    } catch (error) {
      console.error("Error updating zone status:", error);
      return {
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  },

  getStreamUrl(): string {
    return `${API_BASE_URL}/stream`;
  },

  getFrameUrl(): string {
    return `${API_BASE_URL}/frame`;
  },

  getFrameBase64Url(): string {
    return `${API_BASE_URL}/frame_base64`;
  },
};
