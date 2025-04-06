"use client";

import { useState, useEffect } from "react";
import VideoFeed from "@/components/VideoFeed";
import AlertList from "@/components/AlertList";
import ConfigPanel from "@/components/ConfigPanel";
import Navbar from "@/components/Navbar";
import { Alert } from "../types";
import { apiService } from "../services/api";
import { getWebSocketService } from "@/services/websocket";

export default function Home() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [activeTab, setActiveTab] = useState<"feed" | "alerts" | "config">(
    "feed"
  );

  useEffect(() => {
    // Initial fetch of alerts
    const fetchAlerts = async () => {
      const response = await apiService.getAlerts();
      if (response.data) {
        setAlerts(response.data.alerts);
      }
    };

    fetchAlerts();

    // Set up WebSocket
    const wsService = getWebSocketService();

    wsService.setCallbacks({
      onConnect: () => setIsConnected(true),
      onDisconnect: () => setIsConnected(false),
      onNewAlert: (alert) => {
        setAlerts((prev) => [alert, ...prev]);
      },
      onError: (error) => {
        console.error("WebSocket error:", error);
      },
    });

    wsService.connect();

    // Cleanup on unmount
    return () => {
      wsService.disconnect();
    };
  }, []);

  const handleDeleteAlert = async (alertId: string) => {
    const response = await apiService.deleteAlert(alertId);
    if (response.data) {
      // Remove the alert from the state
      setAlerts((prev) => prev.filter((alert) => alert.id !== alertId));
    }
  };

  const handleClearAlerts = async () => {
    const response = await apiService.clearAlerts();
    if (response.data) {
      setAlerts([]);
    }
  };

  return (
    <main className='min-h-screen'>
      <Navbar
        isConnected={isConnected}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      <div className='container mx-auto px-4 py-8'>
        {activeTab === "feed" && (
          <div className='mb-8'>
            <h2 className='text-2xl font-bold mb-4'>Live Surveillance</h2>
            <VideoFeed />
          </div>
        )}

        {activeTab === "alerts" && (
          <div className='mb-8'>
            <h2 className='text-2xl font-bold mb-4'>Security Alerts</h2>
            <AlertList
              alerts={alerts}
              onDeleteAlert={handleDeleteAlert}
              onClearAlerts={handleClearAlerts}
            />
          </div>
        )}

        {activeTab === "config" && (
          <div className='mb-8'>
            <h2 className='text-2xl font-bold mb-4'>System Configuration</h2>
            <ConfigPanel />
          </div>
        )}
      </div>
    </main>
  );
}
