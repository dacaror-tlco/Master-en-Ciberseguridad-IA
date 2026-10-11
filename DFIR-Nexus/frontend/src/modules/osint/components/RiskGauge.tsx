import { riskLevel } from './riskLevel'

type RiskGaugeProps = {
  score: number
}

/**
 * Puerto directo del gauge SVG del frontend anterior de scam-shield
 * (gaugeSVG en frontend/index.html), con los colores de riskLevel.ts en
 * vez de los tokens propios que tenía la web anterior.
 */
export function RiskGauge({ score }: RiskGaugeProps) {
  const level = riskLevel(score)
  const radius = 42
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - score / 100)

  return (
    <div className="flex flex-col items-center gap-1 shrink-0">
      <svg width="110" height="110" viewBox="0 0 110 110">
        <circle cx="55" cy="55" r={radius} stroke="var(--color-hairline)" strokeWidth="9" fill="none" />
        <circle
          cx="55"
          cy="55"
          r={radius}
          stroke={level.colorVar}
          strokeWidth="9"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 55 55)"
        />
      </svg>
      <div
        className="font-headline-md text-headline-md -mt-16"
        style={{ color: level.colorVar }}
      >
        {score}
      </div>
      <div className="font-label-caps text-label-caps text-on-surface-variant mt-8">{level.label}</div>
    </div>
  )
}
