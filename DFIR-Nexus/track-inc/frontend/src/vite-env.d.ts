/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  /** API de Tracking (misma variable que en el frontend único de development). */
  readonly VITE_TRACKING_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
