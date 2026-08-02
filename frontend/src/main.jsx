// main.jsx - the entry point of the React application.
// It renders the whole app (App) into the <div id="root"> of index.html.
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

import App from './App.jsx'
import { AuthProvider } from './context/AuthContext.jsx'
import { ThemeProvider } from './context/ThemeContext.jsx'
import { ToastProvider } from './context/ToastContext.jsx'
import './styles/styles.css'

// Create the root element that React will control.
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {/* BrowserRouter gives us client-side navigation (URLs like /login). */}
    <BrowserRouter basename="/doctor-appointment-booking">
      {/* AuthProvider makes login state available to every page. */}
      <AuthProvider>
        {/* ThemeProvider handles light/dark mode. */}
        <ThemeProvider>
          {/* ToastProvider shows popup notifications. */}
          <ToastProvider>
            <App />
          </ToastProvider>
        </ThemeProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
)
