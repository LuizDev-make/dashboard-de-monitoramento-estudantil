"""
Serviço de cálculo de distância residência–universidade.

Implementa a fórmula de Haversine para calcular a distância em linha reta
(geodésica) entre duas coordenadas geográficas.

IMPORTANTE: Esta é uma distância em linha reta (estimativa). A distância
real por vias rodoviárias será maior. Não deve ser usada para decisões
que exijam distância exata.

Integração opcional com ViaCEP para consulta de endereço a partir do CEP,
com cache de resultados. A aplicação funciona 100% offline com coordenadas
pré-geradas na base sintética.
"""
import math
from functools import lru_cache
from typing import Optional

from backend.config import VIACEP_ENABLED, UFRPE_LATITUDE, UFRPE_LONGITUDE


# Raio médio da Terra em quilômetros
RAIO_TERRA_KM = 6371.0


def distancia_haversine(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Calcula a distância em linha reta entre dois pontos usando Haversine.

    A fórmula de Haversine calcula a distância do grande círculo entre
    dois pontos na superfície de uma esfera a partir de suas latitudes
    e longitudes.

    Args:
        lat1: Latitude do ponto 1 (graus decimais).
        lon1: Longitude do ponto 1 (graus decimais).
        lat2: Latitude do ponto 2 (graus decimais).
        lon2: Longitude do ponto 2 (graus decimais).

    Returns:
        Distância em quilômetros (float).
    """
    # Converte graus para radianos
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    # Fórmula de Haversine
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return RAIO_TERRA_KM * c


def distancia_ate_ufrpe(latitude: float, longitude: float) -> float:
    """Calcula a distância em linha reta até a UFRPE (campus Dois Irmãos).

    Args:
        latitude: Latitude do ponto de origem (graus decimais).
        longitude: Longitude do ponto de origem (graus decimais).

    Returns:
        Distância em quilômetros até a UFRPE.
    """
    return distancia_haversine(
        latitude, longitude, UFRPE_LATITUDE, UFRPE_LONGITUDE
    )


# Cache de consultas ViaCEP para evitar requisições repetidas
_cache_cep: dict[str, Optional[dict]] = {}


def consultar_cep(cep: str) -> Optional[dict]:
    """Consulta endereço a partir do CEP via ViaCEP (opcional).

    Funciona apenas se VIACEP_ENABLED=true no .env.
    Resultados são cacheados para evitar requisições repetidas.
    Em caso de falha externa, retorna None sem bloquear a aplicação.

    Args:
        cep: CEP no formato XXXXX-XXX ou XXXXXXXX.

    Returns:
        Dicionário com dados do endereço ou None em caso de falha.
    """
    if not VIACEP_ENABLED:
        return None

    # Normaliza CEP
    cep_limpo = cep.replace("-", "").replace(".", "").strip()

    if len(cep_limpo) != 8 or not cep_limpo.isdigit():
        return None

    # Verifica cache
    if cep_limpo in _cache_cep:
        return _cache_cep[cep_limpo]

    try:
        import urllib.request
        import json

        url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
        with urllib.request.urlopen(url, timeout=5) as resp:
            dados = json.loads(resp.read().decode("utf-8"))

        if "erro" in dados:
            _cache_cep[cep_limpo] = None
            return None

        _cache_cep[cep_limpo] = dados
        return dados

    except Exception:
        # Não bloqueia a aplicação em caso de falha externa
        _cache_cep[cep_limpo] = None
        return None
