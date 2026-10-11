/** Refleja app/schemas/wallet_analysis.py. No se inventa ningún campo. */
import type { RiskFlag } from './domain'

export type WalletInfo = {
  chain: string
  address: string
  n_transactions: number
  total_received: number
  total_sent: number
  balance: number
  first_transaction_at: string | null
  unique_senders_recent: number
  note: string | null
  token: string | null
  evm_network: string | null
  ofac_sanctioned: boolean
}

export type WalletCase = {
  id: number
  created_at: string
  wallet: WalletInfo
  risk_flags: RiskFlag[]
  risk_score: number
  errors: string[]
  analyzed_at: string
}

export type WalletCaseListItem = {
  id: number
  chain: string
  address: string
  risk_score: number
  created_at: string
}

export type ExtractedAddress = {
  address: string
  chain: string
}

export type AddressFormat = {
  chain: string | null
  subtype: string | null
  valid: boolean
}
