// context/ToastContext.jsx - toast notifications.
// Provides showToast({ type, message }) anywhere in the app. Toasts
// auto-dismiss after a few seconds and stack at the bottom of the screen.
import { createContext, useCallback, useContext, useState } from 'react'

const ToastContext = createContext(null)

let nextId = 1

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const dismiss = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const showToast = useCallback(
    ({ type = 'success', message }) => {
      const id = nextId++
      setToasts((prev) => [...prev, { id, type, message }])
      setTimeout(() => dismiss(id), 4500)
    },
    [dismiss]
  )

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="toast-stack">
        {toasts.map((toast) => (
          <div key={toast.id} className={`toast toast-${toast.type}`} onClick={() => dismiss(toast.id)}>
            <span className="toast-dot" />
            <span>{toast.message}</span>
            <button className="toast-close" onClick={() => dismiss(toast.id)} aria-label="Dismiss">
              &times;
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  return useContext(ToastContext)
}
