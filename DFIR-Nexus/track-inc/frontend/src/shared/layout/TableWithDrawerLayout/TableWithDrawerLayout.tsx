import type { ReactNode } from "react";

export interface TableWithDrawerLayoutProps {
  main: ReactNode;
  drawer?: ReactNode;
}

/**
 * Layout de contenido: zona principal + drawer de detalle opcional.
 * El drawer solo se renderiza si se pasa la prop, y aun así queda oculto
 * bajo xl (1280px) — no hay drawer deslizante para mobile/tablet, es el
 * comportamiento heredado de Casos/code.html (ver DESIGN_SYSTEM.md §6).
 */
export function TableWithDrawerLayout({ main, drawer }: TableWithDrawerLayoutProps) {
  return (
    <div className="h-full overflow-hidden p-gutter flex gap-panel-gap">
      <div className="flex-1 min-w-0 flex flex-col">{main}</div>
      {drawer && <aside className="hidden xl:flex w-96 shrink-0 flex-col">{drawer}</aside>}
    </div>
  );
}
