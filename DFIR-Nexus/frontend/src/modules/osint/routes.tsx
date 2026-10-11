import type { RouteObject } from 'react-router-dom'
import { Navigate } from 'react-router-dom'
import { OsintLayout } from './layout/OsintLayout'
import { DomainAnalysisPage } from './pages/DomainAnalysisPage'
import { EmailAnalysisPage } from './pages/EmailAnalysisPage'
import { WalletAnalysisPage } from './pages/WalletAnalysisPage'
import { TyposquattingPage } from './pages/TyposquattingPage'
import { PhoneAnalysisPage } from './pages/PhoneAnalysisPage'
import { CnmvCheckPage } from './pages/CnmvCheckPage'
import { ImageAnalysisPage } from './pages/ImageAnalysisPage'
import { IpAnalysisPage } from './pages/IpAnalysisPage'
import { MonitoringPage } from './pages/MonitoringPage'
import { SavedCasesPage } from './pages/SavedCasesPage'
import { ReportPage } from './pages/ReportPage'

/**
 * Rutas del módulo OSINT y Fraude, montadas bajo /osint/* por app/router.tsx.
 * OsintLayout aporta la sub-navegación por pestañas.
 */
export const osintRoutes: RouteObject[] = [
  {
    element: <OsintLayout />,
    children: [
      { index: true, element: <Navigate to="domain" replace /> },
      { path: 'domain', element: <DomainAnalysisPage /> },
      { path: 'email', element: <EmailAnalysisPage /> },
      { path: 'wallet', element: <WalletAnalysisPage /> },
      { path: 'typosquatting', element: <TyposquattingPage /> },
      { path: 'phone', element: <PhoneAnalysisPage /> },
      { path: 'cnmv', element: <CnmvCheckPage /> },
      { path: 'image', element: <ImageAnalysisPage /> },
      { path: 'ip', element: <IpAnalysisPage /> },
      { path: 'monitoring', element: <MonitoringPage /> },
      { path: 'cases', element: <SavedCasesPage /> },
      { path: 'report', element: <ReportPage /> },
    ],
  },
]
