import { useEffect, type ReactNode } from "react";
import { Icon } from "@/shared/ui/Icon";

export interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
}

/**
 * Diálogo superpuesto (crear/editar/confirmar). Cierra con clic en el
 * overlay, con el botón de cabecera, o con Escape. El panel usa
 * nexus-glass-panel + backdrop-blur-md (nivel de elevación más alto que
 * Card). No existe en Casos/code.html — extrapolado del nivel de
 * elevación 2 documentado en DESIGN.md (ver DESIGN_SYSTEM.md §7).
 */
export function Modal({ open, onClose, title, children, footer }: ModalProps) {
  useEffect(() => {
    if (!open) return;
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-canvas/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="nexus-glass-panel backdrop-blur-md rounded-lg w-full max-w-lg mx-4 flex flex-col max-h-[85vh]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-gutter py-4 border-b border-hairline shrink-0">
          <h2 className="font-headline text-headline-md text-on-surface">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            className="text-on-surface-variant hover:text-on-surface"
          >
            <Icon name="close" />
          </button>
        </div>

        <div className="flex-1 overflow-auto px-gutter py-4">{children}</div>

        {footer && <div className="px-gutter py-4 border-t border-hairline shrink-0">{footer}</div>}
      </div>
    </div>
  );
}
