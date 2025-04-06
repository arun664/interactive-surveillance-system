"use client";
import { useState, useEffect } from "react";
import { apiService } from "../services/api";
import { Config, Zone } from "../types";

const VideoFeed: React.FC = () => {
  const [useBase64, setUseBase64] = useState(false);
  const [base64Frame, setBase64Frame] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [cameraSource, setCameraSource] = useState("0");
  const [config, setConfig] = useState<Config | null>(null);
  const [selectedZone, setSelectedZone] = useState<string | null>(null);

  // Fetch base64 frame for browsers that don't support streaming response
  const fetchBase64Frame = async () => {
    try {
      const response = await fetch(apiService.getFrameBase64Url());
      if (!response.ok) throw new Error("Failed to fetch frame");

      const data = await response.json();
      setBase64Frame(data.frame);
      setIsLoading(false);

      // Request next frame
      setTimeout(fetchBase64Frame, 100);
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
    } catch (_error) {
      // Suppress the error detail, just log the error message
      setError("Error loading video feed");
      setIsLoading(false);

      // Attempt to reconnect after a delay
      setTimeout(fetchBase64Frame, 5000);
    }
  };

  // Fetch configuration
  const fetchConfig = async () => {
    try {
      const response = await apiService.getConfig();
      if (response.data) {
        setConfig(response.data);
        // Set first active zone as selected if none is selected
        if (!selectedZone && response.data.intrusion_zones) {
          const activeZones = response.data.intrusion_zones.filter(
            (z) => z.active
          );
          if (activeZones.length > 0) {
            setSelectedZone(activeZones[0].name);
          }
        }
      }
    } catch (error) {
      console.error("Error fetching config:", error);
    }
  };

  useEffect(() => {
    // Try the streaming approach first, but have base64 as fallback
    const img = new Image();
    img.onerror = () => {
      setUseBase64(true);
      fetchBase64Frame();
    };
    img.src = apiService.getStreamUrl();

    // Start processing if not already started
    apiService.startProcessing();

    // Fetch configuration
    fetchConfig();

    // Set up a periodic config check to get updates
    const configInterval = setInterval(fetchConfig, 5000);

    return () => {
      // Clean up any pending requests
      clearInterval(configInterval);
    };
  }, []);

  const handleCameraChange = async () => {
    const newSource = window.prompt(
      "Enter camera source (number for webcam or path to video file):",
      cameraSource
    );
    if (newSource !== null) {
      setIsLoading(true);
      const response = await apiService.changeCamera(newSource);
      if (response.error) {
        setError(response.error);
      } else {
        setCameraSource(newSource);
        setError("");
      }
      setIsLoading(false);
    }
  };

  const handleZoneChange = async (zoneName: string) => {
    if (!config || !zoneName) return;

    setSelectedZone(zoneName);

    // First deactivate all zones
    for (const zone of config.intrusion_zones) {
      if (zone.active) {
        await apiService.updateZoneStatus(zone.name, false);
      }
    }

    // Then activate just the selected zone
    await apiService.updateZoneStatus(zoneName, true);

    // Refresh the config
    fetchConfig();
  };

  const toggleAllZones = async (active: boolean) => {
    if (!config) return;

    // Activate/deactivate each zone individually
    for (const zone of config.intrusion_zones) {
      await apiService.updateZoneStatus(zone.name, active);
    }

    // If activating all zones, don't select any specific one
    if (active) {
      setSelectedZone(null);
    }

    // Refresh the config
    fetchConfig();
  };

  return (
    <div className='relative bg-black rounded-lg overflow-hidden'>
      {isLoading && (
        <div className='absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 z-10'>
          <div className='loader animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-white'></div>
        </div>
      )}

      {error && (
        <div className='absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 z-10'>
          <div className='text-white bg-red-600 px-4 py-2 rounded'>{error}</div>
        </div>
      )}

      <div className='aspect-video w-full'>
        {useBase64 ? (
          <img
            src={base64Frame}
            alt='Security camera feed'
            className='w-full h-full object-contain max-w-full max-h-screen'
          />
        ) : (
          <img
            src={apiService.getStreamUrl()}
            alt='Security camera feed'
            className='w-full h-full object-contain max-w-full max-h-screen'
          />
        )}
      </div>

      {/* Zone Controls Overlay */}
      <div className='absolute top-4 left-4 z-20'>
        <div className='bg-black bg-opacity-70 text-white p-3 rounded shadow-lg'>
          <h3 className='text-sm font-semibold mb-2'>Surveillance Zones</h3>

          {/* Zone dropdown */}
          {config && config.intrusion_zones.length > 0 ? (
            <div className='space-y-2'>
              <select
                value={selectedZone || ""}
                onChange={(e) => handleZoneChange(e.target.value)}
                className='w-full px-2 py-1 text-sm bg-gray-800 border border-gray-700 rounded text-white'
              >
                <option value=''>Select a zone</option>
                {config.intrusion_zones.map((zone: Zone, index: number) => (
                  <option key={index} value={zone.name}>
                    {zone.name} {zone.active ? "(Active)" : ""}
                  </option>
                ))}
              </select>

              <div className='flex gap-2'>
                <button
                  onClick={() => toggleAllZones(true)}
                  className='bg-green-600 hover:bg-green-700 text-white text-xs py-1 px-2 rounded'
                >
                  Activate All
                </button>
                <button
                  onClick={() => toggleAllZones(false)}
                  className='bg-red-600 hover:bg-red-700 text-white text-xs py-1 px-2 rounded'
                >
                  Deactivate All
                </button>
              </div>

              {/* Currently active zones */}
              <div className='mt-2 text-xs'>
                <div className='font-semibold mb-1'>Active Zones:</div>
                {config.intrusion_zones.some((z: Zone) => z.active) ? (
                  <ul className='list-disc pl-4 space-y-0.5'>
                    {config.intrusion_zones
                      .filter((z: Zone) => z.active)
                      .map((zone: Zone, idx: number) => (
                        <li key={idx}>{zone.name}</li>
                      ))}
                  </ul>
                ) : (
                  <p className='text-gray-400 italic'>No active zones</p>
                )}
              </div>
            </div>
          ) : (
            <p className='text-gray-400 text-xs italic'>No zones defined</p>
          )}
        </div>
      </div>

      <div className='absolute bottom-4 right-4'>
        <button
          onClick={handleCameraChange}
          className='bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded'
        >
          Change Camera
        </button>
      </div>
    </div>
  );
};

export default VideoFeed;
