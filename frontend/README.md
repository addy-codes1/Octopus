# ScholarChat Frontend

React + TypeScript frontend for ScholarChat - Academic Research RAG Assistant.

## Features

- Dark-themed UI optimized for researchers
- Drag-and-drop PDF upload
- Real-time chat with streaming responses
- Paper library management
- Citation display with source tracking
- BibTeX/RIS export

## Tech Stack

- **Framework:** React 18 + TypeScript
- **Build:** Vite
- **Styling:** Tailwind CSS + shadcn/ui components
- **State:** Zustand (client) + React Query (server)
- **Routing:** React Router v6
- **Forms:** React Hook Form + Zod

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

The frontend will be available at http://localhost:5173

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/           # shadcn/ui components
│   │   └── layout/       # Layout components
│   ├── pages/            # Route pages
│   ├── lib/              # Utilities and API client
│   ├── store/            # Zustand stores
│   ├── hooks/            # Custom React hooks
│   └── types/            # TypeScript types
├── public/               # Static assets
└── index.html
```

## Deployment

### Vercel (Recommended)

1. Connect GitHub repository to Vercel
2. Set root directory to `frontend`
3. Configure environment variables
4. Deploy

### Environment Variables

- `VITE_API_URL` - Backend API URL (default: `/api/v1`)

## Development

```bash
# Lint code
npm run lint

# Type check
npm run build
```

## Connected to Backend

The frontend expects the backend API at `/api/v1`. In development, Vite proxies requests to `http://localhost:8000`. In production, configure your deployment to route API requests appropriately.
