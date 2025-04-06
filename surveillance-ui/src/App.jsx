import DetectionPanel from './components/DetectionPanel';
import ChatPanel from './components/ChatPanel';
import Header from './components/Header';

export default function App() {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <Header />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4">
        <DetectionPanel />
        <ChatPanel />
      </div>
    </div>
  );
}
