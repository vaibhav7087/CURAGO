import { Routes, Route } from 'react-router-dom'
import LoginLanding from './pages/LoginLanding.jsx'
import DoctorDashboard from './pages/DoctorDashboard.jsx'
import TraineeDashboard from './pages/TraineeDashboard.jsx'
import './App.css'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LoginLanding />} />
      <Route path="/doctor" element={<DoctorDashboard />} />
      <Route path="/trainee" element={<TraineeDashboard />} />
    </Routes>
  )
}
