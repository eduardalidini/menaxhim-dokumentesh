import { Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from './components/AppLayout'
import ProtectedRoute from './components/ProtectedRoute'
import ArkivaPage from './pages/ArkivaPage'
import DokumentePage from './pages/DokumentePage'
import DrivePage from './pages/DrivePage'
import LoginPage from './pages/LoginPage'
import NgarkoPage from './pages/NgarkoPage'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/dokumente" replace />} />
          <Route path="/dokumente" element={<DokumentePage />} />
          <Route path="/arkiva" element={<ArkivaPage />} />
          <Route path="/ngarko" element={<NgarkoPage />} />
          <Route path="/drive" element={<DrivePage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
