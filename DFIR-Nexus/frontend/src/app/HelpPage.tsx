import type { ReactNode } from 'react'
import { Alert, Card, Icon } from '@/shared/ui'

/**
 * Ayuda.
 *
 * Es gráfica a propósito, y no por decorar: lo que alguien necesita de esta
 * pantalla es **el recorrido de un expediente**, que es una secuencia real con
 * un orden que importa —sin caso no hay dónde guardar nada, sin tracking la
 * cronología sale vacía—, así que se dibuja como secuencia en vez de contarse en
 * párrafos. Los iconos son los mismos del menú lateral: quien acaba de pulsar
 * «OSINT y Fraude» reconoce su icono aquí sin leer.
 *
 * Los números solo están donde hay orden de verdad. En los bloques de abajo no
 * los hay, y por eso son rejilla y no lista numerada.
 *
 * No enseña la interfaz: enseña por qué la plataforma se comporta como se
 * comporta. Un manual de botones se queda viejo con el primer rediseño; el
 * motivo por el que una evidencia no se edita, no.
 */

type Etapa = {
  icono: string
  titulo: string
  detalle: string
  /** El expediente es la raíz y el informe el final: los dos se pintan distinto. */
  papel?: 'raiz' | 'final'
}

const RECORRIDO: Etapa[] = [
  {
    icono: 'folder_shared',
    titulo: 'Abre el caso',
    detalle: 'Todo lo demás se ata a su número. Sin caso no hay dónde guardar nada.',
    papel: 'raiz',
  },
  {
    icono: 'inventory_2',
    titulo: 'Registra las evidencias',
    detalle: 'Dentro del caso. Cada una recibe su huella SHA-256 al crearse.',
  },
  {
    icono: 'public',
    titulo: 'Analiza los indicadores',
    detalle:
      'Dominios, IPs, correos, teléfonos, carteras. Elige el expediente en la cabecera antes de lanzar el análisis, o el resultado se guarda sin caso.',
  },
  {
    icono: 'radar',
    titulo: 'Sube los registros',
    detalle: 'Los eventos de log, clasificados por severidad. De aquí sale casi toda la cronología.',
  },
  {
    icono: 'timeline',
    titulo: 'Consolida la cronología',
    detalle: 'Ordena lo anterior y cada evento conserva la referencia a su registro de origen.',
  },
  {
    icono: 'description',
    titulo: 'Emite el informe',
    detalle: 'Lee las cinco etapas anteriores. El PDF es el documento que vale.',
    papel: 'final',
  },
]

const REGLAS: { icono: string; titulo: string; texto: string }[] = [
  {
    icono: 'lock',
    titulo: 'Una evidencia no se edita',
    texto:
      'Su hash se calcula una sola vez; si se recalculara en cada cambio dejaría de detectar una modificación. Para corregir un dato, elimínala y registra otra: las dos operaciones quedan en la auditoría.',
  },
  {
    icono: 'history',
    titulo: 'Un informe no se corrige, se reemite',
    texto:
      'Cada emisión es una versión nueva y las anteriores se conservan. Un informe que se puede reescribir después no acredita nada.',
  },
  {
    icono: 'delete',
    titulo: 'Borrar un caso no lo borra',
    texto:
      'Se marca como eliminado y sale de los listados, pero la fila y su historial se quedan. Otros módulos apuntan a él.',
  },
  {
    icono: 'folder_off',
    titulo: 'No hay pantalla de evidencias',
    texto:
      'Se gestionan dentro del caso al que pertenecen, que es como las modela el Módulo 1.',
  },
]

const ASISTENTE: { icono: string; titulo: string; texto: ReactNode }[] = [
  {
    icono: 'shield',
    titulo: 'Las evidencias pueden intentar darle órdenes',
    texto: (
      <>
        El contenido de una evidencia es material bajo análisis, y el asistente tiene instrucciones
        de no obedecerlo.{' '}
        <strong className="text-on-surface">Que las cumpla depende del modelo.</strong> En la prueba
        del 26/09/2026, con siete ataques: el proveedor de API resistió los siete; un modelo local
        de 3 B falló la anulación de instrucciones en la mitad de las pasadas, y uno de 1,5 B
        obedeció en cuatro de siete. Ningún modelo local probado la sostiene.
      </>
    ),
  },
  {
    icono: 'fact_check',
    titulo: 'Las citas se comprueban por código',
    texto: (
      <>
        Cada afirmación lleva la fila de la que sale ([EV3], [TR7]…). Una referencia inventada se
        sustituye por <code>[sin respaldo]</code> con aviso. Funcionó con los dos proveedores,
        incluso cuando el modelo pequeño sí cayó en la inyección.
      </>
    ),
  },
  {
    icono: 'folder_off',
    titulo: 'El aislamiento entre casos no depende del modelo',
    texto: 'Está en el código que arma el expediente: no existe consulta que alcance otro caso.',
  },
  {
    icono: 'chat_bubble',
    titulo: 'La conversación no se guarda',
    texto: 'El historial vive en tu navegador y se pierde al recargar. No escribe en el expediente.',
  },
]

