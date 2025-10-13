from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
from datetime import datetime


class TimelineEntry(BaseModel):
    """Entrada individual na timeline de clicks"""
    day: str = Field(description="Data no formato YYYY-MM-DD")
    clicks: int = Field(ge=0, description="Número de clicks no dia")
    
    class Config:
        json_schema_extra = {
            "example": {
                "day": "2025-10-13",
                "clicks": 45
            }
        }


class CountryStats(BaseModel):
    """Estatísticas por país"""
    country_code: str = Field(min_length=2, max_length=2, description="Código ISO do país")
    clicks: int = Field(ge=0, description="Total de clicks do país")
    
    class Config:
        json_schema_extra = {
            "example": {
                "country_code": "BR",
                "clicks": 234
            }
        }


class CityStats(BaseModel):
    """Estatísticas por cidade"""
    city: str = Field(description="Nome da cidade")
    clicks: int = Field(ge=0, description="Total de clicks da cidade")
    
    class Config:
        json_schema_extra = {
            "example": {
                "city": "São Paulo",
                "clicks": 156
            }
        }


class RefererStats(BaseModel):
    """Estatísticas de referência"""
    referer: str = Field(description="URL de origem do tráfego")
    clicks: int = Field(ge=0, description="Total de clicks desta origem")
    
    class Config:
        json_schema_extra = {
            "example": {
                "referer": "https://google.com",
                "clicks": 89
            }
        }


# ==================== MAIN RESPONSE MODEL ====================

class URLStatsResponse(BaseModel):
    """
    Resposta completa com estatísticas detalhadas de uma URL encurtada.
    Dados baseados nos últimos 30 dias.
    """
    
    short_code: str = Field(
        min_length=3,
        max_length=12,
        description="Código curto da URL"
    )
    
    total_clicks: int = Field(
        ge=0,
        description="Total de clicks nos últimos 30 dias"
    )
    
    unique_visitors: int = Field(
        ge=0,
        description="Número de visitantes únicos (IPs distintos)"
    )
    
    first_click: Optional[str] = Field(
        None,
        description="Data e hora do primeiro click (formato: DD-MM-YYYY HH24:MI:SS)"
    )
    
    last_click: Optional[str] = Field(
        None,
        description="Data e hora do último click (formato: DD-MM-YYYY HH24:MI:SS)"
    )
    
    timeline: List[TimelineEntry] = Field(
        default_factory=list,
        description="Timeline diária de clicks (últimos 30 dias)"
    )
    
    devices: Dict[str, int] = Field(
        default_factory=dict,
        description="Distribuição de clicks por tipo de dispositivo (mobile, desktop, tablet, bot)"
    )
    
    browsers: Dict[str, int] = Field(
        default_factory=dict,
        description="Distribuição de clicks por navegador (Chrome, Firefox, Safari, etc)"
    )
    
    operating_systems: Dict[str, int] = Field(
        default_factory=dict,
        description="Distribuição de clicks por sistema operacional (Windows, macOS, Linux, iOS, Android)"
    )
    
    top_countries: List[CountryStats] = Field(
        default_factory=list,
        max_length=10,
        description="Top 10 países com mais clicks"
    )
    
    top_cities: List[CityStats] = Field(
        default_factory=list,
        max_length=5,
        description="Top 5 cidades com mais clicks"
    )
    
    top_referers: List[RefererStats] = Field(
        default_factory=list,
        max_length=5,
        description="Top 5 fontes de tráfego (referrers)"
    )
    
    @field_validator('timeline', mode='before')
    @classmethod
    def validate_timeline(cls, v):
        """Garante que timeline seja uma lista"""
        if v is None:
            return []
        if isinstance(v, list):
            return v
        return []
    
    @field_validator('devices', 'browsers', 'operating_systems', mode='before')
    @classmethod
    def validate_dicts(cls, v):
        """Garante que dicionários sejam válidos"""
        if v is None:
            return {}
        if isinstance(v, dict):
            return v
        return {}
    
    @field_validator('top_countries', 'top_cities', 'top_referers', mode='before')
    @classmethod
    def validate_lists(cls, v):
        """Garante que listas sejam válidas"""
        if v is None:
            return []
        if isinstance(v, list):
            return v
        return []
    
    class Config:
        json_schema_extra = {
            "example": {
                "short_code": "abc123",
                "total_clicks": 1543,
                "unique_visitors": 892,
                "first_click": "10-10-2025 14:23:45",
                "last_click": "13-10-2025 10:15:32",
                "timeline": [
                    {"day": "2025-10-13", "clicks": 45},
                    {"day": "2025-10-12", "clicks": 67},
                    {"day": "2025-10-11", "clicks": 89}
                ],
                "devices": {
                    "mobile": 823,
                    "desktop": 645,
                    "tablet": 75
                },
                "browsers": {
                    "Chrome": 892,
                    "Safari": 341,
                    "Firefox": 234,
                    "Edge": 76
                },
                "operating_systems": {
                    "Windows": 645,
                    "iOS": 423,
                    "Android": 400,
                    "macOS": 75
                },
                "top_countries": [
                    {"country_code": "BR", "clicks": 678},
                    {"country_code": "US", "clicks": 445},
                    {"country_code": "PT", "clicks": 234}
                ],
                "top_cities": [
                    {"city": "São Paulo", "clicks": 345},
                    {"city": "Rio de Janeiro", "clicks": 234},
                    {"city": "Belo Horizonte", "clicks": 123}
                ],
                "top_referers": [
                    {"referer": "https://google.com", "clicks": 456},
                    {"referer": "https://facebook.com", "clicks": 234},
                    {"referer": "https://twitter.com", "clicks": 123}
                ]
            }
        }


# ==================== HELPER MODELS ====================

class URLStatsNotFound(BaseModel):
    """Resposta quando URL não é encontrada"""
    detail: str = Field(default="URL statistics not found")
    short_code: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "URL statistics not found",
                "short_code": "abc123"
            }
        }


class URLStatsSummary(BaseModel):
    """
    Versão resumida das estatísticas (sem detalhes granulares)
    Útil para listagens ou dashboards
    """
    short_code: str
    total_clicks: int = Field(ge=0)
    unique_visitors: int = Field(ge=0)
    last_click: Optional[str] = None
    top_country: Optional[str] = Field(None, description="País com mais clicks")
    top_device: Optional[str] = Field(None, description="Dispositivo mais usado")
    
    class Config:
        json_schema_extra = {
            "example": {
                "short_code": "abc123",
                "total_clicks": 1543,
                "unique_visitors": 892,
                "last_click": "13-10-2025 10:15:32",
                "top_country": "BR",
                "top_device": "mobile"
            }
        }