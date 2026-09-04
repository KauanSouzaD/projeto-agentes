"""Prevê, de forma aproximada, como o quarto reage a cada ação — usado
tanto pra resolver ambiguidades quanto pra treino offline."""


def prever_estado(estado, acao, temperatura_externa=30.0):
    novo = dict(estado)
    if acao == "abrir_janela":
        novo["janela_aberta"] = True
        novo["temperatura_atual"] += (temperatura_externa - estado["temperatura_atual"]) * 0.3
    elif acao == "fechar_janela":
        novo["janela_aberta"] = False
    elif acao == "ligar_ar":
        novo["ar_ligado"] = True
        novo["temperatura_atual"] -= 2.0
    elif acao == "desligar_ar":
        novo["ar_ligado"] = False
    elif acao == "ligar_ventilador":
        novo["ventilador"] = 1
        novo["temperatura_atual"] -= 0.5
    elif acao == "desligar_ventilador":
        novo["ventilador"] = 0
    elif acao == "ligar_lampada":
        novo["lampada_ligada"] = 1
        novo["luminosidade"] = max(novo["luminosidade"], 70)
    elif acao == "desligar_lampada":
        novo["lampada_ligada"] = 0
    elif acao == "ligar_umidificador":
        novo["umidificador"] = 1
        novo["umidade_atual"] += 3
    elif acao == "desligar_umidificador":
        novo["umidificador"] = 0
    return novo


def avaliar_resultado(estado, temperatura_alvo=24.0, umidade_alvo=50.0):
    """Nota de 'quão bom' é um estado — quanto mais perto do ideal, melhor."""
    conforto = -abs(estado["temperatura_atual"] - temperatura_alvo) * 0.6
    conforto -= abs(estado.get("umidade_atual", umidade_alvo) - umidade_alvo) * 0.1
    energia = -0.5 * (estado.get("ar_ligado", 0) or 0)
    energia -= 0.15 * (estado.get("ventilador", 0) or 0)
    return round(conforto + energia, 3)