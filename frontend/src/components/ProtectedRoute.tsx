import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { getAuth } from '../lib/auth'

export default function ProtectedRoute() {
  const { accessToken } = getAuth()
  const location = useLocation()

  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}
