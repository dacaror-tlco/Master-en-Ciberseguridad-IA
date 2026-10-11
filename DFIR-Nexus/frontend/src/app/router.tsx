import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AppShell } from '@/shared/layout'
import { AuthGuard } from '@/shared/auth'
import { LoginPage } from './LoginPage'
import { ProfilePage } from './ProfilePage'
import { HelpPage } from './HelpPage'
import { CasesPage } from '@/modules/cases/pages'
import { osintRoutes } from '@/modules/osint/routes'
import { TrackingPage } from '@/modules/tracking/pages/TrackingPage'
import { TimelinePage } from '@/modules/timeline/pages/TimelinePage'
import { ReportsPage } from '@/modules/reports/pages/ReportsPage'
import { ChatPage } from '@/modules/chat/pages/ChatPage'
import { DashboardPage } from '@/modules/dashboard/pages/DashboardPage'

/**
 * Único punto que conecta rutas con páginas de módulo. AppShell es el layout
 * raíz (sidebar + header + fondos globales); cada módulo aporta su página
 * (o, en el caso de OSINT, su propio sub-árbol de rutas). /cases, /tracking,
 * /timeline, /reports y /osint son funcionales; los demás módulos quedan
 * preparados con una página placeholder mínima.
 *
 * OSINT ("osint/*") es distinto al resto: no aporta una única página sino
 * `osintRoutes`, su propio conjunto de rutas con pestañas internas (dominio,
 * email, wallet, etc.) — es el módulo `scam-shield/frontend` integrado aquí
 * (ver docs/INTEGRACION_Y_DESPLIEGUE.md), no un backend distinto: solo su
 * *backend* sigue siendo un proceso aparte (puerto 8124).
 *
 * /login vive fuera de AuthGuard/AppShell (sin sidebar, sin sesión
 * exigida — sería la propia pantalla que la crea). Todo lo demás cuelga
 * de AuthGuard: sin sesión localmente válida, ninguna ruta de la
 * aplicación llega a montarse (ver shared/auth/AuthGuard.tsx) — esto es
 * únicamente protección de UX, la autorización real sigue dependiendo de
 * cada backend.
 *
 * La raíz redirige a /dashboard y no a /cases: es la pantalla de entrada
 * que resume lo que hay (ver modules/dashboard). Con sesión recién
 * creada, /login también lleva ahí.
 */
export const router = createBrowserRouter([
  { path: 'login', element: <LoginPage /> },
  {
    element: <AuthGuard />,
    children: [
      {
        element: <AppShell />,
        children: [
          { index: true, element: <Navigate to="/dashboard" replace /> },
          { path: 'dashboard', element: <DashboardPage /> },
          { path: 'perfil', element: <ProfilePage /> },
          { path: 'ayuda', element: <HelpPage /> },
          { path: 'cases', element: <CasesPage /> },
          { path: 'osint/*', children: osintRoutes },
          { path: 'tracking', element: <TrackingPage /> },
          { path: 'timeline', element: <TimelinePage /> },
          { path: 'reports', element: <ReportsPage /> },
          { path: 'chat', element: <ChatPage /> },
        ],
      },
    ],
  },
])
