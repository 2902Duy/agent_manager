import { create } from 'zustand'

export interface ExecutionEvent {
  time: string
  kind: string
  message: string
}

interface AppState {
  isRunning: boolean
  currentSessionId: string | null
  events: ExecutionEvent[]
  result: string | null
  currentAgent: string
  currentTask: string
  delegatedAgent: string

  setRunning: (running: boolean) => void
  setSessionId: (id: string | null) => void
  setEvents: (events: ExecutionEvent[]) => void
  clearEvents: () => void
  setResult: (result: string | null) => void
  setCurrentAgent: (agent: string) => void
  setCurrentTask: (task: string) => void
  setDelegatedAgent: (agent: string) => void
}

export const useAppStore = create<AppState>((set) => ({
  isRunning: false,
  currentSessionId: null,
  events: [],
  result: null,
  currentAgent: '',
  currentTask: '',
  delegatedAgent: '',

  setRunning: (running) => set({ isRunning: running }),
  setSessionId: (id) => set({ currentSessionId: id }),
  setEvents: (events) => set({ events }),
  clearEvents: () => set({ events: [], result: null, currentAgent: '', currentTask: '', delegatedAgent: '' }),
  setResult: (result) => set({ result }),
  setCurrentAgent: (agent) => set({ currentAgent: agent }),
  setCurrentTask: (task) => set({ currentTask: task }),
  setDelegatedAgent: (agent) => set({ delegatedAgent: agent }),
}))
