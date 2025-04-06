import { useEffect, useState } from "react";

export default function DetectionPanel() {
  const [detections, setDetections] = useState({ objects: [], actions: [] });
  const [monitoring, setMonitoring] = useState(false);
  const [loading, setLoading] = useState(false);

  const fetchDetections = async () => {
    try {
      const res = await fetch("http://localhost:8000/monitor/detections");
      const data = await res.json();
      setDetections(data);
    } catch (err) {
      console.error("Error fetching detections:", err);
    }
  };

  useEffect(() => {
    const interval = setInterval(fetchDetections, 2000);
    return () => clearInterval(interval);
  }, []);

  const startMonitoring = async () => {
    await fetch("http://localhost:8000/monitor/start", { method: "POST" });
    setMonitoring(true);
  };

  const stopMonitoring = async () => {
    await fetch("http://localhost:8000/monitor/stop", { method: "POST" });
    setMonitoring(false);
  };

  const runManualCheck = async () => {
    setLoading(true);
    const rule = prompt(
      "Enter a rule to check against (e.g. Alert if person is on the right):"
    );
    if (rule) {
      const res = await fetch(
        `http://localhost:8000/monitor/ai-check?rule=${encodeURIComponent(
          rule
        )}`
      );
      const data = await res.json();
      alert("Gemini says:\n" + (data.ai_analysis || data.error));
    }
    setLoading(false);
  };

  return (
    <div className="bg-gray-800 p-4 rounded-lg shadow">
      <div className="flex justify-between mb-4 items-center">
        <h2 className="text-lg font-semibold">Live Detection</h2>
        <div className="flex gap-2">
          <button
            onClick={startMonitoring}
            className="bg-green-600 px-2 py-1 rounded text-sm hover:bg-green-500"
          >
            Start
          </button>
          <button
            onClick={stopMonitoring}
            className="bg-red-600 px-2 py-1 rounded text-sm hover:bg-red-500"
          >
            Stop
          </button>
          <button
            onClick={runManualCheck}
            disabled={loading}
            className="bg-blue-600 px-2 py-1 rounded text-sm hover:bg-blue-500 disabled:opacity-50"
          >
            Manual Check
          </button>
        </div>
      </div>

      {monitoring ? (
        <img
        src="http://localhost:8000/monitor/stream"
        alt="Live stream"
        className="w-full h-64 object-cover rounded border border-gray-400 mb-4"
        onError={(e) => {
          e.target.src = '';
          console.error("Failed to load stream");
        }}
      />      
      ) : (
        <div className="w-full h-64 bg-gray-100 border-2 border-dashed border-gray-400 flex items-center justify-center rounded text-gray-600 mb-4">
          Monitoring is off. Start to view stream.
        </div>
      )}

      <div className="mb-2">
        <h3 className="text-sm text-gray-400">Objects Detected:</h3>
        <ul className="list-disc list-inside text-green-300">
          {detections.objects?.map((obj, i) => (
            <li key={i}>{obj}</li>
          ))}
        </ul>
      </div>

      <div>
        <h3 className="text-sm text-gray-400">Actions:</h3>
        <ul className="list-disc list-inside text-yellow-300">
          {detections.actions?.map((act, i) => (
            <li key={i}>{act}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
