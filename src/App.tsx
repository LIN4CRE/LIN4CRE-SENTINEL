import { Navigate, Route, Routes } from 'react-router-dom'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { DataProvider, useData } from './DataContext'
import { ToastProvider } from './ToastContext'
import { Layout } from './components/Layout'
import { Button, Logo } from './components/UI'
import Dashboard from './pages/Dashboard'
import Opportunities from './pages/Opportunities'
import Approvals from './pages/Approvals'
import Research from './pages/Research'
import Reports from './pages/Reports'
import Earnings from './pages/Earnings'
import Audit from './pages/Audit'
import SettingsPage from './pages/Settings'
import Assistant from './pages/Assistant'
import Maintenance from './pages/Maintenance'
import Recovery from './pages/Recovery'

function Application() {
  const { loading, error, refresh } = useData()
  if (loading) return <div className="app-loading"><Logo /><div className="loading-line"><i /></div><p>Opening local research operations…</p></div>
  if (error) return <div className="app-loading"><Logo /><div className="connection-error"><AlertTriangle size={24} /><h1>SENTINEL core is unavailable</h1><p>{error}</p><span>The dashboard has not substituted mock data. Start the local API and retry.</span><Button icon={<RefreshCw size={16} />} onClick={refresh}>Retry connection</Button></div></div>
  return <Layout><Routes><Route path="/" element={<Dashboard />} /><Route path="/assistant" element={<Assistant />} /><Route path="/maintenance" element={<Maintenance />} /><Route path="/recovery" element={<Recovery />} /><Route path="/opportunities" element={<Opportunities />} /><Route path="/approvals" element={<Approvals />} /><Route path="/research" element={<Research />} /><Route path="/reports" element={<Reports />} /><Route path="/earnings" element={<Earnings />} /><Route path="/audit" element={<Audit />} /><Route path="/settings" element={<SettingsPage />} /><Route path="*" element={<Navigate to="/" replace />} /></Routes></Layout>
}
export default function App() { return <ToastProvider><DataProvider><Application /></DataProvider></ToastProvider> }