/** Un eslabón del recorrido, con su disco de icono sobre la línea vertical. */
function Eslabon({ etapa, numero, ultimo }: { etapa: Etapa; numero: number; ultimo: boolean }) {
  const esRaiz = etapa.papel === 'raiz'
  const esFinal = etapa.papel === 'final'

  return (
    <li className="relative pl-14 pb-6 last:pb-0">
      {/*
        La línea es un borde del propio <li> y se corta en el último: dibujarla
        como elemento aparte obligaba a calcular su alto, y con textos de dos o
        tres líneas nunca cuadraba.
      */}
      {!ultimo && (
        <span
          aria-hidden
          className="absolute left-[19px] top-10 bottom-0 w-px bg-outline-variant"
        />
      )}

      <span
        aria-hidden
        className={`absolute left-0 top-0 w-10 h-10 rounded-full flex items-center justify-center border ${
          esRaiz || esFinal
            ? 'bg-primary/15 border-primary/40 text-primary'
            : 'bg-surface-container-highest border-hairline text-on-surface-variant'
        }`}
      >
        <Icon name={etapa.icono} filled={esRaiz || esFinal} className="text-[20px]" />
      </span>

      <div className="min-w-0 pt-1">
        <p className="text-on-surface text-sm font-medium">
          <span className="font-mono-data text-on-surface-variant/60 text-xs mr-2">{numero}</span>
          {etapa.titulo}
        </p>
        <p className="text-on-surface-variant text-sm mt-1 max-w-[62ch]">{etapa.detalle}</p>
      </div>
    </li>
  )
}

/** Celda de las dos rejillas: icono, título y una explicación corta. */
function Bloque({ icono, titulo, children }: { icono: string; titulo: string; children: ReactNode }) {
  return (
    <div className="flex gap-3 p-4 rounded border border-hairline bg-surface-container-lowest">
      <Icon name={icono} className="text-tertiary text-[20px] shrink-0 mt-0.5" />
      <div className="min-w-0">
        <p className="text-on-surface text-sm font-medium">{titulo}</p>
        <p className="text-on-surface-variant text-sm mt-1">{children}</p>
      </div>
    </div>
  )
}

export function HelpPage() {
  return (
    <div className="h-full overflow-y-auto p-gutter flex flex-col gap-panel-gap [&>*]:shrink-0">
      <div>
        <h1 className="font-headline text-headline-md text-on-surface">Ayuda</h1>
        <p className="font-body-md text-body-md text-on-surface-variant text-sm mt-1 max-w-[62ch]">
          El recorrido de un expediente y por qué la plataforma se comporta como se comporta.
        </p>
      </div>

      <Card title="El recorrido de un expediente" subtitle="El orden importa: cada etapa alimenta la siguiente">
        <div className="p-6">
          <ol className="list-none">
            {RECORRIDO.map((etapa, indice) => (
              <Eslabon
                key={etapa.titulo}
                etapa={etapa}
                numero={indice + 1}
                ultimo={indice === RECORRIDO.length - 1}
              />
            ))}
          </ol>
          <p className="text-on-surface-variant text-sm mt-2 pl-14 max-w-[62ch]">
            El <span className="text-primary">Asistente</span> puede entrar en cualquier punto:
            responde sobre el caso que tengas seleccionado y cita la fila de la que sale cada
            afirmación.
          </p>
        </div>
      </Card>

      <Card title="Lo que la plataforma no te deja hacer" subtitle="No son limitaciones: son la cadena de custodia">
        <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-3">
          {REGLAS.map(({ icono, titulo, texto }) => (
            <Bloque key={titulo} icono={icono} titulo={titulo}>
              {texto}
            </Bloque>
          ))}
        </div>
      </Card>

      <Card title="Comprobar que un PDF es el que se emitió">
        <div className="p-6 flex flex-col gap-3">
          <p className="text-on-surface-variant text-sm max-w-[62ch]">
            El panel de cada informe muestra la huella SHA-256 del PDF. Descarga el fichero y
            compara:
          </p>
          <pre className="font-mono-data text-xs bg-canvas border border-hairline rounded p-3 overflow-x-auto text-on-surface">
{`sha256sum informe_caso_8_v1.pdf                        # Linux, macOS
Get-FileHash informe_caso_8_v1.pdf -Algorithm SHA256   # Windows`}
          </pre>
          <p className="text-on-surface-variant text-sm max-w-[62ch]">
            Si no coincide, el fichero que tienes no es el que emitió la plataforma. En el mismo
            panel, <span className="text-primary">Ver las instrucciones que se enviaron a la IA</span>{' '}
            descarga el texto literal con el que se redactó, para poder comprobar lo que declara el
            apartado 8 en vez de creérselo.
          </p>
        </div>
      </Card>

      <Card title="Lo que conviene saber del asistente">
        <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-3">
          {ASISTENTE.map(({ icono, titulo, texto }) => (
            <Bloque key={titulo} icono={icono} titulo={titulo}>
              {texto}
            </Bloque>
          ))}
        </div>
      </Card>

      <Card title="Si una pantalla sale vacía">
        <div className="p-6 flex flex-col gap-3">
          <p className="text-on-surface-variant text-sm max-w-[62ch]">
            NEXUS son cinco backends independientes, uno por módulo. Que una pantalla no traiga datos
            casi nunca significa que no haya datos: significa que ese backend no está respondiendo.
            Las demás pantallas seguirán funcionando, que es justo lo que hace difícil darse cuenta.
          </p>
          <Alert variant="info">
            En desarrollo, entra por <code className="font-mono-data">localhost</code> y nunca por{' '}
            <code className="font-mono-data">127.0.0.1</code>: para el navegador son orígenes
            distintos y los backends solo autorizan el primero. Por ahí no responde ninguno.
          </Alert>
        </div>
      </Card>
    </div>
  )
}
