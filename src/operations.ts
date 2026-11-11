import { api, post } from './api'

export interface OperationAction { action: string; component?: string; version?: string; previous_version?: string; model?: string; patch?: string }
export interface OperationPlan { actions?: OperationAction[]; stop_on_failure?: boolean; rollback_plan?: OperationPlan; recovery_point_id?: string; components?: string[]; label?: string }
export interface Operation {
  id: string; kind: string; title: string; description: string; risk: string; status: string
  requires_approval: number; approval_role: string; plan: OperationPlan; result: Record<string, any> | null
  verification: any[] | null; created_at: string; approved_at: string | null; started_at: string | null
  finished_at: string | null; error: string | null; recovery_point_id: string | null
  rollback_available: number; retry_of: string | null
}
export interface Dependency {
  id: string; component: string; name: string; category: string; required: number
  installed_version: string | null; latest_compatible_version: string | null; location: string | null
  source_repository: string; licence: string; status: string; last_checked: string | null
  update_available: number | null; update_category: string | null; release_url: string | null
  release_notes: string | null; download_size_bytes: number | null; new_cost_detected: number | null
  details: Record<string, any>; relationships: string[]
}
export interface HostStatus { connected: boolean; paired: boolean; details: Record<string, any> | null; error: string | null }
export interface AgentHealth { agent: string; status: string; summary: string }
export interface MaintenanceSummary {
  overall: string; last_checked: string | null; host: HostStatus; dependencies: Dependency[]
  core: { checked_at: string; checks: { component: string; status: string; summary: string; evidence: Record<string, any> }[]; agents: AgentHealth[] }
  latest_recovery: RecoveryPoint | null
  update_counts: { security: number; critical: number; application: number; available: number }
}
export interface RecoveryPoint {
  id: string; created_at: string; label: string; kind: string; root_path: string; manifest_path: string
  status: string; sha256: string; size_bytes: number; includes: string[]; source_version: string
  last_known_good: number; restored_at: string | null
}
export interface ChatMessage {
  id: string; conversation_id: string; role: 'user' | 'assistant'; content: string; created_at: string
  operation_id: string | null; status: string; metadata: Record<string, any>
}
export interface Conversation { id: string; created_at: string; title: string; message_count?: number }

export const operationsApi = {
  list: () => api<Operation[]>('/operations'),
  get: (id: string) => api<Operation>(`/operations/${id}`),
  approve: (id: string, planHash: string) => post<Operation>(`/operations/${id}/approve`, { confirmed: true, plan_hash: planHash }),
  retry: (id: string) => post<Operation>(`/operations/${id}/retry`),
  cancel: (id: string) => post<Operation>(`/operations/${id}/cancel`),
  inspect: () => post<any>('/operations/inspect'),
  updates: () => post<any>('/operations/updates/check'),
  installMissing: () => post<{ operation: Operation | null; message: string }>('/operations/install-missing'),
  planUpdates: () => post<{ operation: Operation | null; message: string }>('/operations/updates/plan'),
  repair: (component: string) => post<{ operation: Operation; message: string }>('/operations/repair', { component }),
  backup: () => post<Operation>('/operations/backup'),
  storage: () => api<any>('/operations/storage'),
  maintenance: () => api<MaintenanceSummary>('/maintenance/summary'),
  hostStatus: () => api<HostStatus>('/operations/host-status'),
  recovery: () => api<RecoveryPoint[]>('/recovery'),
  verifyRecovery: (id: string) => post<any>(`/recovery/${id}/verify`),
  restore: (id: string, components = ['database', 'files', 'config']) => post<{ operation: Operation; message: string }>(`/recovery/${id}/restore`, { components }),
  conversations: () => api<Conversation[]>('/assistant/conversations'),
  messages: (id: string) => api<ChatMessage[]>(`/assistant/conversations/${id}`),
  send: (text: string, conversationId?: string) => post<{ conversation_id: string; message: ChatMessage; operation: Operation | null }>('/assistant/message', { text, conversation_id: conversationId }),
}

export async function operationPlanHash(plan: OperationPlan): Promise<string> {
  // Mirrors backend canonical JSON: sorted keys, compact separators, ensure_ascii=False.
  const canonical = (value: any): any => {
    if (Array.isArray(value)) return value.map(canonical)
    if (value && typeof value === 'object') return Object.keys(value).sort().reduce<Record<string, any>>((result, key) => { result[key] = canonical(value[key]); return result }, {})
    return value
  }
  const text = JSON.stringify(canonical(plan))
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text))
  return Array.from(new Uint8Array(digest)).map(byte => byte.toString(16).padStart(2, '0')).join('')
}
