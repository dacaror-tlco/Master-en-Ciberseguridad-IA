import { useEffect, useState } from "react";
import { Alert, Button, Card, Modal } from "@/shared/ui";
import { TableWithDrawerLayout } from "@/shared/layout/TableWithDrawerLayout";
import { CaseForm, CaseTable, CASE_STATUS_MAP } from "../components";
import { createCase, listCases, ApiError } from "../api";
import type { Case, CaseCreateInput } from "../types";

export function CasesPage() {
  const [cases, setCases] = useState<Case[]>([]);
  const [selected, setSelected] = useState<Case | undefined>(undefined);
  const [modalOpen, setModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadCases() {
    try {
      const data = await listCases();
      setCases(data);
      setError(null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No se pudieron cargar los casos.");
    }
  }

  useEffect(() => {
    loadCases();
  }, []);

  async function handleCreate(input: CaseCreateInput) {
    setSubmitting(true);
    try {
      await createCase(input);
      setModalOpen(false);
      await loadCases();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No se pudo crear el caso.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <TableWithDrawerLayout
        main={
          <Card
            title="Gestión de casos"
            actions={
              <Button icon="add" size="sm" onClick={() => setModalOpen(true)}>
                Nuevo caso
              </Button>
            }
            className="flex-1"
          >
            {error && (
              <div className="p-gutter pb-0">
                <Alert variant="error">{error}</Alert>
              </div>
            )}
            <CaseTable cases={cases} selectedCaseId={selected?.id} onRowClick={setSelected} />
          </Card>
        }
        drawer={
          selected ? (
            <div className="nexus-glass-panel rounded-lg p-gutter flex flex-col gap-4 overflow-auto">
              <h3 className="font-headline text-headline-md text-on-surface">{selected.nombre}</h3>
              <div className="text-mono-data text-on-surface-variant">
                Estado: <span className="text-on-surface">{CASE_STATUS_MAP[selected.estado].label}</span>
              </div>
              <div className="text-mono-data text-on-surface-variant">
                Responsable: <span className="text-on-surface">{selected.responsable ?? "—"}</span>
              </div>
              <div className="text-mono-data text-on-surface-variant">
                {selected.descripcion || "Sin descripción."}
              </div>
            </div>
          ) : (
            <div className="nexus-glass-panel rounded-lg p-gutter flex items-center justify-center text-on-surface-variant text-mono-data">
              Selecciona un caso para ver su detalle.
            </div>
          )
        }
      />

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Nuevo caso">
        <CaseForm onSubmit={handleCreate} onCancel={() => setModalOpen(false)} submitting={submitting} />
      </Modal>
    </>
  );
}
