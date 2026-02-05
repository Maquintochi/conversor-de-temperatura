ZERO_ABS_C = -273.15
ZERO_ABS_F = -459.67
ZERO_ABS_K = 0.0

class TemperaturaInvalida(ValueError):
    pass

def _valida_c(c: float):
    if c < ZERO_ABS_C:
        raise TemperaturaInvalida(f"Celsius abaixo do zero absoluto: {c}")

def _valida_f(f: float):
    if f < ZERO_ABS_F:
        raise TemperaturaInvalida(f"Fahrenheit abaixo do zero absoluto: {f}")

def _valida_k(k: float):
    if k < ZERO_ABS_K:
        raise TemperaturaInvalida(f"Kelvin abaixo do zero absoluto: {k}")

def c_to_f(c: float):
    _valida_c(c)
    return c * 9/5 + 32

def f_to_c(f: float):
    _valida_f(f)
    return (f - 32) * 5/9

def c_to_k(c: float):
    _valida_c(c)
    return c + 273.15

def k_to_c(k: float):
    _valida_k(k)
    return k - 273.15

def f_to_k(f: float):
    return c_to_k(f_to_c(f))

def k_to_f(k: float):
    return c_to_f(k_to_c(k))

def converter(valor: float, origem: str, destino: str):
    origem = origem.upper()
    destino = destino.upper()

    # Valida mesmo se for igual
    {"C": _valida_c, "F": _valida_f, "K": _valida_k}[origem](valor)

    if origem == destino:
        return valor

    mapa = {
        ("C","F"): c_to_f,
        ("F","C"): f_to_c,
        ("C","K"): c_to_k,
        ("K","C"): k_to_c,
        ("F","K"): f_to_k,
        ("K","F"): k_to_f,
    }
    return mapa[(origem, destino)](valor)
