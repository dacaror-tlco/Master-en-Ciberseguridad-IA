import { Outlet } from "react-router-dom";
import { SideNav } from "@/shared/layout/SideNav";
import { TopBar } from "@/shared/layout/TopBar";

/**
 * Contenedor raíz de la aplicación. Monta SideNav, TopBar y los 4
 * efectos globales (nexus-canvas, nexus-noise-overlay, nexus-mist-gradient,
 * nexus-scanline) — ver DESIGN_SYSTEM.md §5–6.
 *
 * REGLA DE UNA SOLA INSTANCIA: este es el único componente del código
 * que debe referenciar estas clases nexus-*. Ningún módulo debe volver
 * a declararlas ni crear un fondo alternativo dentro de su página.
 */
export function AppShell() {
  return (
    <div className="nexus-canvas nexus-scrollbars h-screen overflow-hidden flex relative">
      <div className="nexus-scanline" />
      <div className="nexus-mist-gradient absolute inset-0" />
      <div className="nexus-noise-overlay" />

      <SideNav />

      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
