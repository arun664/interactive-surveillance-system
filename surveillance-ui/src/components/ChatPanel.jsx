import { useState, useEffect, useRef } from "react";

export default function ChatPanel() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(false);
  const recognitionRef = useRef(null);
  const [listening, setListening] = useState(false);

  useEffect(() => {
    fetchRules();
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.lang = "en-US";
      recognition.interimResults = false;
      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setQuestion(transcript);
      };
      recognitionRef.current = recognition;
    }
  }, []);

  const fetchRules = async () => {
    try {
      const res = await fetch("http://localhost:8000/rules/list");
      const data = await res.json();
      setRules(data.rules || []);
    } catch (err) {
      console.error("Failed to load rules:", err);
    }
  };

  const askQuestion = async () => {
    if (!question.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/monitor/ask?question=${encodeURIComponent(question)}`);
      const data = await res.json();
      console.log("AI response:", data);
      setAnswer(data.answer || data.ai_analysis || data.error || 'No response');
    } catch (err) {
      console.error("Fetch failed:", err);
      setAnswer("Error contacting server.");
    }
    fetchRules();
    setLoading(false);
  };

  const startVoice = () => {
    if (!recognitionRef.current) return;
    setListening(true);
    recognitionRef.current.start();
    recognitionRef.current.onend = () => setListening(false);
  };

  const handleVoiceUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    const filePath = `data/${file.name}`; // Ensure the file is stored in this path server-side

    try {
      const response = await fetch(
        `http://localhost:8000/voice/command?audio_path=${filePath}`,
        {
          method: "POST",
        }
      );
      const data = await response.json();
      if (data.transcript) {
        setQuestion(data.transcript);
      } else {
        alert("Failed to transcribe voice");
      }
    } catch (error) {
      console.error("Voice upload error:", error);
      alert("Error uploading voice");
    }
  };

  return (
    <div className="bg-gray-800 p-4 rounded-lg shadow flex flex-col">
      <h2 className="text-lg font-semibold mb-4">Ask AI</h2>

      <div className="flex items-start gap-2 mb-2">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask something like: Who came today?"
          className="bg-gray-700 p-2 rounded text-white resize-none w-full"
          rows={3}
        />
        <button
          onClick={startVoice}
          disabled={listening}
          className={`px-3 py-2 rounded transition ${
            listening
              ? "bg-purple-300 cursor-not-allowed"
              : "bg-purple-600 hover:bg-purple-500"
          }`}
        >
          {listening ? "🎙️ Listening..." : "🎤"}
        </button>
      </div>

      <div className="flex justify-between items-center mb-3">
        <input
          type="file"
          accept=".mp3,.wav"
          onChange={handleVoiceUpload}
          className="text-xs text-gray-400"
        />
        <button
          onClick={askQuestion}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded"
        >
          {loading ? "Asking..." : "Ask"}
        </button>
      </div>

      {answer && (
        <div className="mt-4 text-sm text-green-300 whitespace-pre-line bg-gray-700 p-2 rounded">
          <strong>AI Answer:</strong> {answer}
        </div>
      )}

      <div className="mt-6">
        <h3 className="text-sm text-gray-400 mb-1">Tracked Rules:</h3>
        <ul className="text-xs text-purple-300 space-y-1 max-h-40 overflow-y-auto">
          {rules.map((rule, i) => (
            <li
              key={i}
              className="bg-gray-700 p-2 rounded border border-gray-600"
            >
              <code>{JSON.stringify(rule)}</code>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
