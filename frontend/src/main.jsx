// main.jsx - the entry point of the React application.
// It renders the whole app (App) into the <div id="root"> of index.html.
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

import App from './App.jsx'
import { AuthProvider } from './context/AuthContext.jsx'
import './styles/styles.css'

// Create the root element that React will control.
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {/* BrowserRouter gives us client-side navigation (URLs like /login). */}
    <BrowserRouter>
      {/* AuthProvider makes login state available to every page. */}
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
)
