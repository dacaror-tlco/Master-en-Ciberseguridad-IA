import { Icon } from '@/shared/ui'
import { useCasoActivo } from '../state/CasoActivoContext'

/**
 * Elige el expediente al que se atribuyen los análisis que se lancen desde
 * cualquier pestaña de OSINT (ver `state/CasoActivoContext`).
 *
 * Vive en la cabecera del módulo, encima de las pestañas, porque lo que decide
 * aplica a todas: el caso es del trabajo, no de la pantalla.
 *
 * Cuando no hay caso elegido **lo dice, y llamando la atención**. No es
 * decoración: un análisis sin `case_id` no aparece en el informe pericial de
 * ningún caso ni en su cronología, y eso se descubre tarde —al generar el
 * informe y ver el Anexo B vacío— si nada lo avisa en el momento. Se avisa sin
 * bloquear, porque una consulta suelta de reputación es un uso legítimo.
 *
 * Los colores son los del lenguaje ya establecido (ver `shared/ui/Alert`):
 * `tertiary` para lo que reclama atención, `primary` para lo que está
 * correcto, `error` para lo que ha fallado. No se introduce ningún tono nuevo.
 */
export function CasoActivoSelector() {
  const { casoActivoId, casos, cargando, error, elegir } = useCasoActivo()
  const sinCaso = casoActivoId === null

  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-2 px-gutter py-2 border-b border-hairline shrink-0">
      <label
        htmlFor="osint-caso-activo"
        className="flex items-center gap-2 font-label-caps text-label-caps text-on-surface-variant"
      >
        <Icon name="folder_shared" className="text-[16px]" />
        Expediente
      </label>

      <select
        id="osint-caso-activo"
        value={casoActivoId ?? ''}
        disabled={cargando || casos.length === 0}
        onChange={(event) => elegir(event.target.value === '' ? null : Number(event.target.value))}
        className={`bg-surface-container-highest border rounded px-3 py-1.5 font-mono-data text-mono-data text-on-surface min-w-[15rem] max-w-full disabled:opacity-50 ${
          sinCaso ? 'border-tertiary' : 'border-primary'
        }`}
      >
        <option value="">— sin expediente —</option>
        {casos.map((caso) => (
          <option key={caso.id} value={caso.id}>
            #{caso.id} · {caso.nombre}
          </option>
        ))}
      </select>

      {error ? (
        <span className="flex items-center gap-1.5 text-error font-mono-data text-mono-data">
          <Icon name="warning" filled className="text-[16px]" />
          {error}
        </span>
      ) : cargando ? (
        <span className="text-on-surface-variant font-mono-data text-mono-data">cargando casos…</span>
      ) : casos.length === 0 ? (
        <span className="flex items-center gap-1.5 text-on-surface-variant font-mono-data text-mono-data">
          <Icon name="info" className="text-[16px] text-tertiary" />
          No hay casos disponibles. Crea uno en «Casos» para poder atribuirle análisis.
        </span>
      ) : sinCaso ? (
        <span className="flex items-center gap-1.5 text-on-surface font-mono-data text-mono-data">
          <Icon name="info" filled className="text-[16px] text-tertiary" />
          Los análisis no se atribuirán a ningún caso: no saldrán en su informe ni en su cronología.
          Se pueden vincular después en «Casos guardados».
        </span>
      ) : (
        <span className="flex items-center gap-1.5 text-on-surface-variant font-mono-data text-mono-data">
          <Icon name="check_circle" filled className="text-[16px] text-primary" />
          Los análisis nuevos se atribuirán a este expediente.
        </span>
      )}
    </div>
  )
}
