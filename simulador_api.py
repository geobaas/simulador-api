"""Simulador de una API REST de usuarios (Python 3.12).

Uso:
    from simulador_api import obtener_usuario
    respuesta = obtener_usuario(1)
    print(respuesta.status_code)   # 200
    print(respuesta.json())        # {"data": {...}}

Ejecuta `python simulador_api.py` para ver, por cada caso, el código que
hace la llamada, la petición HTTP y la respuesta HTTP completa (estado,
cabeceras y cuerpo JSON), igual que en Postman o en la documentación de una API.
"""

from __future__ import annotations

import json
import random
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from email.utils import format_datetime
from enum import IntEnum

# Alias de tipo con la sintaxis nueva de Python 3.12
type JSON = dict[str, object]

HOST = "api.ejemplo.com"
BASE_PATH = "/api/v1"


class HTTPStatus(IntEnum):
    OK = 200
    BAD_REQUEST = 400
    NOT_FOUND = 404
    INTERNAL_ERROR = 500

    @property
    def frase(self) -> str:
        return {
            200: "OK",
            400: "Bad Request",
            404: "Not Found",
            500: "Internal Server Error",
        }[self.value]


@dataclass(slots=True, frozen=True)
class Usuario:
    id: int
    nombre: str
    email: str
    activo: bool


@dataclass(slots=True, frozen=True)
class RespuestaAPI:
    """Respuesta HTTP simulada: estado + cabeceras + cuerpo JSON."""

    status_code: HTTPStatus
    data: Usuario | None = None
    error: str | None = None
    metodo: str = "GET"
    ruta: str = "/"
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    fecha: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    latencia_ms: float = 0.0

    @property
    def ok(self) -> bool:
        return self.status_code == HTTPStatus.OK

    @property
    def url(self) -> str:
        return f"https://{HOST}{self.ruta}"

    @property
    def headers(self) -> dict[str, str]:
        """Cabeceras HTTP de la respuesta (los metadatos van aquí, no en el JSON)."""
        return {
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": str(len(self.to_json().encode("utf-8"))),
            "Date": format_datetime(self.fecha, usegmt=True),
            "X-Request-Id": self.request_id,
            "X-Response-Time": f"{self.latencia_ms} ms",
        }

    def json(self) -> JSON:
        """Cuerpo de la respuesta como dict (igual que `requests.Response.json()`)."""
        if self.data is not None:
            return {"data": asdict(self.data)}
        return {
            "error": {
                "codigo": int(self.status_code),
                "tipo": self.status_code.name,
                "mensaje": self.error,
            }
        }

    def to_json(self) -> str:
        """Cuerpo de la respuesta como texto JSON."""
        return json.dumps(self.json(), ensure_ascii=False, indent=2)

    def como_http(self) -> str:
        """Respuesta completa tal como viaja por la red."""
        linea_estado = f"HTTP/1.1 {int(self.status_code)} {self.status_code.frase}"
        cabeceras = "\n".join(f"{k}: {v}" for k, v in self.headers.items())
        return f"{linea_estado}\n{cabeceras}\n\n{self.to_json()}"


# "Base de datos" en memoria
_USUARIOS: dict[int, Usuario] = {
    1: Usuario(1, "Ana López", "ana@ejemplo.com", True),
    2: Usuario(2, "Carlos Pérez", "carlos@ejemplo.com", True),
    3: Usuario(3, "María Gómez", "maria@ejemplo.com", False),
}


def obtener_usuario(
    user_id: int,
    *,
    latencia: tuple[float, float] = (0.05, 0.2),
    tasa_error: float = 0.0,
) -> RespuestaAPI:
    """Simula GET /api/v1/usuarios/{user_id}.

    Args:
        user_id: ID del usuario a consultar (entero positivo).
        latencia: Rango (min, max) en segundos de la demora simulada de red.
        tasa_error: Probabilidad (0-1) de simular un error 500 del servidor.

    Returns:
        RespuestaAPI con el usuario (200) o con un mensaje de error (400/404/500).
    """
    ruta = f"{BASE_PATH}/usuarios/{user_id}"
    inicio = time.perf_counter()
    time.sleep(random.uniform(*latencia))

    def responder(status: HTTPStatus, **kwargs) -> RespuestaAPI:
        ms = round((time.perf_counter() - inicio) * 1000, 2)
        return RespuestaAPI(
            status_code=status, metodo="GET", ruta=ruta, latencia_ms=ms, **kwargs
        )

    if random.random() < tasa_error:
        return responder(HTTPStatus.INTERNAL_ERROR, error="Error interno del servidor")

    # bool es subclase de int, por eso se descarta explícitamente
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        return responder(
            HTTPStatus.BAD_REQUEST, error="user_id debe ser un entero positivo"
        )

    usuario = _USUARIOS.get(user_id)
    if usuario is None:
        return responder(HTTPStatus.NOT_FOUND, error=f"Usuario {user_id} no encontrado")

    return responder(HTTPStatus.OK, data=usuario)


# ----------------------------------------------------------------------------
# Demostración por consola
# ----------------------------------------------------------------------------

def _sangrar(texto: str, prefijo: str = "    ") -> str:
    return "\n".join(prefijo + linea if linea else "" for linea in texto.splitlines())


def _mostrar_caso(titulo: str, entrada: object, **opciones) -> None:
    r = obtener_usuario(entrada, **opciones)  # type: ignore[arg-type]

    args = ", ".join([repr(entrada), *(f"{k}={v!r}" for k, v in opciones.items())])
    codigo = (
        "from simulador_api import obtener_usuario\n"
        "\n"
        f"respuesta = obtener_usuario({args})\n"
        "print(respuesta.status_code)\n"
        "print(respuesta.json())"
    )
    peticion = (
        f"{r.metodo} {r.ruta} HTTP/1.1\n"
        f"Host: {HOST}\n"
        "Accept: application/json"
    )
    curl = f"curl -i -H \"Accept: application/json\" {r.url}"

    barra = "=" * 72
    print(barra)
    print(f" {titulo}")
    print(barra)
    print("\n▶ Código (Python)\n")
    print(_sangrar(codigo))
    print("\n▶ Equivalente con curl\n")
    print(_sangrar(curl))
    print("\n▶ Petición HTTP\n")
    print(_sangrar(peticion))
    print("\n◀ Respuesta HTTP\n")
    print(_sangrar(r.como_http()))
    print("\n◀ Salida del código\n")
    print(_sangrar(f"{int(r.status_code)}\n{r.json()}"))
    print()


if __name__ == "__main__":
    # Asegura que los acentos y símbolos se vean bien en la consola de Windows
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    _mostrar_caso("Caso 1 · Usuario existente (200 OK)", 1)
    _mostrar_caso("Caso 2 · Usuario inactivo (200 OK)", 3)
    _mostrar_caso("Caso 3 · Usuario que no existe (404 Not Found)", 99)
    _mostrar_caso("Caso 4 · ID negativo (400 Bad Request)", -5)
    _mostrar_caso("Caso 5 · ID que no es número (400 Bad Request)", "abc")
    _mostrar_caso("Caso 6 · Fallo del servidor (500)", 2, tasa_error=1.0)
