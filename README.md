# Quarto inteligente — agentes cognitivo e adaptativo

O projeto usa Flask e preserva o padrão do sistema original: sensores atualizam
`estado_quarto`, o serviço decide e as ações são enviadas por HTTP às placas.
O modo padrão é `cognitivo`; use `MODO_AGENTE=adaptativo` para selecionar o
agente com aprendizagem já existente.

## PEAS

- **Performance:** conforto térmico e luminoso, segurança e baixo consumo, sem ar
  ligado com janela aberta e sem janela aberta durante chuva.
- **Ambiente:** quarto parcialmente observável, dinâmico e contínuo.
- **Atuadores:** janela, ar-condicionado, ventilador, lâmpada e umidificador.
- **Sensores:** chuva, luminosidade, temperatura, umidade e presenças interna/externa.

## Agentes

O código-base recebido contém um agente reativo no qual regras ligam o ar ou
movem a janela diretamente. O agente cognitivo implementado em
`cognitive_agent.py` não reage com uma regra isolada: ele gera cinco planos,
prevê a temperatura resultante, calcula a utilidade e só então executa o melhor.

```text
utilidade = 20 - 4 × |temperatura prevista - 24| - 2 × consumo
            + bônus de luz/umidade/presença
            - penalidades de chuva, segurança e conflitos
```

Os planos avaliados são: não fazer nada, ventilador, janela, janela com
ventilador e ar-condicionado. Chuva, presença externa ou conflito entre janela
e ar recebem penalidade de 100 pontos. O plano do ar sempre fecha a janela antes
de ligá-lo. Estado, opções, parcelas da utilidade, escolha e motivo são impressos
no terminal e expostos por `GET /interf/agente` e `GET /status`.

O agente adaptativo transforma cada leitura em um estado discreto composto por:
faixa de horário, temperatura, luminosidade, chuva, presenças e umidade. Ele
avalia as 11 ações declaradas em `adaptive_agent.py`. A pontuação é:

```text
utilidade total = preferência inicial + 1,5 × valor Q aprendido
```

As preferências iniciais expressam segurança, conforto e energia: chuva,
presença externa ou conflito janela/ar penalizam abrir a janela em 100 pontos;
ar custa 1,8 ponto; ventilação, iluminação e umidade recebem bônus somente
quando necessários. Todas as parcelas, o motivo e a escolha aparecem no
terminal e em `GET /interf/agente`.

Após uma avaliação, a tabela é atualizada por:

```text
Q(novo) = Q(anterior) + 0,4 × (recompensa - Q(anterior))
```

“Gostei/correto” vale `+1`; rejeição vale `-1`. Uma ação manual oposta à última
decisão (por exemplo, fechar logo após o agente abrir) também gera `-1`. A tabela
fica em `data/q_table.json` e é recarregada ao reiniciar.

## Execução

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
SIMULACAO=1 MODO_AGENTE=cognitivo .venv/bin/python Servidor.py
```

Envie sensores reais ou simulados:

```bash
curl -X POST http://localhost:5050/interf/simular \
  -H 'Content-Type: application/json' \
  -d '{"temperatura":24,"umidade":50,"luminosidade":80,"chuva":false,"presencainterna":true}'
curl -X POST http://localhost:5050/interf/feedback \
  -H 'Content-Type: application/json' -d '{"avaliacao":"nao gostei"}'
curl -X POST http://localhost:5050/interf/acao/fechar_janela
```

Para demonstrar o cenário cognitivo (29 °C, alvo 24 °C, sem chuva e janela
fechada):

```bash
curl -X POST http://localhost:5050/monitoramento \
  -H 'Content-Type: application/json' \
  -d '{"temperatura":29,"umidade":50,"luminosidade":70,"chuva":false,"statusjanela":0,"presencainterna":true,"presencaexterna":false}'
```

O JSON e o terminal mostram as cinco alternativas e suas utilidades. Com os
pesos atuais, o ar-condicionado vence porque alcança 24 °C, apesar do maior
custo energético. Altere chuva para `true` para observar a penalização das
opções que abrem a janela.

Para a apresentação, simule luminosidade alta às 6h (ajustando o relógio do
sistema ou usando o teste), rejeite a abertura três vezes e repita o mesmo
estado. A lista de utilidades mostrará o Q negativo e outra ação será escolhida.
Execute os testes com `python3 -m unittest discover -s tests -v`.
