export const cx = (...values: (string | false | null | undefined)[]) => values.filter(Boolean).join(' ')

export function money(value: number | null | undefined, currency = 'GBP', maximumFractionDigits = 0) {
  if (value === null || value === undefined) return '—'
  return new Intl.NumberFormat('en-GB', { style: 'currency', currency, maximumFractionDigits }).format(value)
}

export function date(value: string | null | undefined, includeTime = false) {
  if (!value) return 'Not recorded'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value.slice(0, 10)
  return new Intl.DateTimeFormat('en-GB', includeTime
    ? { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }
    : { day: '2-digit', month: 'short', year: 'numeric' }).format(parsed)
}

export function label(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export function percent(value: number | null | undefined) {
  return value === null || value === undefined ? 'Not estimated' : `${Math.round(value * 100)}%`
}

export function isoInHours(hours: number) {
  return new Date(Date.now() + hours * 3600000).toISOString()
}

export async function copyText(text: string) {
  await navigator.clipboard.writeText(text)
}
