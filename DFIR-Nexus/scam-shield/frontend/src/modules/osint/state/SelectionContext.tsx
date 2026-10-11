import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import type { CaseType } from '../types/report'

const CASE_TYPES: CaseType[] = ['domain', 'email', 'wallet', 'typosquatting', 'phone', 'cnmv', 'image', 'ip']

type Selection = Record<CaseType, Set<number>>

type SelectionContextValue = {
  selected: Selection
  toggle: (type: CaseType, id: number) => void
  totalSelected: number
}

const SelectionContext = createContext<SelectionContextValue | null>(null)

function emptySelection(): Selection {
  return {
    domain: new Set(),
    email: new Set(),
    wallet: new Set(),
    typosquatting: new Set(),
    phone: new Set(),
    cnmv: new Set(),
    image: new Set(),
    ip: new Set(),
  }
}

/**
 * Selección de casos compartida entre "Casos guardados" (donde se marcan)
 * e "Informe" (donde se usan) — puerto de `state.selected` del frontend
 * anterior de scam-shield, ahora como Context en vez de estado global.
 */
export function SelectionProvider({ children }: { children: ReactNode }) {
  const [selected, setSelected] = useState<Selection>(emptySelection)

  const toggle = useCallback((type: CaseType, id: number) => {
    setSelected((prev) => {
      const next = { ...prev, [type]: new Set(prev[type]) }
      if (next[type].has(id)) next[type].delete(id)
      else next[type].add(id)
      return next
    })
  }, [])

  const totalSelected = useMemo(
    () => CASE_TYPES.reduce((total, type) => total + selected[type].size, 0),
    [selected],
  )

  const value = useMemo(() => ({ selected, toggle, totalSelected }), [selected, toggle, totalSelected])

  return <SelectionContext.Provider value={value}>{children}</SelectionContext.Provider>
}

export function useSelection() {
  const ctx = useContext(SelectionContext)
  if (!ctx) throw new Error('useSelection debe usarse dentro de <SelectionProvider>')
  return ctx
}

export { CASE_TYPES }
