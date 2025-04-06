# AI Security Guard Frontend

This is the frontend application for the AI Security Guard system, built with Next.js, TypeScript, and Tailwind CSS.

## Features

- Real-time camera feed monitoring
- Detection of suspicious activities
- Alert management
- System configuration controls
- WebSocket communication for real-time updates

## Technologies Used

- Next.js 14
- TypeScript
- Tailwind CSS
- WebSocket API

## Getting Started

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Set the API URL (optional, defaults to http://localhost:3000):
   ```bash
   export NEXT_PUBLIC_API_URL=http://your-api-url
   ```
4. Run the development server:
   ```bash
   npm run dev
   ```
5. Open [http://localhost:3000](http://localhost:3000) in your browser

## Connecting to the Backend

The frontend requires the AI Security Guard API to be running. Ensure the Python FastAPI backend is running on the same machine or specify the correct URL using the `NEXT_PUBLIC_API_URL` environment variable.

## Features

- **Camera Feed**: View the real-time camera feed with detection overlays
- **Alerts Panel**: Monitor and manage detected security alerts
- **Configuration**: Adjust detection parameters and camera settings

## License

This project is licensed under the MIT License.
