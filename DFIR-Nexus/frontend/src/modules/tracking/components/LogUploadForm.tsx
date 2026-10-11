import { useRef, useState } from "react";
import { Button, Icon, Select } from "@/shared/ui";
import { ZONAS_HORARIAS } from "./formatHora";

export interface LogUploadFormProps {
  /** `zonaHoraria`: en la que están escritas las horas del log ("UTC", "+02:00"...). */
  onAnalyze: (file: File, zonaHoraria: string) => void;
  analyzing?: boolean;
}

export function LogUploadForm({ onAnalyze, analyzing = false }: LogUploadFormProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  // Los logs no suelen decir en qué zona están; lo sabe el perito (la del
  // equipo afectado). Por defecto UTC, que es lo que se asumía antes.
  const [zonaHoraria, setZonaHoraria] = useState("UTC");
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="flex flex-wrap items-end gap-3">
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="flex items-center gap-2 border border-hairline rounded px-3 py-2 font-body text-mono-data text-on-surface-variant hover:text-on-surface hover:border-outline"
      >
        <Icon name="upload_file" className="text-[16px]" />
        {selectedFile ? selectedFile.name : "Seleccionar fichero de log..."}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept=".log,.txt"
        className="hidden"
        onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
      />
      <div className="w-36">
        <Select
          label="Zona del log"
          title="Zona horaria en la que están escritas las horas del log"
          value={zonaHoraria}
          onChange={(e) => setZonaHoraria(e.target.value)}
          options={ZONAS_HORARIAS}
        />
      </div>
      <Button
        icon="search"
        loading={analyzing}
        disabled={!selectedFile}
        onClick={() => selectedFile && onAnalyze(selectedFile, zonaHoraria)}
      >
        Analizar (sin guardar)
      </Button>
    </div>
  );
}
