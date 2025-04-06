"use client";
import { useState, useEffect } from "react";
import { Config, Zone } from "../types";
import { apiService } from "../services/api";

const ConfigPanel: React.FC = () => {
  const [config, setConfig] = useState<Config>({
    loitering_threshold: 10.0,
    pacing_threshold: 3,
    intrusion_zones: [],
    zones_enabled: true,
    confidence_threshold: 0.5,
    audio_alerts: true,
    camera_source: "0",
    quiet_period_start: "22:00",
    quiet_period_end: "06:00",
    quiet_period_enabled: false,
  });

  const [isLoading, setIsLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [zoneName, setZoneName] = useState("");

  useEffect(() => {
    const fetchConfig = async () => {
      setIsLoading(true);
      const response = await apiService.getConfig();
      if (response.data) {
        setConfig(response.data);
        setError("");
      } else if (response.error) {
        setError("Failed to load configuration");
      }
      setIsLoading(false);
    };

    fetchConfig();
  }, []);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target as HTMLInputElement;
    const checked =
      type === "checkbox" ? (e.target as HTMLInputElement).checked : undefined;

    setConfig((prev) => ({
      ...prev,
      [name]:
        type === "checkbox"
          ? checked
          : type === "number"
          ? parseFloat(value)
          : value,
    }));
  };

  const handleSave = async () => {
    setIsLoading(true);
    setMessage("");
    setError("");

    const response = await apiService.updateConfig(config);

    if (response.data) {
      setMessage("Configuration saved successfully");
      setTimeout(() => setMessage(""), 3000);
    } else if (response.error) {
      setError("Failed to save configuration: " + response.error);
    }

    setIsLoading(false);
  };

  const addIntrustionZone = () => {
    if (!zoneName.trim()) {
      setError("Zone name is required");
      return;
    }

    // Create a simple rectangular zone in the center of the video
    const newZone: Zone = {
      points: [
        [0.25, 0.25],
        [0.75, 0.25],
        [0.75, 0.75],
        [0.25, 0.75],
      ],
      name: zoneName.trim(),
      active: true,
    };

    setConfig((prev) => ({
      ...prev,
      intrusion_zones: [...prev.intrusion_zones, newZone],
    }));

    setZoneName(""); // Reset zone name input
  };

  const toggleZoneStatus = (index: number) => {
    setConfig((prev) => {
      const updatedZones = [...prev.intrusion_zones];
      updatedZones[index] = {
        ...updatedZones[index],
        active: !updatedZones[index].active,
      };
      return {
        ...prev,
        intrusion_zones: updatedZones,
      };
    });
  };

  const removeZone = (index: number) => {
    setConfig((prev) => ({
      ...prev,
      intrusion_zones: prev.intrusion_zones.filter((_, i) => i !== index),
    }));
  };

  // Set current time to time field
  const setCurrentTime = (field: "quiet_period_start" | "quiet_period_end") => {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, "0");
    const minutes = now.getMinutes().toString().padStart(2, "0");
    const currentTime = `${hours}:${minutes}`;

    setConfig((prev) => ({
      ...prev,
      [field]: currentTime,
    }));
  };

  return (
    <div className='bg-white shadow rounded-lg p-6'>
      <h3 className='text-lg font-semibold mb-4'>System Configuration</h3>

      {isLoading ? (
        <div className='flex justify-center py-8'>
          <div className='loader animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500'></div>
        </div>
      ) : (
        <>
          {message && (
            <div className='mb-4 p-2 bg-green-100 text-green-700 rounded'>
              {message}
            </div>
          )}

          {error && (
            <div className='mb-4 p-2 bg-red-100 text-red-700 rounded'>
              {error}
            </div>
          )}

          <div className='space-y-4'>
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                Loitering Threshold (seconds)
              </label>
              <input
                type='number'
                name='loitering_threshold'
                value={config.loitering_threshold}
                onChange={handleChange}
                min='1'
                step='0.1'
                className='w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
              />
            </div>

            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                Pacing Threshold (direction changes)
              </label>
              <input
                type='number'
                name='pacing_threshold'
                value={config.pacing_threshold}
                onChange={handleChange}
                min='1'
                step='1'
                className='w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
              />
            </div>

            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                Confidence Threshold
              </label>
              <input
                type='number'
                name='confidence_threshold'
                value={config.confidence_threshold}
                onChange={handleChange}
                min='0.1'
                max='0.9'
                step='0.05'
                className='w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
              />
            </div>

            <div>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                Camera Source
              </label>
              <input
                type='text'
                name='camera_source'
                value={config.camera_source}
                onChange={handleChange}
                className='w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
              />
              <p className='text-sm text-gray-500 mt-1'>
                Use &quot;0&quot; for default webcam, or enter a path to a video
                file
              </p>
            </div>

            <div className='border-t pt-4 mt-4'>
              <h4 className='font-medium mb-2'>Quiet Period Settings</h4>

              <div className='flex items-center mb-2'>
                <input
                  type='checkbox'
                  name='quiet_period_enabled'
                  checked={config.quiet_period_enabled}
                  onChange={handleChange}
                  className='h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
                />
                <label className='ml-2 block text-sm text-gray-700'>
                  Enable Quiet Period (No Alerts)
                </label>
              </div>

              <div className='grid grid-cols-2 gap-2'>
                <div>
                  <label className='block text-sm font-medium text-gray-700 mb-1'>
                    Start Time
                  </label>
                  <div className='flex'>
                    <input
                      type='time'
                      name='quiet_period_start'
                      value={config.quiet_period_start}
                      onChange={handleChange}
                      className='flex-1 px-3 py-2 border border-gray-300 rounded-l-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
                    />
                    <button
                      type='button'
                      onClick={() => setCurrentTime("quiet_period_start")}
                      className='px-3 py-2 bg-gray-100 border border-l-0 border-gray-300 rounded-r-md hover:bg-gray-200 text-sm'
                    >
                      Now
                    </button>
                  </div>
                </div>
                <div>
                  <label className='block text-sm font-medium text-gray-700 mb-1'>
                    End Time
                  </label>
                  <div className='flex'>
                    <input
                      type='time'
                      name='quiet_period_end'
                      value={config.quiet_period_end}
                      onChange={handleChange}
                      className='flex-1 px-3 py-2 border border-gray-300 rounded-l-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
                    />
                    <button
                      type='button'
                      onClick={() => setCurrentTime("quiet_period_end")}
                      className='px-3 py-2 bg-gray-100 border border-l-0 border-gray-300 rounded-r-md hover:bg-gray-200 text-sm'
                    >
                      Now
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div className='flex items-center'>
              <input
                type='checkbox'
                name='audio_alerts'
                checked={config.audio_alerts}
                onChange={handleChange}
                className='h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
              />
              <label className='ml-2 block text-sm text-gray-700'>
                Enable Audio Alerts
              </label>
            </div>

            <div className='border-t pt-4'>
              <div className='flex justify-between items-center mb-2'>
                <label className='block text-sm font-medium text-gray-700'>
                  Surveillance Zones
                </label>
                <div className='flex items-center'>
                  <input
                    type='checkbox'
                    name='zones_enabled'
                    checked={config.zones_enabled}
                    onChange={handleChange}
                    className='h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mr-2'
                  />
                  <span className='text-sm mr-4'>Enable Zones</span>
                </div>
              </div>

              <p className='text-sm text-gray-600 mb-3'>
                Zones are designated areas in the video feed that trigger alerts
                when someone enters them. Create a zone by giving it a name and
                clicking &quot;Add Zone&quot;.
              </p>

              <div className='flex space-x-2 mb-3'>
                <input
                  type='text'
                  value={zoneName}
                  onChange={(e) => setZoneName(e.target.value)}
                  placeholder='Enter zone name'
                  className='flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
                />
                <button
                  type='button'
                  onClick={addIntrustionZone}
                  className='px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition'
                  disabled={!zoneName.trim()}
                >
                  Add Zone
                </button>
              </div>

              {config.intrusion_zones.length > 0 ? (
                <div className='space-y-2 border p-2 rounded max-h-60 overflow-y-auto'>
                  {config.intrusion_zones.map((zone, index) => (
                    <div
                      key={index}
                      className={`flex justify-between text-sm border-b pb-1 ${
                        !zone.active ? "opacity-50" : ""
                      }`}
                    >
                      <div>
                        <span className='font-medium'>{zone.name}</span>
                        <span className='ml-2 text-xs text-gray-500'>
                          (Default Rectangle)
                        </span>
                      </div>
                      <div>
                        <button
                          type='button'
                          onClick={() => toggleZoneStatus(index)}
                          className={`text-xs px-2 py-0.5 rounded mr-2 ${
                            zone.active
                              ? "bg-green-100 text-green-800"
                              : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {zone.active ? "Active" : "Inactive"}
                        </button>
                        <button
                          type='button'
                          onClick={() => removeZone(index)}
                          className='text-red-500 hover:text-red-700'
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className='text-sm text-gray-500'>No zones defined</p>
              )}
            </div>

            <div className='pt-4'>
              <button
                type='button'
                onClick={handleSave}
                className='w-full px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
                disabled={isLoading}
              >
                {isLoading ? "Saving..." : "Save Configuration"}
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ConfigPanel;
