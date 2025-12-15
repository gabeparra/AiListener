# React Frontend Setup

Glup now includes a React frontend for interactive chat and real-time updates.

## Development Setup

### 1. Install Node.js dependencies

```bash
npm install
```

### 2. Start React development server

```bash
npm run dev
```

This will start Vite dev server on http://localhost:3000

### 3. Start Glup backend (in another terminal)

```bash
source .venv/bin/activate
python -m caption_ai --web --port 8000
```

The React app will proxy API requests to the backend automatically.

## Production Build

### Build React app

```bash
npm run build
```

This creates a production build in `web/dist/`

### Serve production build

The FastAPI server will automatically serve the built React app when you run:

```bash
python -m caption_ai --web
```

## Features

- **Interactive Chat**: Talk directly with Glup using the chat panel
- **Real-time Updates**: WebSocket connections for instant segment and summary updates
- **Meeting Segments**: View conversation segments in real-time
- **Glup Analysis**: See AI-generated summaries and analyses
- **Dark Theme**: Glup's distinctive dark styling

## Development Notes

- React dev server runs on port 3000
- Backend API runs on port 8000
- Vite automatically proxies `/api` and `/ws` to the backend
- Hot Module Replacement (HMR) enabled for instant updates

