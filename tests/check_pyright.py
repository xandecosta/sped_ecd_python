import os
import sys

# 1. TESTE DE IMPORTAÇÃO (Deve gerar WARNING - Amarelo)
# Uma biblioteca que NÃO existe no seu ambiente
import biblioteca_inexistente_xyz  # type: ignore (Remova o ignore para ver o alerta)


# 2. TESTE DE TIPAGEM (Deve gerar INFORMATION - Azul - ou ser aceito silenciosamente)
# O Pyright/Pylance é rigoroso com tipos. Aqui forçamos uma incerteza.
def soma_numeros(a: int, b: int) -> int:
    return a + b


# Passando uma string onde deveria ser int (Diagnostic: reportGeneralTypeIssues)
resultado_ruim = soma_numeros(10, "20")  # Deve sinalizar como informação/erro de tipo


# 3. TESTE DE ATRIBUTOS (Deve gerar ERROR ou WARNING)
class Teste:
    def __init__(self):
        self.valor = 10


t = Teste()
print(t.atributo_que_nao_existe)  # Deve avisar que o atributo não existe


# 4. TESTE DE UNUSED (Geralmente esmaecido)
def funcao_nao_utilizada():
    x = 100  # Variavel não utilizada


# 5. TESTE DE IMPORT LOCAL (Deve funcionar SEM erro se o ambiente estiver ok)
try:
    from core.telemetry import TelemetryCollector

    print("Import local da 'core' funcionando!")
except ImportError:
    print("Erro no import local!")

print("Fim do teste de integridade do Pyright")
