// Patterns only — adapt imports/types to current api.ts and DataContext.

export async function fetchWithTimeout<T>(url: string, init: RequestInit = {}, timeoutMs = 10_000): Promise<T> {
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), timeoutMs)
  try {
    const response = await fetch(url, { ...init, signal: controller.signal })
    if (!response.ok) throw new Error(`Request failed (${response.status})`)
    return await response.json() as T
  } finally {
    window.clearTimeout(timer)
  }
}

export function shouldPollNow(): boolean {
  return document.visibilityState === 'visible' && navigator.onLine
}

// In a polling effect: pause while hidden/offline; refresh when visible/online.
// Always clear interval + event listeners on unmount, and never treat stale safety data as fresh.
export function useVisibilityRefresh(refresh: () => void) {
  // Sketch: useEffect(() => { const onVisible = () => { if (shouldPollNow()) refresh() };
  // document.addEventListener('visibilitychange', onVisible);
  // window.addEventListener('online', onVisible);
  // return () => { ...remove listeners... } }, [refresh])
}

// Partial bootstrap example: preserve successful independent panels.
export async function settledBootstrap<T extends Record<string, () => Promise<unknown>>>(
  requests: T
): Promise<Record<keyof T, PromiseSettledResult<unknown>>> {
  const entries = Object.entries(requests)
  const settled = await Promise.allSettled(entries.map(([, request]) => request()))
  return Object.fromEntries(entries.map(([key], i) => [key, settled[i]])) as Record<keyof T, PromiseSettledResult<unknown>>
}

// Never queue/auto-replay consequential mutations while offline. Offer explicit retry only after user review.
