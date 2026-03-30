from hypothesis import given, strategies as st
from ejercicio_01 import maximo_basico


@given(st.integers(), st.integers())
def test_maximo_basico_property(a, b):
    # El máximo nunca puede ser menor que los argumentos proporcionados
    resultado = maximo_basico(a, b)
    assert resultado >= a
    assert resultado >= b
    assert resultado == a or resultado == b
