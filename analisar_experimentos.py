#!/usr/bin/env python3

import csv
import os
import re
import subprocess
from collections import defaultdict

RESULTADOS_DIR = "./resultados"
LOGS_DIR = "./logs"
CAPTURAS_DIR = "./capturas"

EXPERIMENTOS = {
    "E1":  (200, 0, 0, "sem"),
    "E2":  (200, 0, 0, "com"),
    "E3":  (200, 0, 10, "sem"),
    "E4":  (200, 0, 10, "com"),
    "E5":  (200, 50, 0, "sem"),
    "E6":  (200, 50, 0, "com"),
    "E7":  (200, 50, 10, "sem"),
    "E8":  (200, 50, 10, "com"),
    "E9":  (100, 0, 0, "sem"),
    "E10": (100, 0, 0, "com"),
    "E11": (100, 0, 10, "sem"),
    "E12": (100, 0, 10, "com"),
    "E13": (100, 50, 0, "sem"),
    "E14": (100, 50, 0, "com"),
    "E15": (100, 50, 10, "sem"),
    "E16": (100, 50, 10, "com"),
}

REPETICOES = 5


def numero(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def ler_iperf3(caminho):
    if not os.path.exists(caminho):
        return None, None

    with open(caminho, "r", errors="ignore") as arquivo:
        texto = arquivo.read()

    linhas = texto.splitlines()

    sender_linha = None

    for linha in reversed(linhas):
        if "sender" in linha:
            sender_linha = linha
            break

    if not sender_linha:
        return None, None

    padrao = re.search(
        r"\]\s+\S+-\S+\s+sec\s+.*?"
        r"([\d.]+)\s+(Kbits/sec|Mbits/sec|Gbits/sec)"
        r"\s+(\d+)\s+sender",
        sender_linha
    )

    if not padrao:
        return None, None

    valor = float(padrao.group(1))
    unidade = padrao.group(2)
    retransmissoes = int(padrao.group(3))

    if unidade == "Kbits/sec":
        throughput_mbps = valor / 1000
    elif unidade == "Mbits/sec":
        throughput_mbps = valor
    elif unidade == "Gbits/sec":
        throughput_mbps = valor * 1000
    else:
        throughput_mbps = None

    return throughput_mbps, retransmissoes


def ler_ffmpeg(caminho):
    if not os.path.exists(caminho):
        return None, None, None

    with open(caminho, "r", errors="ignore") as arquivo:
        texto = arquivo.read()

    frames = re.findall(r"frame=\s*(\d+)", texto)
    fps = re.findall(r"fps=\s*([\d.]+)", texto)
    bitrate = re.findall(r"bitrate=\s*([\d.]+)kbits/s", texto)

    frame_final = int(frames[-1]) if frames else None
    fps_final = float(fps[-1]) if fps else None
    bitrate_final = float(bitrate[-1]) if bitrate else None

    return frame_final, fps_final, bitrate_final


def contar_pacotes_video(caminho):
    if not os.path.exists(caminho):
        return None, None

    tamanho = os.path.getsize(caminho)

    comando = [
        "tcpdump",
        "-nn",
        "-r",
        caminho,
        "udp",
        "port",
        "1234"
    ]

    try:
        resultado = subprocess.run(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )

        linhas = [
            linha for linha in resultado.stdout.splitlines()
            if linha.strip()
        ]

        return len(linhas), tamanho

    except Exception:
        return None, tamanho


def calcular_perda(router, client):
    if router is None or client is None:
        return None

    if router <= 0:
        return None

    perda = ((router - client) / router) * 100

    if perda < 0:
        perda = 0

    return perda


def media(valores):
    valores = [
        float(v)
        for v in valores
        if v is not None
    ]

    if not valores:
        return None

    return sum(valores) / len(valores)


def minimo(valores):
    valores = [
        float(v)
        for v in valores
        if v is not None
    ]

    return min(valores) if valores else None


def maximo(valores):
    valores = [
        float(v)
        for v in valores
        if v is not None
    ]

    return max(valores) if valores else None


def fmt(valor, casas=2):
    if valor is None:
        return "N/A"

    return f"{valor:.{casas}f}"


def analisar():
    os.makedirs(RESULTADOS_DIR, exist_ok=True)

    resultados = []

    print("=" * 70)
    print("ANÁLISE DOS EXPERIMENTOS")
    print("=" * 70)

    for experimento, config in EXPERIMENTOS.items():

        banda, atraso, perda_configurada, fundo = config

        print(f"\nAnalisando {experimento}...")

        for repeticao in range(1, REPETICOES + 1):

            base = f"{experimento}_R{repeticao}"

            iperf_path = os.path.join(
                LOGS_DIR,
                f"{base}_iperf3.log"
            )

            ffmpeg_path = os.path.join(
                LOGS_DIR,
                f"{base}_ffmpeg.log"
            )

            router_pcap = os.path.join(
                CAPTURAS_DIR,
                f"{base}_router.pcap"
            )

            client_pcap = os.path.join(
                CAPTURAS_DIR,
                f"{base}_client1.pcap"
            )

            throughput, retrans = ler_iperf3(iperf_path)

            frames, fps, bitrate = ler_ffmpeg(ffmpeg_path)

            pacotes_router, tamanho_router = contar_pacotes_video(
                router_pcap
            )

            pacotes_client, tamanho_client = contar_pacotes_video(
                client_pcap
            )

            perda_observada = calcular_perda(
                pacotes_router,
                pacotes_client
            )

            resultado = {
                "Experimento": experimento,
                "Repeticao": repeticao,
                "Banda_Mbps": banda,
                "Atraso_ms": atraso,
                "Perda_configurada_percentual": perda_configurada,
                "Fundo": fundo,
                "Throughput_iperf_Mbps": throughput,
                "Retransmissoes_iperf": retrans,
                "FPS": fps,
                "Frames": frames,
                "Bitrate_video_kbits": bitrate,
                "Pacotes_video_Router": pacotes_router,
                "Pacotes_video_Client1": pacotes_client,
                "Perda_observada_percentual": perda_observada,
                "Tamanho_PCAP_Router_bytes": tamanho_router,
                "Tamanho_PCAP_Client1_bytes": tamanho_client,
            }

            resultados.append(resultado)

            print(
                f"  R{repeticao}: "
                f"throughput={fmt(throughput)} Mbps | "
                f"frames={frames if frames is not None else 'N/A'} | "
                f"perda={fmt(perda_observada)}%"
            )

    arquivo_completo = os.path.join(
        RESULTADOS_DIR,
        "resultados_completos.csv"
    )

    campos = [
        "Experimento",
        "Repeticao",
        "Banda_Mbps",
        "Atraso_ms",
        "Perda_configurada_percentual",
        "Fundo",
        "Throughput_iperf_Mbps",
        "Retransmissoes_iperf",
        "FPS",
        "Frames",
        "Bitrate_video_kbits",
        "Pacotes_video_Router",
        "Pacotes_video_Client1",
        "Perda_observada_percentual",
        "Tamanho_PCAP_Router_bytes",
        "Tamanho_PCAP_Client1_bytes",
    ]

    with open(
        arquivo_completo,
        "w",
        newline="",
        encoding="utf-8"
    ) as arquivo:

        escritor = csv.DictWriter(
            arquivo,
            fieldnames=campos
        )

        escritor.writeheader()

        for resultado in resultados:
            escritor.writerow(resultado)

    medias = []

    for experimento, config in EXPERIMENTOS.items():

        registros = [
            r for r in resultados
            if r["Experimento"] == experimento
        ]

        banda, atraso, perda_configurada, fundo = config

        registro_media = {
            "Experimento": experimento,
            "Banda_Mbps": banda,
            "Atraso_ms": atraso,
            "Perda_configurada_percentual": perda_configurada,
            "Fundo": fundo,
            "Throughput_medio_Mbps": media(
                [r["Throughput_iperf_Mbps"] for r in registros]
            ),
            "Throughput_min_Mbps": minimo(
                [r["Throughput_iperf_Mbps"] for r in registros]
            ),
            "Throughput_max_Mbps": maximo(
                [r["Throughput_iperf_Mbps"] for r in registros]
            ),
            "Retransmissoes_media": media(
                [r["Retransmissoes_iperf"] for r in registros]
            ),
            "FPS_medio": media(
                [r["FPS"] for r in registros]
            ),
            "Frames_medio": media(
                [r["Frames"] for r in registros]
            ),
            "Bitrate_video_medio_kbits": media(
                [r["Bitrate_video_kbits"] for r in registros]
            ),
            "Pacotes_Router_medio": media(
                [r["Pacotes_video_Router"] for r in registros]
            ),
            "Pacotes_Client1_medio": media(
                [r["Pacotes_video_Client1"] for r in registros]
            ),
            "Perda_observada_media_percentual": media(
                [r["Perda_observada_percentual"] for r in registros]
            ),
            "Perda_observada_min_percentual": minimo(
                [r["Perda_observada_percentual"] for r in registros]
            ),
            "Perda_observada_max_percentual": maximo(
                [r["Perda_observada_percentual"] for r in registros]
            ),
            "PCAP_Router_medio_bytes": media(
                [r["Tamanho_PCAP_Router_bytes"] for r in registros]
            ),
            "PCAP_Client1_medio_bytes": media(
                [r["Tamanho_PCAP_Client1_bytes"] for r in registros]
            ),
        }

        medias.append(registro_media)

    arquivo_medias = os.path.join(
        RESULTADOS_DIR,
        "resultados_medias.csv"
    )

    campos_medias = list(medias[0].keys())

    with open(
        arquivo_medias,
        "w",
        newline="",
        encoding="utf-8"
    ) as arquivo:

        escritor = csv.DictWriter(
            arquivo,
            fieldnames=campos_medias
        )

        escritor.writeheader()

        for registro in medias:
            escritor.writerow(registro)

    arquivo_relatorio = os.path.join(
        RESULTADOS_DIR,
        "relatorio_experimentos.txt"
    )

    with open(
        arquivo_relatorio,
        "w",
        encoding="utf-8"
    ) as arquivo:

        arquivo.write("RELATÓRIO DOS EXPERIMENTOS\n")
        arquivo.write("=" * 80 + "\n\n")

        arquivo.write(
            "Os valores de throughput foram convertidos para Mbps "
            "independentemente da unidade registrada pelo iperf3.\n"
        )

        arquivo.write(
            "A perda observada corresponde à diferença percentual entre "
            "os pacotes UDP da porta 1234 capturados no roteador e no cliente.\n\n"
        )

        arquivo.write(
            "Não foram inventados valores de CPU/Prometheus, pois essas "
            "métricas não estão presentes nos arquivos analisados.\n\n"
        )

        for registro in medias:

            arquivo.write("-" * 80 + "\n")

            arquivo.write(
                f"{registro['Experimento']} | "
                f"Banda: {registro['Banda_Mbps']} Mbps | "
                f"Atraso: {registro['Atraso_ms']} ms | "
                f"Perda configurada: "
                f"{registro['Perda_configurada_percentual']}% | "
                f"Fundo: {registro['Fundo']}\n"
            )

            if registro["Throughput_medio_Mbps"] is None:
                arquivo.write(
                    "Throughput iperf3: N/A "
                    "(sem tráfego de fundo)\n"
                )
            else:
                arquivo.write(
                    f"Throughput iperf3: "
                    f"{fmt(registro['Throughput_medio_Mbps'])} Mbps "
                    f"(min={fmt(registro['Throughput_min_Mbps'])}, "
                    f"max={fmt(registro['Throughput_max_Mbps'])})\n"
                )

                arquivo.write(
                    f"Retransmissões médias: "
                    f"{fmt(registro['Retransmissoes_media'])}\n"
                )

            arquivo.write(
                f"FPS médio: {fmt(registro['FPS_medio'])}\n"
            )

            arquivo.write(
                f"Frames médios: {fmt(registro['Frames_medio'], 0)}\n"
            )

            arquivo.write(
                f"Bitrate médio do vídeo: "
                f"{fmt(registro['Bitrate_video_medio_kbits'])} kbits/s\n"
            )

            arquivo.write(
                f"Pacotes UDP vídeo - Router: "
                f"{fmt(registro['Pacotes_Router_medio'], 0)}\n"
            )

            arquivo.write(
                f"Pacotes UDP vídeo - Client1: "
                f"{fmt(registro['Pacotes_Client1_medio'], 0)}\n"
            )

            arquivo.write(
                f"Perda observada média: "
                f"{fmt(registro['Perda_observada_media_percentual'])}% "
                f"(min={fmt(registro['Perda_observada_min_percentual'])}%, "
                f"max={fmt(registro['Perda_observada_max_percentual'])}%)\n"
            )

            arquivo.write(
                f"PCAP médio Router: "
                f"{fmt(registro['PCAP_Router_medio_bytes'], 0)} bytes\n"
            )

            arquivo.write(
                f"PCAP médio Client1: "
                f"{fmt(registro['PCAP_Client1_medio_bytes'], 0)} bytes\n"
            )

            arquivo.write(
                "CPU/Prometheus: não disponível nos dados analisados.\n"
            )

        arquivo.write("\n")
        arquivo.write("=" * 80 + "\n")
        arquivo.write("FIM DO RELATÓRIO\n")

    print("\n" + "=" * 70)
    print("ANÁLISE CONCLUÍDA")
    print("=" * 70)
    print(f"Arquivo completo: {arquivo_completo}")
    print(f"Médias:           {arquivo_medias}")
    print(f"Relatório:        {arquivo_relatorio}")


if __name__ == "__main__":
    analisar()
