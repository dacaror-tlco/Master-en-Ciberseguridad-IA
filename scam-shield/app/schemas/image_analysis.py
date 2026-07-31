from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.domain_analysis import RiskFlag


class ExifInfo(BaseModel):
    has_exif: bool = False
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    software: Optional[str] = None
    date_taken: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None


class ImageMatch(BaseModel):
    """Otra imagen ya analizada en la herramienta que se parece a esta (posible foto reciclada)."""
    case_id: int
    filename: Optional[str] = None
    similarity_percent: int
    analyzed_at: datetime


class ImageAnalysisResponse(BaseModel):
    filename: Optional[str] = None
    perceptual_hash: str
    exif: ExifInfo
    matches: list[ImageMatch] = []
    reverse_search_links: dict[str, str] = {}
    risk_flags: list[RiskFlag] = []
    risk_score: int = Field(0, ge=0, le=100)
    errors: list[str] = []
    analyzed_at: datetime
    raw_file_sha256: Optional[str] = Field(
        None, description="Huella SHA-256 del archivo original en el momento de la captura (informativa, no se guarda la imagen)"
    )


class ImageCaseResponse(ImageAnalysisResponse):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ImageCaseListItem(BaseModel):
    id: int
    filename: Optional[str] = None
    risk_score: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReverseImageMatch(BaseModel):
    """Una página externa donde SerpApi encontró esta misma imagen (o muy parecida)."""
    url: str
    page_title: Optional[str] = None
    source: Optional[str] = None
    thumbnail_url: Optional[str] = None


class ReverseImageSearchResponse(BaseModel):
    image_case_id: int
    matches: list[ReverseImageMatch] = []
    reverse_search_links: dict[str, str] = {}
    risk_flags: list[RiskFlag] = []
    risk_score: int = Field(0, ge=0, le=100)
    errors: list[str] = []
    analyzed_at: datetime


class ReverseImageSearchCaseResponse(ReverseImageSearchResponse):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class FacialSearchMatch(BaseModel):
    """Una página externa donde PimEyes encontró una cara coincidente."""
    url: str
    page_title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    confidence: Optional[float] = None


class FacialSearchResponse(BaseModel):
    image_case_id: int
    confirmed_legal_basis: bool
    notes: Optional[str] = None
    matches: list[FacialSearchMatch] = []
    risk_flags: list[RiskFlag] = []
    risk_score: int = Field(0, ge=0, le=100)
    errors: list[str] = []
    requested_at: datetime


class FacialSearchCaseResponse(FacialSearchResponse):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
