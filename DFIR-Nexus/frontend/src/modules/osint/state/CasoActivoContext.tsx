import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { casesLookupApi } from '../api/casesLookupApi'
import type { CaseOption } from '../types/case'

/**
 * El expediente de Nexus (`cases.id`) al que se atribuyen los análisis de
 * OSINT, compartido por las nueve pantallas del módulo.
 *
 * **Por qué existe.** Los ocho endpoints de análisis aceptan `case_id` desde
 * el principio y lo guardan en su tabla y en `osint_findings`, que es lo único
 * que leen Informes y Cronología. Pero el frontend nunca lo enviaba: no había
 * dónde elegir el caso. Resultado, `osint_findings.case_id` a NULL en casi
 * todos los análisis y el Anexo B de los informes vacío aunque hubiera trabajo
 * de OSINT hecho — se veía en el panel de inicio como «sin caso asociado».
 *
 * Arreglarlo solo desde «Casos guardados» (con el PATCH de vinculación, que sí
 * existe) deja el trabajo hecho al revés: hay que acordarse de volver a
 * vincular cada análisis después. Lo que faltaba era poder decirlo **antes**,
 * una vez, y que valga para toda la sesión de trabajo.
 *
 * **Por qué aquí y no en cada página.** Un perito trabaja sobre un caso, no
 * sobre un indicador: en una sesión analiza el dominio, la IP, el teléfono y la
 * wallet del mismo expediente. Un selector por pestaña obligaría a repetir la
 * misma elección nueve veces y a acertar las nueve.
 *
 * **Por qué se puede dejar en «ninguno».** Una consulta suelta de reputación no
 * pertenece a ningún expediente todavía, y forzar un caso obligaría a inventar
 * uno. Cuando no hay caso el selector lo dice en voz alta (ver
 * `CasoActivoSelector`), en vez de dejar que se descubra semanas después con un
 * anexo vacío.
 */

const CLAVE_ALMACEN = 'nexus_osint_caso_activo'

type CasoActivoContextValue = {
  /** `null` = análisis sin expediente (el backend guardará `case_id` a NULL). */
  casoActivoId: number | null
  /** El caso elegido, si sigue estando en la lista. */
  casoActivo: CaseOption | null
  casos: CaseOption[]
  cargando: boolean
  /** Por qué no se pudo leer la lista de casos, si es que no se pudo. */
  error: string | null
  elegir: (caseId: number | null) => void
}

const CasoActivoContext = createContext<CasoActivoContextValue | null>(null)

function leerGuardado(): number | null {
  try {
    const guardado = localStorage.getItem(CLAVE_ALMACEN)
    if (!guardado) return null
    const id = Number(guardado)
    return Number.isInteger(id) && id > 0 ? id : null
  } catch {
    // Navegación privada, cuota, almacenamiento bloqueado: se empieza sin caso.
    return null
  }
}

export function CasoActivoProvider({ children }: { children: ReactNode }) {
  const [casoActivoId, setCasoActivoId] = useState<number | null>(leerGuardado)
  const [casos, setCasos] = useState<CaseOption[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelado = false
    casesLookupApi
      .list()
      .then((lista) => {
        if (cancelado) return
        setCasos(lista)
        // Un caso puede haberse cerrado o eliminado desde la última sesión. Se
        // limpia la elección en vez de seguir mandando un `case_id` que el
        // backend rechazaría con un 404 en cada análisis.
        setCasoActivoId((actual) =>
          actual !== null && !lista.some((caso) => caso.id === actual) ? null : actual,
        )
      })
      .catch(() => {
        if (!cancelado) {
          setError('No se ha podido leer la lista de casos (Módulo 1). ¿Está arrancado su backend?')
        }
      })
      .finally(() => {
        if (!cancelado) setCargando(false)
      })
    return () => {
      cancelado = true
    }
  }, [])

  useEffect(() => {
    try {
      if (casoActivoId === null) localStorage.removeItem(CLAVE_ALMACEN)
      else localStorage.setItem(CLAVE_ALMACEN, String(casoActivoId))
    } catch {
      // Sin persistencia la elección dura lo que dure la pestaña: molesto, no grave.
    }
  }, [casoActivoId])

  const elegir = useCallback((caseId: number | null) => setCasoActivoId(caseId), [])

  const casoActivo = useMemo(
    () => casos.find((caso) => caso.id === casoActivoId) ?? null,
    [casos, casoActivoId],
  )

  const value = useMemo(
    () => ({ casoActivoId, casoActivo, casos, cargando, error, elegir }),
    [casoActivoId, casoActivo, casos, cargando, error, elegir],
  )

  return <CasoActivoContext.Provider value={value}>{children}</CasoActivoContext.Provider>
}

export function useCasoActivo() {
  const ctx = useContext(CasoActivoContext)
  if (!ctx) throw new Error('useCasoActivo debe usarse dentro de <CasoActivoProvider>')
  return ctx
}
