import { createContext, ReactNode, useContext, useState } from 'react'
import { AlertCircle, CheckCircle2, X } from 'lucide-react'

type Toast = { id: number; message: string; tone: 'success' | 'error' }
const ToastContext = createContext<(message: string, tone?: 'success' | 'error') => void>(() => {})
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const notify = (message: string, tone: 'success' | 'error' = 'success') => {
    const id = Date.now() + Math.random()
    setToasts(current => [...current, { id, message, tone }])
    window.setTimeout(() => setToasts(current => current.filter(item => item.id !== id)), 5000)
  }
  return <ToastContext.Provider value={notify}>{children}<div className="toast-stack">{toasts.map(toast => <div className={`toast toast-${toast.tone}`} key={toast.id}>{toast.tone === 'success' ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}<span>{toast.message}</span><button onClick={() => setToasts(current => current.filter(item => item.id !== toast.id))}><X size={15} /></button></div>)}</div></ToastContext.Provider>
}
export const useToast = () => useContext(ToastContext)
