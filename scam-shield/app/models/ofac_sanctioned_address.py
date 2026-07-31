"""
Caché local de direcciones cripto sancionadas por la OFAC (Tesoro de EEUU).

La OFAC publica el listado SDN oficial como un XML pesado sin una API
sencilla de consultar por dirección. Usamos en su lugar el espejo
`0xB10C/ofac-sanctioned-digital-currency-addresses` (rama `lists`, se
regenera cada noche desde la fuente oficial vía GitHub Actions), que ya
lo deja en ficheros de texto plano por moneda. Mismo patrón que
`cnmv_warning.py`: caché local que se refresca sola cuando caduca (ver
ofac_service.py).
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OfacSanctionedAddress(Base):
    __tablename__ = "ofac_sanctioned_addresses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    address: Mapped[str] = mapped_column(String, index=True)
    asset: Mapped[str] = mapped_column(String)  # "BTC" | "ETH" | "TRON"
    cached_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
