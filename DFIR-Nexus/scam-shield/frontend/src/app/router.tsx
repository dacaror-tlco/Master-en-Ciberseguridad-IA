import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AppShell } from '@/shared/layout'
import { osintRoutes } from '@/modules/osint/routes'

/**
 * Único punto que conecta rutas con páginas de módulo, mismo patrón que
 * modulo-casos. AppShell es el layout raíz (sidebar + header + fondos
 * globales); cada módulo aporta sus propias rutas. En esta rama solo
 * /osint es funcional — el resto de módulos vive en otras ramas.
 */
export const router = createBrowserRouter([
  {
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/osint" replace /> },
      { path: 'osint/*', children: osintRoutes },
    ],
  },
])
