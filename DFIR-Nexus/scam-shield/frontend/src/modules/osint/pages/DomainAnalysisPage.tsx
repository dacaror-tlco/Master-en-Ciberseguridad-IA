import { useState } from 'react'
import { Alert, Button, Card, Input } from '@/shared/ui'
import { ApiError } from '../api/httpClient'
import { domainApi } from '../api/domainApi'
import type { DomainCase } from '../types/domain'
import { RiskGauge } from '../components/RiskGauge'
import { KVTable } from '../components/KVTable'
import { FlagsTable } from '../components/FlagsTable'

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return typeof error.detail === 'string' ? error.detail : 'La API rechazó la solicitud.'
  }
  return 'No se ha podido conectar con el backend.'
}

/**
 * Panel de Análisis de dominio. Página de referencia del puerto a Nexus:
 * fija el patrón (formulario en un Card + resultado en otro Card, con
 * RiskGauge/KVTable/FlagsTable) que replican el resto de paneles OSINT.
 * Datos reales de /analysis/domain (app/api/routes/analysis.py) — sin mocks.
 */
export function DomainAnalysisPage() {
  const [domain, setDomain] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<DomainCase | null>(null)

  const handleAnalyze = async () => {
    const trimmed = domain.trim()
    if (!trimmed) {
      setError('Escribe un dominio primero.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const data = await domainApi.analyze(trimmed)
      setResult(data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const otherIps = result?.ip_reputations.filter((entry) => entry.ip !== result.resolved_ip) ?? []

  return (
    <div className="h-full overflow-auto p-gutter flex flex-col gap-panel-gap">
      <Card
        title="Análisis de dominio"
        subtitle="WHOIS, certificado SSL, VirusTotal, AbuseIPDB, DNS, crt.sh y Wayback Machine de un dominio sospechoso."
      >
        <div className="p-6 flex flex-col gap-4">
          <div className="flex gap-3 items-end flex-wrap">
            <div className="flex-1 min-w-[240px]">
              <Input
                label="Dominio"
                icon="language"
                placeholder="ejemplo-sospechoso.com"
                value={domain}
                onChange={(event) => setDomain(event.target.value)}
                onKeyDown={(event) => event.key === 'Enter' && handleAnalyze()}
              />
            </div>
            <Button variant="primary" loading={loading} onClick={handleAnalyze}>
              Analizar dominio
            </Button>
          </div>
          {error && <Alert variant="error">{error}</Alert>}
        </div>
      </Card>

      {result && (
        <Card>
          <div className="p-6 flex gap-6 items-start flex-wrap">
            <RiskGauge score={result.risk_score} />
            <div className="flex-1 min-w-[280px]">
              <div className="font-headline-md text-headline-md text-on-surface mb-4 break-all">
                Caso #{result.id} — {result.domain}
              </div>

              <span className="font-label-caps text-label-caps text-on-surface-variant">WHOIS</span>
              <KVTable
                rows={[
                  ['Registrador', result.whois?.registrar],
                  ['Fecha de registro', result.whois?.creation_date],
                  ['Antigüedad (días)', result.whois?.domain_age_days],
                  ['País', result.whois?.country],
                ]}
              />

              <span className="font-label-caps text-label-caps text-on-surface-variant">Certificado SSL</span>
              <KVTable
                rows={[
                  ['Válido', result.ssl ? (result.ssl.has_valid_cert ? 'Sí' : 'No') : null],
                  ['Emisor', result.ssl?.issuer],
                  ['Días desde emisión', result.ssl?.days_since_issued],
                ]}
              />

              {result.virustotal && (
                <>
                  <span className="font-label-caps text-label-caps text-on-surface-variant">VirusTotal</span>
                  <KVTable
                    rows={[
                      ['Motores: malicioso', result.virustotal.malicious_count],
                      ['Motores: sospechoso', result.virustotal.suspicious_count],
                      ['Sin detección', result.virustotal.undetected_count],
                      ['Categorías', result.virustotal.categories.join(', ')],
                    ]}
                  />
                </>
              )}

              {result.resolved_ip && (
                <>
                  <span className="font-label-caps text-label-caps text-on-surface-variant">
                    IP resuelta{result.abuseipdb ? ' — reputación (AbuseIPDB)' : ''}
                  </span>
                  <KVTable
                    rows={[
                      ['IP', result.resolved_ip],
                      ...(result.abuseipdb
                        ? ([
                            ['Puntuación de abuso', `${result.abuseipdb.abuse_confidence_score}/100`],
                            ['Nº de reportes', result.abuseipdb.total_reports],
                            ['ISP', result.abuseipdb.isp],
                            ['Nodo Tor', result.abuseipdb.is_tor ? 'Sí' : 'No'],
                          ] as [string, string][])
                        : []),
                    ]}
                  />
                </>
              )}

              {otherIps.length > 0 && (
                <>
                  <span className="font-label-caps text-label-caps text-on-surface-variant">
                    Otras IPs ({otherIps.length})
                  </span>
                  <KVTable
                    rows={otherIps.map(
                      (entry) =>
                        [
                          entry.ip,
                          entry.abuseipdb
                            ? `${entry.abuseipdb.abuse_confidence_score}/100 de abuso (${entry.abuseipdb.total_reports} reportes)`
                            : 'sin datos AbuseIPDB',
                        ] as [string, string],
                    )}
                  />
                </>
              )}

              {result.dns && (
                <>
                  <span className="font-label-caps text-label-caps text-on-surface-variant">DNS</span>
                  <KVTable
                    rows={[
                      ['Servidores de correo (MX)', result.dns.mx_hosts.length ? result.dns.mx_hosts.join(', ') : '—'],
                      ['SPF configurado', result.dns.mx_hosts.length ? (result.dns.has_spf ? 'Sí' : 'No') : 'N/A (sin MX)'],
                      ['DMARC configurado', result.dns.mx_hosts.length ? (result.dns.has_dmarc ? 'Sí' : 'No') : 'N/A (sin MX)'],
                      ['Registros CAA', result.dns.caa_records.length || 'Ninguno'],
                    ]}
                  />
                </>
              )}

              {result.crtsh && (
                <>
                  <span className="font-label-caps text-label-caps text-on-surface-variant">
                    Subdominios relacionados (crt.sh)
                  </span>
                  <KVTable
                    rows={[
                      ['Subdominios encontrados', result.crtsh.subdomain_count],
                      ['Ejemplos', result.crtsh.subdomains.slice(0, 8).join(', ') || '—'],
                    ]}
                  />
                  {result.crtsh.suspected_brand_subdomains.length > 0 && (
                    <Alert variant="error">
                      Mencionan una marca conocida sin pertenecerle:{' '}
                      {result.crtsh.suspected_brand_subdomains.join(', ')}
                    </Alert>
                  )}
                </>
              )}

              {result.wayback && (
                <>
                  <span className="font-label-caps text-label-caps text-on-surface-variant">
                    Historial (Wayback Machine)
                  </span>
                  <KVTable
                    rows={[
                      ['Capturas totales', result.wayback.total_snapshots],
                      ['Primera captura', result.wayback.first_snapshot],
                      ['Última captura', result.wayback.last_snapshot],
                    ]}
                  />
                </>
              )}

              <span className="font-label-caps text-label-caps text-on-surface-variant">Señales</span>
              <div className="mt-2">
                <FlagsTable flags={result.risk_flags} />
              </div>

              {result.errors.length > 0 && <Alert variant="info">{result.errors.join(' · ')}</Alert>}
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
