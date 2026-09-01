import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

import App from './App'
import { AuthProvider } from './context/AuthContext'
import { NotificationProvider } from './context/NotificationContext'
import { ThemeProvider } from './context/ThemeContext'
import { ToastProvider } from './context/ToastContext'
import { ConfirmProvider } from './components/ui/ConfirmDialog'
import { RecurrenceScopeProvider } from './components/schedule/RecurrenceScopeDialog'
import './index.css'

/**
 * Ordem dos provedores (de fora para dentro):
 *   Theme    → não depende de nada
 *   Toast    → usado por Auth e Notification
 *   Auth     → NotificationProvider precisa saber se há sessão
 *   Notification → consome Auth + Toast
 *   Confirm  → diálogos, usados pelas páginas
 *   RecurrenceScope → diálogo de exclusão de sessões recorrentes
 */
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <ThemeProvider>
        <ToastProvider>
          <AuthProvider>
            <NotificationProvider>
              <ConfirmProvider>
                <RecurrenceScopeProvider>
                  <App />
                </RecurrenceScopeProvider>
              </ConfirmProvider>
            </NotificationProvider>
          </AuthProvider>
        </ToastProvider>
      </ThemeProvider>
    </BrowserRouter>
  </StrictMode>,
)
