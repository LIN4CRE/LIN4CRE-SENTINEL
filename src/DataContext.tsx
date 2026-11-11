import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from 'react'
import { api } from './api'
import type { Approval, AuditEvent, Dashboard, Finding, Health, Payment, Programme, Report, Settings, Sources } from './types'

interface DataState {
  health: Health | null; dashboard: Dashboard | null; programmes: Programme[]; approvals: Approval[]
  findings: Finding[]; reports: Report[]; payments: Payment[]; audit: AuditEvent[]
  settings: Settings | null; sources: Sources | null; loading: boolean; error: string | null
  refresh: () => Promise<void>
}
const DataContext = createContext<DataState | null>(null)

export function DataProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<Omit<DataState, 'refresh'>>({ health: null, dashboard: null, programmes: [], approvals: [], findings: [], reports: [], payments: [], audit: [], settings: null, sources: null, loading: true, error: null })
  const refresh = useCallback(async () => {
    try {
      const [health, dashboard, programmes, approvals, findings, reports, payments, audit, settings, sources] = await Promise.all([
        api<Health>('/health'), api<Dashboard>('/dashboard'), api<Programme[]>('/programmes'), api<Approval[]>('/approvals'),
        api<Finding[]>('/findings'), api<Report[]>('/reports'), api<Payment[]>('/payments'), api<AuditEvent[]>('/audit'),
        api<Settings>('/settings'), api<Sources>('/sources'),
      ])
      setState({ health, dashboard, programmes, approvals, findings, reports, payments, audit, settings, sources, loading: false, error: null })
    } catch (error) {
      setState(previous => ({ ...previous, loading: false, error: error instanceof Error ? error.message : 'Unable to reach SENTINEL core' }))
    }
  }, [])
  useEffect(() => { refresh() }, [refresh])
  return <DataContext.Provider value={{ ...state, refresh }}>{children}</DataContext.Provider>
}
export function useData() {
  const value = useContext(DataContext)
  if (!value) throw new Error('useData must be used within DataProvider')
  return value
}
