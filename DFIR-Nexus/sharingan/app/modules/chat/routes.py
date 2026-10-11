"""
Capa HTTP del asistente conversacional.

Un único endpoint, `POST /chat`. No hay `GET /chat/cases` para poblar el
selector: el propietario de `cases` es el Módulo 1 y ya expone `GET /cases`
—el frontend lo consume de ahí, igual que hace el panel de Informes— en vez
de que este backend reivindique una ruta que no le pertenece.

Traducción de errores a HTTP, con el mismo criterio que `reports/routes.py`:
distinguir lo que es culpa de la petición (404) de lo que es una carencia de
configuración del despliegue (503) o un fallo del proveedor de IA (502). Un
502 aquí no es un bug del módulo: es que la respuesta no era utilizable y se
ha preferido no servirla.
"""
import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.chat import service
from app.modules.chat.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def conversar(
    payload: ChatRequest, request: Request, db: Session = Depends(get_db)
) -> ChatResponse:
    try:
        respuesta = service.responder(
            db=db,
            mensaje=payload.mensaje,
            case_id=payload.case_id,
            historial=payload.historial,
            historial_case_id=payload.historial_case_id,
            token=_token(request),
        )
    except service.CaseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except service.ChatConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except (service.ChatUnavailableError, service.ChatResponseError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return ChatResponse(
        respuesta=respuesta.texto,
        fuentes=respuesta.fuentes,
        con_contexto_de_caso=respuesta.con_contexto_de_caso,
        modelo=respuesta.modelo,
        filas_de_contexto=respuesta.filas_de_contexto,
        advertencias=respuesta.advertencias,
        documentacion=respuesta.documentacion,
    )


def _token(request: Request) -> str:
    """El JWT de quien pregunta, para leer el expediente con su identidad.

    Ya está verificado: el router entero depende de `get_current_user`."""
    return request.headers.get("Authorization", "").removeprefix("Bearer ").strip()


def _sse(evento: str, datos: dict) -> str:
    """Un evento del protocolo SSE. `ensure_ascii=False` conserva las tildes."""
    return f"event: {evento}\ndata: {json.dumps(datos, ensure_ascii=False)}\n\n"


@router.post("/stream")
def conversar_en_trozos(payload: ChatRequest, request: Request, db: Session = Depends(get_db)):
    """
    La misma respuesta que `POST /chat`, pero según se escribe.

    Existe por una razón medida: con el modelo local y sin GPU, una pregunta
    sobre un caso tarda del orden de cinco minutos, y hasta ahora la pantalla
    se quedaba en blanco todo ese rato. Los trozos no acortan la espera —eso
    depende de los tokens por segundo del hardware— pero la hacen soportable y,
    sobre todo, distinguen «está trabajando» de «se ha colgado».

    Tres eventos: `trozo` con texto parcial, `fin` con la respuesta ya
    verificada (que es la que debe quedar en pantalla, ver `service._componer`)
    y `error` con el motivo.

    Los errores viajan como evento y no como código HTTP a propósito: la
    cabecera ya se ha enviado en cuanto sale el primer trozo, así que un 502 a
    mitad de emisión no llegaría al cliente. Los fallos que ocurren *antes* de
    empezar —caso inexistente, Ollama apagado— sí podrían ser un código HTTP,
    pero se emiten igual como evento para que la interfaz tenga un solo camino
    de tratamiento.
    """

    def eventos():
        try:
            for tipo, valor in service.responder_en_trozos(
                db=db,
                mensaje=payload.mensaje,
                case_id=payload.case_id,
                historial=payload.historial,
                historial_case_id=payload.historial_case_id,
                token=_token(request),
            ):
                if tipo == "trozo":
                    yield _sse("trozo", {"texto": valor})
                else:
                    yield _sse(
                        "fin",
                        ChatResponse(
                            respuesta=valor.texto,
                            fuentes=valor.fuentes,
                            con_contexto_de_caso=valor.con_contexto_de_caso,
                            modelo=valor.modelo,
                            filas_de_contexto=valor.filas_de_contexto,
                            advertencias=valor.advertencias,
                            documentacion=valor.documentacion,
                        ).model_dump(),
                    )
        except (
            service.CaseNotFoundError,
            service.ChatConfigError,
            service.ChatUnavailableError,
            service.ChatResponseError,
        ) as exc:
            yield _sse("error", {"detail": str(exc)})

    return StreamingResponse(
        eventos(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            # Sin esto, un proxy inverso con buffer (nginx por defecto) retiene
            # los trozos y los entrega juntos al final: el streaming deja de
            # existir sin que nada falle de forma visible.
            "X-Accel-Buffering": "no",
        },
    )
