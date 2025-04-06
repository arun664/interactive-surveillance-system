import React from "react";

interface NavbarProps {
  isConnected: boolean;
  activeTab: "feed" | "alerts" | "config";
  onTabChange: (tab: "feed" | "alerts" | "config") => void;
}

const Navbar: React.FC<NavbarProps> = ({
  isConnected,
  activeTab,
  onTabChange,
}) => {
  return (
    <nav className='bg-gray-800 text-white shadow-md'>
      <div className='container mx-auto px-4'>
        <div className='flex items-center justify-between h-16'>
          <div className='flex items-center'>
            <span className='text-xl font-bold'>AI Security Guard</span>

            <div className='ml-10 flex space-x-4'>
              <button
                onClick={() => onTabChange("feed")}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  activeTab === "feed"
                    ? "bg-gray-900 text-white"
                    : "text-gray-300 hover:bg-gray-700"
                }`}
              >
                Live Feed
              </button>

              <button
                onClick={() => onTabChange("alerts")}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  activeTab === "alerts"
                    ? "bg-gray-900 text-white"
                    : "text-gray-300 hover:bg-gray-700"
                }`}
              >
                Alerts
              </button>

              <button
                onClick={() => onTabChange("config")}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  activeTab === "config"
                    ? "bg-gray-900 text-white"
                    : "text-gray-300 hover:bg-gray-700"
                }`}
              >
                Configuration
              </button>
            </div>
          </div>

          <div className='flex items-center'>
            <div className='flex items-center'>
              <div
                className={`h-3 w-3 rounded-full mr-2 ${
                  isConnected ? "bg-green-500" : "bg-red-500"
                }`}
              ></div>
              <span className='text-sm'>
                {isConnected ? "Connected" : "Disconnected"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
