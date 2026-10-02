import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ARQUIVO = Path("resultados/resultados_medias.csv")
SAIDA = Path("resultados/analise")
SAIDA.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(ARQUIVO)

df["Experimento"] = pd.Categorical(
    df["Experimento"],
    categories=[f"E{i}" for i in range(1, 17)],
    ordered=True
)

df["Fundo"] = df["Fundo"].map({
    "sem": "Sem fundo",
    "com": "Com fundo"
})

def salvar_grafico(nome):
    plt.tight_layout()
    plt.savefig(SAIDA / nome, dpi=150, bbox_inches="tight")
    plt.close()

# ============================================================
# 1. TABELAS
# ============================================================

df.to_csv(
    SAIDA / "tabela_completa.csv",
    index=False
)

colunas_principais = [
    "Experimento",
    "Banda_Mbps",
    "Atraso_ms",
    "Perda_configurada_percentual",
    "Fundo",
    "Throughput_medio_Mbps",
    "Retransmissoes_media",
    "FPS_medio",
    "Frames_medio",
    "Bitrate_video_medio_kbits",
    "Pacotes_Router_medio",
    "Pacotes_Client1_medio",
    "Perda_observada_media_percentual",
    "PCAP_Router_medio_bytes",
    "PCAP_Client1_medio_bytes"
]

df[colunas_principais].to_csv(
    SAIDA / "tabela_principal.csv",
    index=False
)

# ============================================================
# 2. THROUGHPUT POR EXPERIMENTO
# ============================================================

plt.figure(figsize=(12, 6))

plt.bar(
    df["Experimento"].astype(str),
    df["Throughput_medio_Mbps"].fillna(0)
)

plt.xlabel("Experimento")
plt.ylabel("Throughput médio (Mbps)")
plt.title("Throughput médio por experimento")
plt.grid(axis="y", alpha=0.3)

salvar_grafico("01_throughput_por_experimento.png")

# ============================================================
# 3. RETRANSMISSÕES
# ============================================================

plt.figure(figsize=(12, 6))

plt.bar(
    df["Experimento"].astype(str),
    df["Retransmissoes_media"].fillna(0)
)

plt.xlabel("Experimento")
plt.ylabel("Retransmissões médias")
plt.title("Retransmissões médias por experimento")
plt.grid(axis="y", alpha=0.3)

salvar_grafico("02_retransmissoes_por_experimento.png")

# ============================================================
# 4. FPS
# ============================================================

plt.figure(figsize=(12, 6))

plt.bar(
    df["Experimento"].astype(str),
    df["FPS_medio"]
)

plt.xlabel("Experimento")
plt.ylabel("FPS")
plt.title("FPS médio do vídeo por experimento")
plt.grid(axis="y", alpha=0.3)

salvar_grafico("03_fps_por_experimento.png")

# ============================================================
# 5. BITRATE DO VÍDEO
# ============================================================

plt.figure(figsize=(12, 6))

plt.bar(
    df["Experimento"].astype(str),
    df["Bitrate_video_medio_kbits"]
)

plt.xlabel("Experimento")
plt.ylabel("Bitrate (kbits/s)")
plt.title("Bitrate médio do vídeo por experimento")
plt.grid(axis="y", alpha=0.3)

salvar_grafico("04_bitrate_video.png")

# ============================================================
# 6. PERDA OBSERVADA
# ============================================================

plt.figure(figsize=(12, 6))

plt.bar(
    df["Experimento"].astype(str),
    df["Perda_observada_media_percentual"]
)

plt.xlabel("Experimento")
plt.ylabel("Perda observada (%)")
plt.title("Perda observada entre os pontos de captura")
plt.grid(axis="y", alpha=0.3)

salvar_grafico("05_perda_observada.png")

# ============================================================
# 7. TAMANHO DOS PCAPs
# ============================================================

plt.figure(figsize=(12, 6))

x = range(len(df))

plt.bar(
    [i - 0.2 for i in x],
    df["PCAP_Router_medio_bytes"] / 1024 / 1024,
    width=0.4,
    label="Router"
)

