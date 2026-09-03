"""Agente cognitivo baseado em objetivo e função de utilidade explícita."""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Callable


TARGET_TEMPERATURE = 24.0


@dataclass
class CognitiveDecision:
    state: dict
    plan: str
    actions: list[str]
    utility: float
    reason: str
    evaluated_options: list[dict]
    timestamp: str


class CognitiveAgent:
    """Compara planos, prevê seus efeitos e executa o de maior utilidade."""

    PLANS = (
        ("nao_fazer_nada", ("nao_fazer_nada",), 0.0, 0.0),
        ("apenas_ventilador", ("ligar_ventilador",), 1.2, 0.4),
        ("abrir_janela", ("abrir_janela",), 1.0, 0.0),
        ("janela_e_ventilador", ("abrir_janela", "ligar_ventilador"), 2.0, 0.4),
        ("ar_condicionado", ("fechar_janela", "ligar_ar"), 4.5, 3.0),
    )

    def __init__(self):
        self.last_decision = None

    @staticmethod
    def _boolean(value):
        return value if isinstance(value, bool) else str(value).lower() in ("1", "true", "sim", "aberta")

    def evaluate(self, name, actions, cooling, energy, state):
        temperature = float(state.get("temperatura_atual", 24))
        humidity = float(state.get("umidade_atual", 50))
        light = float(state.get("luminosidade", 0))
        rain = self._boolean(state.get("chuva", False))
        inside = self._boolean(state.get("presenca_interna", False))
        outside = self._boolean(state.get("presenca_externa", False))
        window = self._boolean(state.get("janela_aberta", False))
        ac = self._boolean(state.get("ar_ligado", False))

        predicted = max(TARGET_TEMPERATURE, temperature - cooling) if temperature > TARGET_TEMPERATURE else temperature
        comfort = 20.0 - 4.0 * abs(predicted - TARGET_TEMPERATURE)
        energy_penalty = 2.0 * energy
        utility = comfort - energy_penalty
        reasons = [f"temperatura prevista {predicted:.1f} °C", f"conforto {comfort:.1f}",
                   f"custo de energia -{energy_penalty:.1f}"]

        opens_window = "abrir_janela" in actions
        uses_ac = "ligar_ar" in actions
        if opens_window and rain:
            utility -= 100
            reasons.append("chuva: penalidade -100")
        if opens_window and outside:
            utility -= 100
            reasons.append("presença externa: risco de segurança -100")
        if opens_window and ac and not uses_ac:
            utility -= 100
            reasons.append("conflito com ar já ligado -100")
        if uses_ac and window and "fechar_janela" not in actions:
            utility -= 100
            reasons.append("ar com janela aberta -100")
        if not inside and name not in ("nao_fazer_nada", "ar_condicionado"):
            utility -= 2
            reasons.append("sem presença interna -2")
        if opens_window and light >= 60 and inside:
            utility += 1
            reasons.append("luz natural +1")
        if "ligar_ventilador" in actions and humidity > 70:
            utility += 0.5
            reasons.append("umidade alta +0.5")
        if name == "nao_fazer_nada" and abs(temperature - TARGET_TEMPERATURE) <= 1:
            utility += 3
            reasons.append("temperatura já confortável +3")

        return {
            "opcao": name,
            "acoes": list(actions),
            "temperatura_prevista": round(predicted, 1),
            "utilidade": round(utility, 2),
            "motivo": "; ".join(reasons),
        }

    def decide(self, state, now=None):
        snapshot = dict(state)
        options = [self.evaluate(name, actions, cooling, energy, snapshot)
                   for name, actions, cooling, energy in self.PLANS]
        selected = max(options, key=lambda option: option["utilidade"])
        decision = CognitiveDecision(
            state=snapshot,
            plan=selected["opcao"],
            actions=selected["acoes"],
            utility=selected["utilidade"],
            reason=selected["motivo"],
            evaluated_options=options,
            timestamp=(now or datetime.now()).isoformat(timespec="seconds"),
        )
        self.last_decision = decision
        self._print(decision)
        return decision

    def run(self, state, executor: Callable[[str], object], now=None):
        decision = self.decide(state, now)
        for action in decision.actions:
            executor(action)
        return decision

    def status(self):
        return asdict(self.last_decision) if self.last_decision else None

    @staticmethod
    def _print(decision):
        print("\n=== AGENTE COGNITIVO: OBJETIVO E UTILIDADE ===")
        print("Estado atual:", decision.state)
        for option in decision.evaluated_options:
            print(f"- {option['opcao']}: utilidade={option['utilidade']:.2f} — {option['motivo']}")
        print(f"Escolhida: {decision.plan} ({decision.utility:.2f}) — {decision.reason}")
