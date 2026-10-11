import { Link, useLocation } from "react-router-dom";
import { Icon } from "@/shared/ui/Icon";

interface NavItem {
  label: string;
  icon: string;
  path: string | null;
}

// Orden fijo. Solo los que tienen path no nulo son clicables.
const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", icon: "dashboard", path: null },
  { label: "Casos", icon: "folder_managed", path: "/cases" },
  { label: "Evidencias", icon: "fingerprint", path: "/cases" },
  { label: "OSINT y Fraude", icon: "public", path: "/osint" },
  { label: "Tracking Post-Incidente", icon: "history_edu", path: "/tracking" },
  { label: "Línea Temporal", icon: "timeline", path: "/timeline" },
  { label: "Informes", icon: "description", path: "/reports" },
  { label: "Configuración", icon: "settings", path: null },
];

/**
 * Sidebar compartido por toda la app. Ancho fijo w-64, oculto bajo md
 * (no hay alternativa mobile). Solo un ítem activo a la vez: el primer
 * match de .find() gana, para que Casos/Evidencias (misma ruta) no se
 * resalten simultáneamente (ver DESIGN_SYSTEM.md §6).
 */
export function SideNav() {
  const location = useLocation();
  const activeItem = NAV_ITEMS.find((item) => item.path && location.pathname.startsWith(item.path));

  return (
    <nav className="hidden md:flex w-64 h-full flex-col bg-surface-container-low border-r border-hairline shrink-0">
      <div className="flex items-center gap-3 px-gutter py-margin-safe">
        <Icon name="hub" filled className="text-primary text-[28px]" />
        <div>
          <div className="font-headline text-headline-md text-on-surface leading-none">NEXUS</div>
          <div className="text-mono-data text-on-surface-variant">Forensic Analyst</div>
        </div>
      </div>

      <div className="px-gutter mb-4">
        <Link
          to="/cases"
          className="flex items-center justify-center gap-2 w-full rounded bg-primary text-on-primary font-label text-label-caps uppercase py-3 hover:bg-primary/90"
        >
          <Icon name="add" className="text-[16px]" />
          Nueva investigación
        </Link>
      </div>

      <ul className="flex-1 overflow-auto px-2">
        {NAV_ITEMS.map((item) => {
          const isActive = activeItem?.label === item.label;
          const isDisabled = item.path === null;

          const content = (
            <>
              <Icon name={item.icon} filled={isActive} className="text-[20px]" />
              <span className="font-label text-label-caps uppercase">{item.label}</span>
            </>
          );

          if (isDisabled) {
            return (
              <li key={item.label}>
                <span className="flex items-center gap-3 px-4 py-2.5 opacity-40 cursor-not-allowed">{content}</span>
              </li>
            );
          }

          return (
            <li key={item.label}>
              <Link
                to={item.path!}
                className={`flex items-center gap-3 px-4 py-2.5 rounded transition-all ${
                  isActive
                    ? "text-primary border-l-2 border-primary bg-secondary-container/10 translate-x-1"
                    : "text-on-surface-variant border-l-2 border-transparent hover:text-on-surface"
                }`}
              >
                {content}
              </Link>
            </li>
          );
        })}
      </ul>

      <div className="px-gutter py-4 border-t border-hairline">
        <span className="flex items-center gap-3 px-4 py-2 opacity-60 cursor-not-allowed">
          <Icon name="help" className="text-[20px]" />
          <span className="font-label text-label-caps uppercase">Ayuda</span>
        </span>
        <span className="flex items-center gap-3 px-4 py-2 opacity-60 cursor-not-allowed">
          <Icon name="logout" className="text-[20px]" />
          <span className="font-label text-label-caps uppercase">Cerrar sesión</span>
        </span>
      </div>
    </nav>
  );
}
