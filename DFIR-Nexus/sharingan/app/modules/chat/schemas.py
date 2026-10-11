"""
Contratos de entrada/salida del asistente conversacional.

El backend es **sin estado**: la conversación entera viaja en cada petición
(`historial`). No hay tabla nueva ni migración — es una decisión deliberada,
no una simplificación pendiente. El modelo de datos oficial (CLAUDE.md) no
contempla el chat, y añadirle una tabla obligaría a un acuerdo de equipo
(regla 4) para algo que hoy no aporta: un chat de apoyo al perito no es
material probatorio y no tiene por qué persistir. Si algún día debe quedar
registro de las consultas, esa sí es una decisión de equipo, y entonces se
añade la tabla con su migración.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Mensaje(BaseModel):
    """Un turno de la conversación, tal como lo mantiene el frontend."""

    rol: Literal["usuario", "asistente"]
    contenido: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    #: Pregunta del perito.
    mensaje: str = Field(min_length=1, max_length=8000)
    #: Caso sobre el que se pregunta. Si es `None`, el asistente responde en
    #: modo general (dudas técnicas, ayuda de redacción) y se le prohíbe
    #: explícitamente afirmar nada sobre un caso concreto, porque no ha leído
    #: ninguno.
    case_id: int | None = None
    #: Turnos anteriores, del más antiguo al más reciente. Se recorta al
    #: final para no crecer sin límite.
    historial: list[Mensaje] = Field(default_factory=list, max_length=100)
    #: A qué caso pertenece `historial`. Si no coincide con `case_id`, el
    #: servidor **descarta la conversación anterior** y avisa.
    #:
    #: Existe porque el historial se le reenvía al modelo en cada turno, así
    #: que una conversación sobre el caso 8 arrastrada a una pregunta sobre el
    #: caso 1 mete las evidencias, las IPs y los usuarios del 8 dentro del
    #: prompt del 1. Reproducido: el prompt del caso 1 contenía
    #: `203.0.113.45`, `srv-preprod-01` y `auth.log`, que son del 8.
    #:
    #: La interfaz ya no puede provocarlo (mantiene un hilo por caso), pero el
    #: aislamiento entre casos es la promesa central de este módulo y no puede
    #: depender de que el cliente esté bien escrito. `None` significa «el
    #: historial es del mismo caso», que es lo que asumía la versión anterior.
    historial_case_id: int | None = None


class FuenteCitada(BaseModel):
    """
    Una fila real de la base que el asistente tenía delante al responder.

    Es lo que convierte la respuesta en verificable: el perito puede ir a esa
    tabla y esa fila y comprobarlo por su cuenta.
    """

    #: Referencia con la que aparece en el prompt y en el texto: `EV3`, `TR7`…
    ref: str
    #: Tabla de la que procede (`evidences`, `tracking_events`, …).
    tabla: str
    #: Identificador de la fila en esa tabla.
    fila_id: str
    #: Resumen de una línea, para pintarlo en la interfaz sin otra consulta.
    resumen: str


class ChatResponse(BaseModel):
    respuesta: str
    #: Solo las fuentes que el modelo ha citado de verdad en `respuesta`.
    fuentes: list[FuenteCitada] = Field(default_factory=list)
    #: `True` si la respuesta se apoya en datos de un caso; `False` en modo
    #: general. La interfaz lo usa para no dar a entender que ha consultado
    #: el expediente cuando no lo ha hecho.
    con_contexto_de_caso: bool
    #: Quién ha respondido, con proveedor incluido: `ollama/qwen2.5:3b-instruct`.
    #: Se devuelve para que la interfaz pueda decirlo — no es lo mismo, para
    #: quien firma un peritaje, que la respuesta la haya dado un modelo local
    #: o un servicio externo.
    modelo: str
    #: Cuántas filas del caso se le pasaron al modelo. Un 0 con `case_id`
    #: puesto significa caso vacío, no fallo.
    filas_de_contexto: int
    #: Lo que el perito tiene que saber para valorar esta respuesta: citas
    #: retiradas por no corresponder a ningún registro, colecciones recortadas,
    #: registros no disponibles. Nunca se omite nada en silencio.
    advertencias: list[str] = Field(default_factory=list)
    #: Apartados de la documentación del proyecto que se le pasaron al
    #: modelo, como «Documento › Apartado». Vacío cuando la pregunta no
    #: casaba con ninguno con claridad suficiente, que es lo normal en
    #: preguntas generales. Se publica para que el perito pueda ir a leer
    #: la misma fuente que leyó el asistente.
    documentacion: list[str] = Field(default_factory=list)
