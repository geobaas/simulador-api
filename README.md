# Simulador de API REST de usuarios

Simulador en Python 3.12 de un endpoint REST `GET /api/v1/usuarios/{id}`.
No necesita servidor ni librerías externas: imita en memoria cómo responde una API real,
con código de estado, cabeceras HTTP y cuerpo JSON, como lo verías en Postman.

## Requisitos

- Python **3.12** o superior (usa la sintaxis `type JSON = ...`)
- Sin dependencias externas

## Ejecutar la demo

```bash
python simulador_api.py
```

Por cada caso muestra:

1. El código Python que hace la llamada
2. El equivalente con `curl`
3. La petición HTTP
4. La respuesta HTTP completa (estado, cabeceras y JSON)
5. Lo que imprime el código

## Casos incluidos

| Caso | Entrada | Resultado |
|------|---------|-----------|
| 1 | `1` | `200 OK`: usuario existente |
| 2 | `3` | `200 OK`: usuario inactivo |
| 3 | `99` | `404 Not Found` |
| 4 | `-5` | `400 Bad Request`: ID negativo |
| 5 | `"abc"` | `400 Bad Request`: ID que no es número |
| 6 | `2`, `tasa_error=1.0` | `500 Internal Server Error` |

## Usarlo desde tu código

```python
from simulador_api import obtener_usuario

respuesta = obtener_usuario(1)
print(respuesta.status_code)   # 200
print(respuesta.json())        # {'data': {'id': 1, 'nombre': 'Ana López', ...}}
print(respuesta.headers)       # Content-Type, Date, X-Request-Id, ...
print(respuesta.como_http())   # respuesta completa en formato HTTP
```

### Parámetros de `obtener_usuario`

| Parámetro | Tipo | Por defecto | Descripción |
|-----------|------|-------------|-------------|
| `user_id` | `int` | — | ID del usuario (entero positivo) |
| `latencia` | `tuple[float, float]` | `(0.05, 0.2)` | Rango en segundos de la demora de red simulada |
| `tasa_error` | `float` | `0.0` | Probabilidad (0 a 1) de devolver un error 500 |

## Ejemplo de respuesta

```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
X-Request-Id: 6f1c...
X-Response-Time: 123.45 ms

{
  "data": {
    "id": 1,
    "nombre": "Ana López",
    "email": "ana@ejemplo.com",
    "activo": true
  }
}
```

Respuesta de error:

```json
{
  "error": {
    "codigo": 404,
    "tipo": "NOT_FOUND",
    "mensaje": "Usuario 99 no encontrado"
  }
}
```
