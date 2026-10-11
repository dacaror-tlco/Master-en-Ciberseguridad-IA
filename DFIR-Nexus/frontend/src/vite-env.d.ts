/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_OSINT_API_URL?: string
  readonly VITE_TRACKING_API_URL?: string
  readonly VITE_TIMELINE_API_URL?: string
  readonly VITE_REPORTS_API_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
