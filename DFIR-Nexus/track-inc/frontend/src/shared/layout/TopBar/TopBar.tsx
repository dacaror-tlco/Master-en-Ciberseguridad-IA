import { Icon } from "@/shared/ui/Icon";

/**
 * Barra superior global, altura fija h-16, backdrop-blur.
 *
 * Nota (ver DESIGN_SYSTEM.md §6): el buscador se implementa con un
 * <input> nativo con clases propias, replicando el lenguaje visual de
 * Input pero SIN importar el componente compartido — es una
 * discrepancia conocida y documentada del sistema real, no un patrón a
 * seguir. Se reproduce aquí tal cual para no introducir una
 * "corrección" que el resto del equipo no tiene en su código real.
 */
export function TopBar() {
  return (
    <header className="h-16 flex items-center justify-between px-gutter bg-surface-container-low/80 backdrop-blur-md border-b border-hairline shrink-0">
      <div className="font-headline text-headline-md text-primary md:hidden">NEXUS</div>

      <div className="hidden md:block flex-1 max-w-md">
        <div className="relative">
          <Icon name="search" className="absolute left-3 top-1/2 -translate-y-1/2 text-[16px] text-on-surface-variant" />
          <input
            type="search"
            placeholder="Buscar..."
            disabled
            className="w-full bg-canvas border border-hairline rounded px-9 py-2 font-body text-mono-data text-on-surface placeholder:text-on-surface-variant focus:border-primary focus:ring-1 focus:ring-primary/50 outline-none"
          />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          type="button"
          disabled
          aria-label="Notificaciones"
          className="text-on-surface-variant disabled:opacity-60 disabled:cursor-not-allowed"
        >
          <Icon name="notifications" className="text-[20px]" />
        </button>
        <button
          type="button"
          disabled
          aria-label="Huella"
          className="hidden md:block text-on-surface-variant disabled:opacity-60 disabled:cursor-not-allowed"
        >
          <Icon name="fingerprint" className="text-[20px]" />
        </button>
        <div className="w-8 h-8 rounded-full bg-surface-container-highest flex items-center justify-center">
          <Icon name="person" className="text-[18px] text-on-surface-variant" />
        </div>
      </div>
    </header>
  );
}
