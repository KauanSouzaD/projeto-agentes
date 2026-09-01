"""Estado compartilhado e configuração do quarto inteligente."""

import os

placas_registradas = {}

estado_quarto = {
    "modo_agente": os.getenv("MODO_AGENTE", "adaptativo"),
    "temperatura_atual": 24.0,
    "umidade_atual": 50.0,
    "luminosidade": 0.0,
    "chuva": False,
    "presenca_interna": False,
    "presenca_externa": False,
    "janela_aberta": 0,
    "ar_ligado": 0,
    "ventilador": 0,
    "umidificador": 0,
    "lampada_ligada": 0,
    "dormir": 0,
    "temperatura_limite": 28.0,
}

SIMULACAO = os.getenv("SIMULACAO", "0") == "1"
