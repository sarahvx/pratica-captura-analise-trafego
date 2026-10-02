# Resultados dos Experimentos

Esta pasta contém os resultados obtidos durante a execução da prática de captura e análise de tráfego em rede emulada com `netns`, `tc/netem`, PCAP, Prometheus e Grafana.

Foram realizados 16 experimentos (E1–E16), com 5 repetições cada, totalizando 80 execuções.

## Organização

### Resultados principais

- `resultados_completos.csv` — resultados individuais das 80 execuções.
- `resultados_medias.csv` — médias das métricas obtidas em cada experimento.
- `relatorio_experimentos.txt` — resumo automático dos resultados experimentais.

### Análise

A pasta `analise/` contém os arquivos utilizados para a análise comparativa dos experimentos.

- `tabela_completa.csv` — tabela com os resultados utilizados na análise.
- `tabela_principal.csv` — principais métricas de cada experimento.
- `comparacao_trafego_fundo.csv` — comparação entre experimentos com e sem tráfego de fundo.
- `comparacao_sem_com_fundo.csv` — comparações específicas entre condições sem e com tráfego de fundo.
- `relatorio_analise.txt` — análise geral dos resultados.

### Gráficos

Os gráficos gerados automaticamente estão em `analise/`:

- `01_throughput_por_experimento.png` — throughput médio por experimento.
- `02_retransmissoes_por_experimento.png` — retransmissões TCP por experimento.
- `03_fps_por_experimento.png` — FPS do vídeo.
- `04_bitrate_video.png` — bitrate médio do vídeo.
- `05_perda_observada.png` — perda observada nos pontos de captura.
- `06_tamanho_pcap.png` — tamanho dos arquivos PCAP.
- `07_efeito_banda.png` — efeito da largura de banda.
- `08_efeito_atraso.png` — efeito do atraso.
- `09_efeito_perda.png` — efeito da perda de pacotes.

## Matriz dos experimentos

| Experimento | Banda | Atraso | Perda | Tráfego de fundo |
|---|---:|---:|---:|---|
| E1 | 200 Mbps | 0 ms | 0% | Não |
| E2 | 200 Mbps | 0 ms | 0% | Sim |
| E3 | 200 Mbps | 0 ms | 10% | Não |
| E4 | 200 Mbps | 0 ms | 10% | Sim |
| E5 | 200 Mbps | 50 ms | 0% | Não |
| E6 | 200 Mbps | 50 ms | 0% | Sim |
| E7 | 200 Mbps | 50 ms | 10% | Não |
| E8 | 200 Mbps | 50 ms | 10% | Sim |
| E9 | 100 Mbps | 0 ms | 0% | Não |
| E10 | 100 Mbps | 0 ms | 0% | Sim |
| E11 | 100 Mbps | 0 ms | 10% | Não |
| E12 | 100 Mbps | 0 ms | 10% | Sim |
| E13 | 100 Mbps | 50 ms | 0% | Não |
| E14 | 100 Mbps | 50 ms | 0% | Sim |
| E15 | 100 Mbps | 50 ms | 10% | Não |
| E16 | 100 Mbps | 50 ms | 10% | Sim |

Cada experimento foi executado cinco vezes.

## Principais resultados

Nos experimentos com tráfego de fundo e sem perda configurada, o throughput acompanhou aproximadamente a largura de banda definida. Foram obtidas médias de aproximadamente 191 Mbps no E2 (200 Mbps) e 95 Mbps no E10 (100 Mbps).

A presença de 10% de perda provocou uma redução significativa do throughput e aumento das retransmissões TCP. O maior número médio de retransmissões foi observado no E4, com 3374,8 retransmissões.

Os menores throughputs foram observados nos experimentos que combinaram 50 ms de atraso, 10% de perda e tráfego de fundo. O E8 apresentou média de 0,739 Mbps e o E16, 0,733 Mbps.

As métricas registradas pelo FFmpeg permaneceram constantes nos experimentos, com aproximadamente 30 FPS, 1801 frames e bitrate de 1064 kbits/s.

A perda observada foi calculada pela diferença entre a quantidade de pacotes UDP capturados no router e no client1. Essa métrica apresentou 0% em todos os experimentos. Esse resultado representa a diferença entre os dois pontos de captura e não deve ser interpretado isoladamente como prova de ausência de perda no caminho.

## CPU e Prometheus

O Prometheus e o Node Exporter estavam configurados e coletando métricas do host. Entretanto, o histórico disponível não abrangia o período em que os experimentos E1–E16 foram executados.

Por esse motivo, os dados de CPU disponíveis atualmente não foram associados aos experimentos, evitando relacionar medições posteriores às execuções experimentais.

## PCAP

Foram realizadas capturas de tráfego em dois pontos da rede:

- router → interface `r-c1`;
- client1 → interface `c1`.

Os arquivos PCAP foram utilizados para contabilizar os pacotes UDP do fluxo de vídeo e complementar a análise dos experimentos.

As capturas foram realizadas com `tcpdump` utilizando `-s 96`.

## Reprodutibilidade

Os resultados apresentados nesta pasta foram gerados a partir das execuções realizadas no ambiente experimental definido para a prática.

Os arquivos de resultados permitem consultar tanto os dados de cada repetição quanto as médias utilizadas na análise.

Para consultar os resultados resumidos, utilize:

```text
resultados_medias.csv
