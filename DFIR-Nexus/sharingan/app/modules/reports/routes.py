from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.reports import repository, service
from app.modules.reports.ai_narrative import (
    AIConfigError,
    AIResponseError,
    AIUnavailableError,
)
from app.modules.reports.formats import FORMATO_PRINCIPAL, FORMATOS, FormatoInforme
from app.modules.reports.html_builder import CSP_INFORME
from app.modules.reports.schemas import ReportGenerateRequest, ReportOut

router = APIRouter(prefix="/reports", tags=["reports"])
cases_router = APIRouter(prefix="/cases", tags=["reports"])


@router.post("/generate", response_model=ReportOut)
def generate_report(payload: ReportGenerateRequest, db: Session = Depends(get_db)):
    try:
        return service.generate_report(
            db,
            payload.case_id,
            payload.generado_por,
            payload.notas,
            payload.opciones.a_dominio() if payload.opciones else None,
        )
    except service.CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except service.EmptyTimelineError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except service.EmptySelectionError as exc:
        # El caso sí tiene cronología: son las opciones de esta petición las
        # que la dejan vacía. El mensaje dice qué aflojar.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except service.VersionConflictError as exc:
        # Varias generaciones simultáneas del mismo caso se pisaron el número
        # de versión. No es culpa de la petición: reintentarla funciona.
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except AIConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except AIUnavailableError as exc:
        # La IA no está disponible ahora mismo (red, rate limit, 5xx de
        # Anthropic): es un fallo transitorio del proveedor, no del cliente.
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except AIResponseError as exc:
        # La IA respondió, pero con algo que no se puede firmar (truncado,
        # rechazado, o citando eventos inexistentes).
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = repository.get_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"No existe el informe {report_id}")
    return report


@router.get("/{report_id}/download")
def download_report(
    report_id: int,
    formato: FormatoInforme = Query(
        FORMATO_PRINCIPAL,
        description=(
            "Soporte en el que se descarga el informe. El PDF es el documento "
            "firmado; los demás son copias del mismo contenido emitidas a la vez."
        ),
    ),
    db: Session = Depends(get_db),
):
    try:
        report, ruta = service.get_report_file(db, report_id, formato)
    except service.ReportTamperedError as exc:
        # 409 y no 410: el 410 de arriba dice «esta copia no se emitió nunca»,
        # que es una situación normal en los informes antiguos. Esto dice que
        # el fichero almacenado no es el que el informe declara, y quien lo
        # pide tiene que poder distinguir una cosa de la otra.
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except service.ReportFileMissingError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    cabeceras = {}
    huella = service.huella_registrada(report, formato)
    if huella is not None:
        # Publicada para que el destinatario pueda contrastar el fichero por su
        # cuenta (`sha256sum informe.pdf`). Una huella que solo comprueba el
        # servidor no demuestra nada a quien recibe el documento.
        cabeceras["X-Informe-SHA256"] = huella
    if formato is FormatoInforme.HTML:
        # El informe se sirve en línea y desde el mismo origen que la API, y su
        # contenido procede de los Módulos 1 a 4. El escapado es la defensa
        # principal y tiene tests, pero esta política es la que garantiza que
        # un fallo de escapado no se convierta en ejecución: `default-src
        # 'none'` no deja correr ningún script. El documento la lleva además
        # incrustada, para cuando se abra desde disco y no haya cabeceras.
        cabeceras["Content-Security-Policy"] = CSP_INFORME

    return FileResponse(
        ruta,
        media_type=FORMATOS[formato].media_type,
        filename=(
            f"informe_caso_{report.case_id}_v{report.version}.{formato.value}"
        ),
        headers=cabeceras,
        # El HTML existe para leerlo en pantalla: servido como `attachment` el
        # navegador lo descarga y hay que abrirlo a mano, que es justo lo que
        # ese formato venía a evitar. Se sirve en línea. Es seguro porque todo
        # el texto que viene de la base de datos y del LLM pasa por
        # `html.escape` (con test propio) y el documento no incrusta scripts.
        # Los otros tres se descargan: nadie quiere un PDF o un JSON pintado
        # dentro de la pestaña de una API.
        content_disposition_type=(
            "inline" if formato is FormatoInforme.HTML else "attachment"
        ),
    )


@router.get("/{report_id}/prompt")
def download_report_prompt(report_id: int, db: Session = Depends(get_db)):
    """
    Instrucciones literales que se enviaron a la IA para redactar el informe.

    El apartado 8 del documento declara el modelo y la versión de las
    instrucciones; esto es lo que permite comprobar esa declaración en vez de
    tener que creérsela. Se sirve aparte del informe porque no es una copia
    suya: es el registro de cómo se redactó.
    """
    try:
        report, ruta = service.get_report_prompt(db, report_id)
    except service.ReportTamperedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except service.PromptNotStoredError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    cabeceras = {}
    huella = service.huella_registrada(report, service.CLAVE_PROMPT)
    if huella is not None:
        cabeceras["X-Informe-SHA256"] = huella

    return FileResponse(
        ruta,
        media_type="text/plain; charset=utf-8",
        filename=f"instrucciones_caso_{report.case_id}_v{report.version}.txt",
        headers=cabeceras,
    )


@cases_router.get("/{case_id}/reports", response_model=list[ReportOut])
def list_reports_for_case(case_id: int, db: Session = Depends(get_db)):
    return repository.list_reports_for_case(db, case_id)
