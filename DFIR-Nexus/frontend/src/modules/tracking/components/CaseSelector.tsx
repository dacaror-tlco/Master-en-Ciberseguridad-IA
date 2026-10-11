import { useCallback, useEffect, useState } from "react";
import { Select } from "@/shared/ui";
import { listCasesForSelector } from "../api";
import type { CaseOption } from "../types";

export interface CaseSelectorProps {
  value: number | null;
  onChange: (caseId: number | null) => void;
}

export function CaseSelector({ value, onChange }: CaseSelectorProps) {
  const [cases, setCases] = useState<CaseOption[]>([]);
  const [error, setError] = useState<string | undefined>();

  const cargar = useCallback(() => {
    listCasesForSelector()
      .then((lista) => {
        setCases(lista);
        setError(undefined);
      })
      // Antes el fallo se tragaba y decía "Sin casos disponibles": no se
      // distinguía un backend caído de un sistema sin casos.
      .catch(() => setError("No se pudieron cargar los casos."));
  }, []);

  // Se recarga al volver a la pestaña o ventana: un caso recién creado en
  // Casos aparece sin tener que recargar la página entera.
  useEffect(() => {
    cargar();
    window.addEventListener("focus", cargar);
    return () => window.removeEventListener("focus", cargar);
  }, [cargar]);

  return (
    <Select
      label="Caso"
      value={value ?? ""}
      error={error}
      onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
      options={[
        { value: "", label: cases.length ? "Selecciona un caso..." : "Sin casos disponibles" },
        ...cases.map((c) => ({ value: String(c.id), label: `#${c.id} — ${c.nombre} (${c.estado})` })),
      ]}
    />
  );
}