plt.bar(
    [i + 0.2 for i in x],
    df["PCAP_Client1_medio_bytes"] / 1024 / 1024,
    width=0.4,
    label="Client1"
)

plt.xticks(x, df["Experimento"].astype(str))
plt.xlabel("Experimento")
plt.ylabel("Tamanho médio (MB)")
plt.title("Tamanho médio dos PCAPs")
plt.legend()
plt.grid(axis="y", alpha=0.3)

salvar_grafico("06_tamanho_pcap.png")

# ============================================================
# 8. EFEITO DA BANDA
# ============================================================

grupo_banda = (
    df[df["Fundo"] == "Com fundo"]
    .groupby("Banda_Mbps", as_index=False)["Throughput_medio_Mbps"]
    .mean()
)

plt.figure(figsize=(8, 5))

plt.bar(
    grupo_banda["Banda_Mbps"].astype(str),
    grupo_banda["Throughput_medio_Mbps"]
)

plt.xlabel("Banda configurada (Mbps)")
plt.ylabel("Throughput médio (Mbps)")
plt.title("Efeito da banda configurada no throughput")
plt.grid(axis="y", alpha=0.3)

salvar_grafico("07_efeito_banda.png")

# ============================================================
# 9. EFEITO DO ATRASO
# ============================================================

grupo_atraso = (
    df[df["Fundo"] == "Com fundo"]
    .groupby("Atraso_ms", as_index=False)["Throughput_medio_Mbps"]
    .mean()
)

plt.figure(figsize=(8, 5))

plt.bar(
    grupo_atraso["Atraso_ms"].astype(str),
    grupo_atraso["Throughput_medio_Mbps"]
)

plt.xlabel("Atraso configurado (ms)")
plt.ylabel("Throughput médio (Mbps)")
plt.title("Efeito do atraso no throughput")
plt.grid(axis="y", alpha=0.3)

salvar_grafico("08_efeito_atraso.png")

# ============================================================
# 10. EFEITO DA PERDA
# ============================================================

grupo_perda = (
    df[df["Fundo"] == "Com fundo"]
    .groupby("Perda_configurada_percentual", as_index=False)
    ["Throughput_medio_Mbps"]
    .mean()
)

plt.figure(figsize=(8, 5))

plt.bar(
    grupo_perda["Perda_configurada_percentual"].astype(str),
    grupo_perda["Throughput_medio_Mbps"]
)

plt.xlabel("Perda configurada (%)")
plt.ylabel("Throughput médio (Mbps)")
plt.title("Efeito da perda configurada no throughput")
plt.grid(axis="y", alpha=0.3)

salvar_grafico("09_efeito_perda.png")

# ============================================================
# 11. EFEITO DO TRÁFEGO DE FUNDO
# ============================================================

grupo_fundo = (
    df.groupby(
        ["Banda_Mbps", "Atraso_ms", "Perda_configurada_percentual", "Fundo"],
        as_index=False
    )["Throughput_medio_Mbps"]
    .mean()
)

grupo_fundo.to_csv(
    SAIDA / "comparacao_trafego_fundo.csv",
    index=False
)

# ============================================================
# 12. COMPARAÇÃO SEM/COM FUNDO
# ============================================================

pares = []

for banda in [100, 200]:
    for atraso in [0, 50]:
        for perda in [0, 10]:

            sem = df[
                (df["Banda_Mbps"] == banda) &
                (df["Atraso_ms"] == atraso) &
                (df["Perda_configurada_percentual"] == perda) &
                (df["Fundo"] == "Sem fundo")
            ]

            com = df[
                (df["Banda_Mbps"] == banda) &
                (df["Atraso_ms"] == atraso) &
                (df["Perda_configurada_percentual"] == perda) &
                (df["Fundo"] == "Com fundo")
            ]

            if not sem.empty and not com.empty:
                sem_val = sem["Throughput_medio_Mbps"].iloc[0]
                com_val = com["Throughput_medio_Mbps"].iloc[0]

                pares.append({
                    "Banda_Mbps": banda,
                    "Atraso_ms": atraso,
                    "Perda_percentual": perda,
                    "Throughput_sem_fundo": sem_val,
                    "Throughput_com_fundo": com_val,
                    "Diferenca_Mbps": com_val - sem_val
                })

