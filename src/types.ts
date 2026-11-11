export type Eligibility = 'eligible' | 'review_required' | 'rejected'
export type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'revoked'

export interface ScoreFactor { key: string; weight: number; factor: number; points: number }
export interface Programme {
  id: string; name: string; platform: string; handle: string
  programme_url: string; policy_url: string; reward_criteria_url: string
  currency: string; reward_min: number; reward_max: number; realistic_reward: number | null
  assets: string[]; automation_policy: string; ai_policy: string; payout_process: string
  source_checked_at: string; probability_valid: number | null; competition_risk: number | null
  estimated_hours: number | null; notes: string; source_type: string
  eligibility_status: Eligibility; eligibility_reasons: string[]; score: number | null
  expected_value_per_hour: number | null; score_breakdown: ScoreFactor[] | null
  created_at: string; updated_at: string; archived: number
  approvals?: Approval[]; findings?: Finding[]
}
export interface Approval {
  id: string; programme_id: string; programme_name?: string; platform?: string
  assets: string[]; methods: string[]; rate_limit: number; expires_at: string
  scope_hash: string; status: ApprovalStatus; requested_at: string; decided_at: string | null
  decision_note: string
}
export interface Finding {
  id: string; programme_id: string; programme_name?: string; platform?: string
  title: string; asset: string; vulnerability_class: string; severity: string
  status: string; summary: string; reproduction_steps: string; impact: string
  evidence: string; remediation: string; ai_disclosure: string
  created_at: string; updated_at: string; validated_at: string | null; validated_by: string | null
  report_id?: string; report_status?: string
}
export interface Report {
  id: string; finding_id: string; platform_report_id: string; status: string
  content_md: string; submitted_at: string | null; decision_at: string | null
  created_at: string; updated_at: string; title?: string; asset?: string; severity?: string
  programme_name?: string; platform?: string; programme_currency?: string
}
export interface Payment {
  id: string; report_id: string; amount: number; currency: string; status: 'awarded' | 'paid'
  awarded_at: string | null; paid_at: string | null; reference: string; notes: string
  created_at: string; title?: string; programme_name?: string; platform_report_id?: string
}
export interface AuditEvent {
  id: number; timestamp: string; event_type: string; entity_type: string; entity_id: string
  message: string; details: Record<string, unknown>
}
export interface Settings {
  ai_strategy: string; opportunity_scope: string; autonomy: string; kill_switch: boolean
  testing_engine_enabled: boolean; auto_submission_enabled: boolean; external_ai_enabled: boolean
  external_provider: string; monthly_spend_cap_gbp: number; ollama_url: string
  ollama_model: string; researcher_name: string; setup_backup_verified: boolean
  automatic_monitoring: boolean; monitor_interval_minutes: number; last_monitor_run: string | null
  host_companion_url: string; host_companion_configured: boolean; setup_role: string
}
export interface Dashboard {
  counts: { programmes: number; eligible: number; pending_approvals: number; findings: number; validated_findings: number; submitted_reports: number; accepted_reports: number; pc_audits: number }
  paid: { currency: string; total: number }[]; awarded: { currency: string; total: number }[]
  settings: Settings; recent_activity: AuditEvent[]
}
export interface SourceRepository { name: string; repository: string; url: string; role: string; status: string; cost: string; caution: string }
export interface SourcePolicy { name: string; url: string; checked_at: string; summary: string }
export interface Sources { checked_at: string; repositories: SourceRepository[]; policies: SourcePolicy[] }
export interface Health { status: string; version: string; database: string; testing_engine: string; auto_submission: string; kill_switch: boolean; time: string }
