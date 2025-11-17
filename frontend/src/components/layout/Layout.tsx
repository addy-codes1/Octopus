import { Outlet, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import Sidebar from './Sidebar'

export default function Layout() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
