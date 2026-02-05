import streamlit as st

# ------------------ Lógica de conversão ------------------
ZERO_ABS_C = -273.15
ZERO_ABS_F = -459.67
ZERO_ABS_K = 0.0

class TemperaturaInvalida(ValueError):
    pass

def _valida_c(c: float) -> None:
    if c < ZERO_ABS_C:
        raise TemperaturaInvalida(f"Celsius abaixo do zero absoluto: {c}")

def _valida_f(f: float) -> None:
    if f < ZERO_ABS_F:
        raise TemperaturaInvalida(f"Fahrenheit abaixo do zero absoluto: {f}")

def _valida_k(k: float) -> None:
    if k < ZERO_ABS_K:
        raise TemperaturaInvalida(f"Kelvin abaixo do zero absoluto: {k}")

def c_to_f(c: float) -> float:
    _valida_c(c)
    return c * 9/5 + 32

def f_to_c(f: float) -> float:
    _valida_f(f)
    return (f - 32) * 5/9

def c_to_k(c: float) -> float:
    _valida_c(c)
    return c + 273.15

def k_to_c(k: float) -> float:
    _valida_k(k)
    return k - 273.15

def f_to_k(f: float) -> float:
    return c_to_k(f_to_c(f))

def k_to_f(k: float) -> float:
    return c_to_f(k_to_c(k))

def converter(valor: float, origem: str, destino: str) -> float:
    origem = origem.upper(); destino = destino.upper()
    # valida mesmo quando origem == destino
    {"C": _valida_c, "F": _valida_f, "K": _valida_k}[origem](valor)
    if origem == destino:
        return valor
    mapa = {
        ("C","F"): c_to_f, ("F","C"): f_to_c,
        ("C","K"): c_to_k, ("K","C"): k_to_c,
        ("F","K"): f_to_k, ("K","F"): k_to_f,
    }
    return mapa[(origem, destino)](valor)

# ------------------ UI (única página) ------------------
st.set_page_config(page_title="Conversor de Temperatura", page_icon="🌡️", layout="centered")

st.title("🌡️ Conversor de Temperatura")
st.caption("")

# Entrada do valor e casas decimais
valor = st.number_input("Valor da temperatura", value=25.0, step=0.1, format="%.4f")
casas = st.slider("Casas decimais", 0, 6, 2)

# Botões-lista (radios) lado a lado: origem e destino
col1, col2 = st.columns(2)
with col1:
    origem_label = "Unidade de **origem**"
    origem = st.radio(origem_label, ["Celsius (°C)", "Fahrenheit (°F)", "Kelvin (K)"], index=0, key="origem")
with col2:
    destino_label = "Unidade de **destino**"
    destino = st.radio(destino_label, ["Celsius (°C)", "Fahrenheit (°F)", "Kelvin (K)"], index=1, key="destino")

# Normaliza para C/F/K
abbr = {"Celsius (°C)":"C", "Fahrenheit (°F)":"F", "Kelvin (K)":"K"}
origem_u = abbr[origem]
destino_u = abbr[destino]

# Botão de converter
converter_click = st.button("Converter", type="primary", use_container_width=True)

# Resultado
if converter_click:
    try:
        resultado = converter(valor, origem_u, destino_u)
        st.success(f"{valor:.{casas}f} {origem_u}  =  **{resultado:.{casas}f} {destino_u}**")
    except TemperaturaInvalida as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"Erro inesperado: {e}")

st.divider()
st.markdown(
    """
**Notas**
- Limites físicos: °C ≥ -273.15, °F ≥ -459.67, K ≥ 0.
- Se origem e destino forem iguais, o app apenas valida o valor e retorna o mesmo número.
"""
)
