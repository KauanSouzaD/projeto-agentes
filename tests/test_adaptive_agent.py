import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from adaptive_agent import AdaptiveAgent


def morning_state(**changes):
    state = {
        "temperatura_atual": 24, "umidade_atual": 50, "luminosidade": 80,
        "chuva": False, "presenca_interna": True, "presenca_externa": False,
        "janela_aberta": False, "ar_ligado": False, "ventilador": 0,
        "lampada_ligada": 0, "umidificador": 0,
    }
    state.update(changes)
    return state


class AdaptiveAgentTests(unittest.TestCase):
    def test_learns_not_to_open_at_six(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "q.json"
            agent = AdaptiveAgent(path)
            moment = datetime(2026, 8, 28, 6)
            self.assertEqual(agent.decide(morning_state(), moment).action, "abrir_janela")
            for _ in range(3):
                self.assertEqual(agent.decide(morning_state(), moment).action, "abrir_janela")
                agent.feedback(-1)
            self.assertNotEqual(agent.decide(morning_state(), moment).action, "abrir_janela")
            self.assertTrue(json.loads(path.read_text(encoding="utf-8")))
            self.assertEqual(AdaptiveAgent(path).q_table, agent.q_table)

    def test_rain_makes_opening_unsafe(self):
        with tempfile.TemporaryDirectory() as directory:
            agent = AdaptiveAgent(Path(directory) / "q.json")
            decision = agent.decide(morning_state(chuva=True), datetime(2026, 8, 28, 6))
            opening = next(item for item in decision.evaluated_actions if item["acao"] == "abrir_janela")
            self.assertLess(opening["utilidade_total"], -90)
            self.assertEqual(decision.action, "fechar_janela")


if __name__ == "__main__":
    unittest.main()
