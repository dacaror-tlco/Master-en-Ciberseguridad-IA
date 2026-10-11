/**
 * Tipos que reflejan exactamente app/schemas/domain_analysis.py del backend.
 * No se inventa ningún campo.
 */

export type RiskFlag = {
  code: string
  description: string
  severity: 'low' | 'medium' | 'high'
}

export type WhoisInfo = {
  registrar: string | null
  creation_date: string | null
  expiration_date: string | null
  domain_age_days: number | null
  country: string | null
  name_servers: string[]
}

export type SSLCertInfo = {
  has_valid_cert: boolean
  issuer: string | null
  issued_date: string | null
  days_since_issued: number | null
  subject_alt_names: string[]
}

export type VirusTotalInfo = {
  malicious_count: number
  suspicious_count: number
  harmless_count: number
  undetected_count: number
  reputation: number
  categories: string[]
}

export type DnsRecords = {
  all_ips: string[]
  mx_hosts: string[]
  txt_records: string[]
  has_spf: boolean
  has_dmarc: boolean
  caa_records: string[]
}

export type CrtShInfo = {
  subdomain_count: number
  subdomains: string[]
  suspected_brand_subdomains: string[]
}

export type WaybackInfo = {
  total_snapshots: number
  first_snapshot: string | null
  last_snapshot: string | null
}

export type AbuseIpInfo = {
  ip_address: string
  abuse_confidence_score: number
  total_reports: number
  is_whitelisted: boolean | null
  is_tor: boolean
  usage_type: string | null
  isp: string | null
  domain: string | null
  country_code: string | null
  last_reported_at: string | null
}

export type IpReputationEntry = {
  ip: string
  abuseipdb: AbuseIpInfo | null
}

export type DomainAnalysisRequest = {
  domain: string
}

export type DomainCase = {
  id: number
  created_at: string
  domain: string
  analyzed_at: string
  whois: WhoisInfo | null
  ssl: SSLCertInfo | null
  virustotal: VirusTotalInfo | null
  resolved_ip: string | null
  abuseipdb: AbuseIpInfo | null
  dns: DnsRecords | null
  ip_reputations: IpReputationEntry[]
  crtsh: CrtShInfo | null
  wayback: WaybackInfo | null
  risk_flags: RiskFlag[]
  risk_score: number
  errors: string[]
}

export type DomainCaseListItem = {
  id: number
  domain: string
  risk_score: number
  analyzed_at: string
  created_at: string
}
