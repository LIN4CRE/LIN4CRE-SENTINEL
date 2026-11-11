import { FormEvent, useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Bot, CheckCircle2, ChevronDown, CircleDollarSign, Clock3, CloudOff, HardDrive, History, Loader2, LockKeyhole, MessageSquareText, Plus, RotateCcw, Send, ShieldCheck, Sparkles, SquareActivity, User, Wrench, ZapOff } from 'lucide-react'
import { ChatMessage, Conversation, HostStatus, Operation, operationsApi } from '../operations'
import { useData } from '../DataContext'
import { useToast } from '../ToastContext'
import { cx, date } from '../utils'
import { Badge, Button, EmptyState, Notice } from '../components/UI'
import OperationCard from '../components/OperationCard'

const suggestions = [
  { text: 'Check whether everything is working', icon: SquareActivity },
  { text: 'Install anything I’m missing', icon: Wrench },
  { text: 'Check for updates', icon: RotateCcw },
  { text: 'Back up everything', icon: HardDrive },
  { text: 'Show me how much storage SENTINEL is using', icon: CircleDollarSign },
  { text: 'Explain what you’re doing', icon: MessageSquareText },
]

export default function Assistant() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [conversationId, setConversationId] = useState<string | undefined>()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [operations, setOperations] = useState<Record<string, Operation>>({})
  const [host, setHost] = useState<HostStatus | null>(null)
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [historyOpen, setHistoryOpen] = useState(false)
  const { settings } = useData()
  const toast = useToast(); const navigate = useNavigate(); const bottom = useRef<HTMLDivElement>(null)

  const loadOperations = useCallback(async () => {
    try {
      const items = await operationsApi.list()
      setOperations(Object.fromEntries(items.map(item => [item.id, item])))
    } catch { /* Preserve last actual state; next poll retries. */ }
  }, [])
  const loadConversations = useCallback(async () => {
    try { setConversations(await operationsApi.conversations()) } catch { /* shown when sending fails */ }
  }, [])
  useEffect(() => { loadConversations(); loadOperations(); operationsApi.hostStatus().then(setHost).catch(() => setHost(null)) }, [loadConversations, loadOperations])
  useEffect(() => {
    const timer = window.setInterval(loadOperations, 2500)
    return () => window.clearInterval(timer)
  }, [loadOperations])
  useEffect(() => { bottom.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [messages, busy])

  const openConversation = async (id?: string) => {
    setConversationId(id)
    if (!id) { setMessages([]); return }
    try { setMessages(await operationsApi.messages(id)) }
    catch (error) { toast(error instanceof Error ? error.message : 'Unable to open conversation', 'error') }
  }
  const send = async (text: string) => {
    if (!text.trim() || busy) return
    setBusy(true); setInput('')
    const optimistic: ChatMessage = { id: `local-${Date.now()}`, conversation_id: conversationId || '', role: 'user', content: text, created_at: new Date().toISOString(), operation_id: null, status: 'complete', metadata: {} }
    setMessages(current => [...current, optimistic])
    try {
      const result = await operationsApi.send(text, conversationId)
      if (!conversationId) setConversationId(result.conversation_id)
      setMessages(current => [...current.filter(item => item.id !== optimistic.id), { ...optimistic, id: `sent-${Date.now()}` }, result.message])
      if (result.operation) setOperations(current => ({ ...current, [result.operation!.id]: result.operation! }))
      await Promise.all([loadConversations(), loadOperations()])
    } catch (error) {
      setMessages(current => current.filter(item => item.id !== optimistic.id))
      setInput(text)
      toast(error instanceof Error ? error.message : 'SENTINEL could not process the request', 'error')
    } finally { setBusy(false) }
  }
  const submit = (event: FormEvent) => { event.preventDefault(); send(input) }
  const active = Object.values(operations).filter(item => ['running', 'queued'].includes(item.status))

  return <div className="assistant-page">
    <header className="assistant-header"><div><div className="eyebrow">NATURAL-LANGUAGE OPERATIONS</div><h1><Sparkles size={25} />Ask SENTINEL</h1><p>Talk to your research operation. Technical work stays behind registered, auditable permission boundaries.</p></div><div className="assistant-header-actions"><div className="conversation-select"><button onClick={() => setHistoryOpen(!historyOpen)}><History size={15} />{conversationId ? 'Conversation history' : 'New conversation'}<ChevronDown size={14} /></button>{historyOpen && <div className="conversation-menu">{conversations.map(item => <button key={item.id} onClick={() => { openConversation(item.id); setHistoryOpen(false) }}><MessageSquareText size={14} /><span>{item.title}</span><small>{item.message_count || 0}</small></button>)}{!conversations.length && <p>No previous conversations</p>}</div>}</div><Button variant="secondary" size="sm" icon={<Plus size={15} />} onClick={() => openConversation()}>New chat</Button></div></header>
    <div className="assistant-layout">
      <section className="assistant-conversation panel">
        <div className="conversation-status"><div><span className="assistant-pulse" /><strong>Operations assistant</strong><span>Constrained planner · local first</span></div><Badge value={settings?.kill_switch ? 'revoked' : 'operational'} dot /></div>
        <div className="message-scroll">
          {!messages.length && <div className="assistant-welcome"><div className="assistant-emblem"><Sparkles size={28} /></div><h2>What would you like SENTINEL to handle?</h2><p>You don’t need commands or configuration files. Ask in ordinary language. You’ll see the plan, approval requirement, actual result and any limitation.</p><div className="suggestion-grid">{suggestions.map(item => <button key={item.text} onClick={() => send(item.text)}><item.icon size={17} /><span>{item.text}</span><ArrowRight size={14} /></button>)}</div><div className="assistant-boundary"><ShieldCheck size={16} /><span><strong>You remain in control.</strong> Installs, updates, repairs, restores and external testing always follow their approval rules.</span></div></div>}
          {messages.map(message => <div key={message.id} className={cx('chat-message', `chat-${message.role}`)}>
            <div className="chat-avatar">{message.role === 'assistant' ? <Bot size={17} /> : <User size={17} />}</div>
            <div className="chat-content"><div className="chat-meta"><strong>{message.role === 'assistant' ? 'SENTINEL' : 'You'}</strong><span>{date(message.created_at, true)}</span></div><p>{message.content}</p>
              {message.metadata.interpretation && <div className="intent-note"><LockKeyhole size={12} />{message.metadata.interpretation}</div>}
              {message.metadata.links?.map((link: any) => <button className="chat-link" key={link.path} onClick={() => navigate(link.path)}>{link.label}<ArrowRight size={13} /></button>)}
              {message.operation_id && operations[message.operation_id] && <OperationCard operation={operations[message.operation_id]} onChanged={loadOperations} compact />}
            </div>
          </div>)}
          {busy && <div className="chat-message chat-assistant"><div className="chat-avatar"><Bot size={17} /></div><div className="chat-content"><div className="assistant-thinking"><Loader2 size={15} className="spin" /><span>Checking real state and preparing the safest registered action…</span></div></div></div>}
          <div ref={bottom} />
        </div>
        <form className="assistant-input" onSubmit={submit}><div><textarea rows={2} value={input} onChange={event => setInput(event.target.value)} onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); submit(event) } }} placeholder="Ask SENTINEL to check, install, repair, update, back up, restore or explain…" disabled={busy} /><div className="input-bottom"><span><LockKeyhole size={12} />No arbitrary commands · approval before system changes</span><Button type="submit" disabled={!input.trim() || busy} icon={<Send size={15} />}>Send</Button></div></div></form>
      </section>
      <aside className="assistant-sidebar">
        <section className="panel assistant-side-card"><div className="side-card-title"><SquareActivity size={16} /><h3>Live operation state</h3></div><div className="assistant-state-row"><span>Core planner</span><Badge value="operational" dot /></div><div className="assistant-state-row"><span>Windows companion</span><Badge value={host?.connected ? 'operational' : 'not_configured'} /></div>{host?.error && <p className="side-warning">{host.error}</p>}<div className="assistant-state-row"><span>Active operations</span><strong>{active.length}</strong></div><div className="assistant-state-row"><span>AI model fallback</span><strong>{settings?.ollama_model || 'Not configured'}</strong></div></section>
        <section className="panel assistant-side-card"><div className="side-card-title"><ShieldCheck size={16} /><h3>Permission envelope</h3></div><ul className="permission-list"><li><CheckCircle2 size={14} /><span>Health and update checks</span><Badge value="read only" /></li><li><CheckCircle2 size={14} /><span>Backups</span><Badge value="safe write" /></li><li><LockKeyhole size={14} /><span>Installs, updates and repairs</span><Badge value="owner" /></li><li><LockKeyhole size={14} /><span>Restore and security changes</span><Badge value="owner" /></li><li><ZapOff size={14} /><span>Emergency stop</span><Badge value="immediate" /></li></ul></section>
        <section className="panel assistant-side-card"><div className="side-card-title"><Clock3 size={16} /><h3>What happens next</h3></div><ol className="operation-explainer"><li><span>1</span>SENTINEL interprets your request.</li><li><span>2</span>Real state is inspected when needed.</li><li><span>3</span>You review any consequential plan.</li><li><span>4</span>The action runs and is verified.</li><li><span>5</span>Results and failures enter the audit log.</li></ol></section>
        <button className="assistant-emergency" onClick={() => send('Stop all running research')}><ZapOff size={17} /><span><strong>Emergency stop</strong>Revoke research approvals now</span></button>
      </aside>
    </div>
  </div>
}
