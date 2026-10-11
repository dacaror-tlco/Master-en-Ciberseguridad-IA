import { useState } from "react";
import { Button, Input, Select } from "@/shared/ui";
import type { CaseCreateInput, EstadoCaso } from "../types";

export interface CaseFormProps {
  onSubmit: (input: CaseCreateInput) => void;
  onCancel: () => void;
  submitting?: boolean;
}

const ESTADO_OPTIONS: { value: EstadoCaso; label: string }[] = [
  { value: "abierto", label: "Abierto" },
  { value: "en_progreso", label: "En progreso" },
  { value: "cerrado", label: "Cerrado" },
  { value: "archivado", label: "Archivado" },
];

/**
 * No existe componente Textarea en shared/ui: la descripción se resuelve
 * con un <textarea> nativo replicando las clases de Input, tal como
 * documenta DESIGN_SYSTEM.md §7 que hace el CaseForm real.
 */
export function CaseForm({ onSubmit, onCancel, submitting = false }: CaseFormProps) {
  const [nombre, setNombre] = useState("");
  const [estado, setEstado] = useState<EstadoCaso>("abierto");
  const [responsable, setResponsable] = useState("");
  const [descripcion, setDescripcion] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!nombre.trim()) return;
    onSubmit({ nombre, estado, responsable: responsable || undefined, descripcion: descripcion || undefined });
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <Input label="Nombre del caso" value={nombre} onChange={(e) => setNombre(e.target.value)} required />
      <Select label="Estado" options={ESTADO_OPTIONS} value={estado} onChange={(e) => setEstado(e.target.value as EstadoCaso)} />
      <Input label="Responsable" value={responsable} onChange={(e) => setResponsable(e.target.value)} />
      <div className="flex flex-col gap-1.5">
        <label className="font-label text-label-caps uppercase text-on-surface-variant">Descripción</label>
        <textarea
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
          rows={3}
          className="w-full bg-canvas border border-hairline rounded px-3 py-2 font-body text-mono-data text-on-surface focus:border-primary focus:ring-1 focus:ring-primary/50 outline-none resize-none"
        />
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="ghost" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit" loading={submitting}>
          Crear caso
        </Button>
      </div>
    </form>
  );
}