comparacao = pd.DataFrame(pares)

comparacao.to_csv(
    SAIDA / "comparacao_sem_com_fundo.csv",
    index=False
)

# ============================================================
# 13. RELATÓRIO AUTOMÁTICO
# ============================================================

with open(SAIDA / "relatorio_analise.txt", "w", encoding="utf-8") as f:

    f.write("ANÁLISE DOS EXPERIMENTOS E1–E16\n")
    f.write("=" * 70 + "\n\n")

    f.write("Quantidade de experimentos: 16\n")
    f.write("Repetições por experimento: 5\n")
    f.write("Total de execuções: 80\n\n")

    f.write("1. THROUGHPUT\n")
    f.write("-" * 70 + "\n")

    throughput_validos = df["Throughput_medio_Mbps"].dropna()

    if not throughput_validos.empty:
        f.write(
            f"Maior throughput médio: "
            f"{throughput_validos.max():.3f} Mbps\n"
        )

        f.write(
            f"Menor throughput médio: "
            f"{throughput_validos.min():.3f} Mbps\n"
        )

    f.write("\n")

    f.write("2. RETRANSMISSÕES\n")
    f.write("-" * 70 + "\n")

    retrans = df["Retransmissoes_media"].dropna()

    if not retrans.empty:
        maior = df.loc[
            df["Retransmissoes_media"].idxmax()
        ]

        f.write(
            f"Maior média de retransmissões: "
            f"{maior['Retransmissoes_media']:.1f} "
            f"({maior['Experimento']})\n"
        )

    f.write("\n")

    f.write("3. VÍDEO\n")
    f.write("-" * 70 + "\n")

    f.write(
        f"FPS médio geral: "
        f"{df['FPS_medio'].mean():.2f}\n"
    )

    f.write(
        f"Frames médios: "
        f"{df['Frames_medio'].mean():.2f}\n"
    )

    f.write(
        f"Bitrate médio: "
        f"{df['Bitrate_video_medio_kbits'].mean():.2f} kbits/s\n"
    )

    f.write("\n")

    f.write("4. PERDA OBSERVADA\n")
    f.write("-" * 70 + "\n")

    f.write(
        "A perda observada foi calculada pela diferença entre "
        "a quantidade de pacotes UDP capturados no router e no client1.\n"
    )

    f.write(
        "Esse valor representa a perda observada entre os dois "
        "pontos de captura e não deve ser interpretado isoladamente "
        "como prova de ausência de perda no caminho.\n\n"
    )

    f.write(
        f"Média geral da perda observada: "
        f"{df['Perda_observada_media_percentual'].mean():.2f}%\n\n"
    )

    f.write("5. PCAP\n")
    f.write("-" * 70 + "\n")

    f.write(
        f"Tamanho médio PCAP router: "
        f"{df['PCAP_Router_medio_bytes'].mean() / 1024 / 1024:.2f} MB\n"
    )

    f.write(
        f"Tamanho médio PCAP client1: "
        f"{df['PCAP_Client1_medio_bytes'].mean() / 1024 / 1024:.2f} MB\n"
    )

    f.write("\n")

    f.write("6. CPU / PROMETHEUS\n")
    f.write("-" * 70 + "\n")

    f.write(
        "Não incluído nos resultados dos experimentos porque o "
        "histórico disponível no Prometheus não cobre o período "
        "das execuções E1–E16.\n"
    )

print()
print("=" * 60)
print("ANÁLISE CONCLUÍDA")
print("=" * 60)
print()
print(f"Entrada: {ARQUIVO}")
print(f"Saída:   {SAIDA}")
print()
print("Arquivos gerados:")
for arquivo in sorted(SAIDA.iterdir()):
    print(f"  - {arquivo.name}")
print()
