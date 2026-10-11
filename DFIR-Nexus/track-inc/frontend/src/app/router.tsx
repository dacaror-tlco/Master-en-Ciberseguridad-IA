import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppShell } from "@/shared/layout/AppShell";
import { CasesPage } from "@/modules/cases/pages";
import { TrackingPage } from "@/modules/tracking/pages";
import { OSINTPage } from "@/modules/osint/pages/OSINTPage";
import { TimelinePage } from "@/modules/timeline/pages/TimelinePage";
import { ReportsPage } from "@/modules/reports/pages/ReportsPage";

export const router = createBrowserRouter([
  {
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/cases" replace /> },
      { path: "cases", element: <CasesPage /> },
      { path: "osint", element: <OSINTPage /> },
      { path: "tracking", element: <TrackingPage /> },
      { path: "timeline", element: <TimelinePage /> },
      { path: "reports", element: <ReportsPage /> },
    ],
  },
]);
