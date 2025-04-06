import React, { useEffect, useState } from "react";
import { Alert } from "../types";

interface AlertListProps {
  alerts: Alert[];
  onDeleteAlert: (id: string) => void;
  onClearAlerts: () => void;
}

const AlertList: React.FC<AlertListProps> = ({
  alerts,
  onDeleteAlert,
  onClearAlerts,
}) => {
  const [sortedAlerts, setSortedAlerts] = useState<Alert[]>([]);

  // Sort alerts in descending order by timestamp whenever the alerts prop changes
  useEffect(() => {
    const sorted = [...alerts].sort((a, b) => b.timestamp - a.timestamp);
    setSortedAlerts(sorted);
  }, [alerts]);

  const getAlertTypeColor = (type: string) => {
    switch (type) {
      case "loitering":
        return "bg-yellow-100 border-yellow-500 text-yellow-700";
      case "pacing":
        return "bg-orange-100 border-orange-500 text-orange-700";
      case "intrusion":
        return "bg-red-100 border-red-500 text-red-700";
      case "zone_intrusion":
        return "bg-red-100 border-red-500 text-red-700";
      case "high_risk":
        return "bg-purple-100 border-purple-500 text-purple-700";
      default:
        return "bg-gray-100 border-gray-500 text-gray-700";
    }
  };

  return (
    <div className='bg-white shadow rounded-lg p-6'>
      <div className='flex justify-between mb-4'>
        <h3 className='text-lg font-semibold'>Recent Alerts</h3>
        {sortedAlerts.length > 0 && (
          <button
            onClick={onClearAlerts}
            className='bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm'
          >
            Clear All
          </button>
        )}
      </div>

      {sortedAlerts.length === 0 ? (
        <p className='text-gray-500 text-center py-8'>
          No alerts detected yet.
        </p>
      ) : (
        <div className='space-y-3'>
          {sortedAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`border-l-4 p-4 rounded shadow-sm ${getAlertTypeColor(
                alert.type
              )}`}
            >
              <div className='flex justify-between'>
                <div>
                  <h4 className='font-semibold capitalize'>
                    {alert.type.replace(/_/g, " ")} Alert
                  </h4>
                  <p className='text-sm'>
                    Person ID: {alert.track_id} | Suspicion Score:{" "}
                    {alert.suspicion_score.toFixed(1)}
                  </p>
                  <p className='text-sm'>
                    {new Date(alert.timestamp * 1000).toLocaleString()}
                  </p>
                </div>
                <button
                  onClick={() => onDeleteAlert(alert.id)}
                  className='text-gray-500 hover:text-red-500'
                  aria-label='Delete alert'
                >
                  <svg
                    xmlns='http://www.w3.org/2000/svg'
                    className='h-5 w-5'
                    viewBox='0 0 20 20'
                    fill='currentColor'
                  >
                    <path
                      fillRule='evenodd'
                      d='M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z'
                      clipRule='evenodd'
                    />
                  </svg>
                </button>
              </div>

              {alert.duration && (
                <p className='text-xs mt-1'>
                  Duration: {alert.duration.toFixed(1)}s
                </p>
              )}

              {alert.direction_changes && (
                <p className='text-xs mt-1'>
                  Direction Changes: {alert.direction_changes}
                </p>
              )}

              {alert.zone_name ? (
                <p className='text-xs mt-1 font-medium'>
                  Zone: {alert.zone_name}
                </p>
              ) : (
                alert.zone_id !== undefined && (
                  <p className='text-xs mt-1'>Zone ID: {alert.zone_id}</p>
                )
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AlertList;
