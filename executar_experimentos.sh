#!/usr/bin/env bash
set -euo pipefail

DURATION="${DURATION:-60}"
REPETITIONS=5
VIDEO="${VIDEO:-./videos/video.mp4}"
BASE_DIR="${BASE_DIR:-./experimentos}"
PCAP_DIR="${PCAP_DIR:-./capturas}"
LOG_DIR="${LOG_DIR:-./logs}"

# Porta usada pelo vídeo.
VIDEO_PORT="${VIDEO_PORT:-1234}"

# Interface do roteador que leva aos clientes.
ROUTER_CLIENT_IF="${ROUTER_CLIENT_IF:-r-c1}"

# Cliente que recebe o vídeo e também serve o iperf3.
CLIENT_IP="10.0.11.2"

mkdir -p "$BASE_DIR" "$PCAP_DIR" "$LOG_DIR"

if [[ ! -f "$VIDEO" ]]; then
    echo "ERRO: vídeo não encontrado: $VIDEO"
    exit 1
fi

if ! ip netns list | grep -q '^ns-router'; then
    echo "ERRO: ns-router não existe. Execute primeiro:"
    echo "  bash setup_lab_netns.sh"
    exit 1
fi

cleanup_processes() {
    sudo ip netns exec ns-video pkill -f "ffmpeg.*${VIDEO_PORT}" 2>/dev/null || true
    sudo ip netns exec ns-bg pkill -x iperf3 2>/dev/null || true
    sudo ip netns exec ns-client1 pkill -x iperf3 2>/dev/null || true
    sudo pkill -f "tcpdump.*E[0-9].*router" 2>/dev/null || true
    sudo pkill -f "tcpdump.*E[0-9].*client1" 2>/dev/null || true
}

clear_tc() {
    sudo ip netns exec ns-router tc qdisc del dev "$ROUTER_CLIENT_IF" root 2>/dev/null || true
}

apply_tc() {
    local bandwidth="$1"
    local delay="$2"
    local loss="$3"

    clear_tc

    # Um único qdisc netem permite combinar banda, atraso e perda.
    # Isso evita que uma regra tc sobrescreva a anterior.
    if [[ "$delay" == "0" && "$loss" == "0" ]]; then
        sudo ip netns exec ns-router \
            tc qdisc add dev "$ROUTER_CLIENT_IF" root netem rate "${bandwidth}mbit"
    elif [[ "$delay" == "0" ]]; then
        sudo ip netns exec ns-router \
            tc qdisc add dev "$ROUTER_CLIENT_IF" root netem \
            rate "${bandwidth}mbit" loss "${loss}%"
    else
        sudo ip netns exec ns-router \
            tc qdisc add dev "$ROUTER_CLIENT_IF" root netem \
            rate "${bandwidth}mbit" delay "${delay}ms" loss "${loss}%"
    fi
}

start_iperf_server() {
    sudo ip netns exec ns-client1 \
        iperf3 -s > /dev/null 2>&1 &
    IPERF_SERVER_PID=$!
    sleep 1
}

start_background() {
    local logfile="$1"

    sudo ip netns exec ns-bg \
        iperf3 -c "$CLIENT_IP" -t "$DURATION" \
        --logfile "$logfile" &
    BG_PID=$!
}

start_captures() {
    local exp="$1"
    local rep="$2"
    local dir="$3"

    sudo ip netns exec ns-router \
        tcpdump -i "$ROUTER_CLIENT_IF" -s 96 -w \
        "$dir/${exp}_R${rep}_router.pcap" \
        > "$dir/${exp}_R${rep}_router_tcpdump.log" 2>&1 &
    TCP_ROUTER_PID=$!

    sudo ip netns exec ns-client1 \
        tcpdump -i c1 -s 96 -w \
        "$dir/${exp}_R${rep}_client1.pcap" \
        > "$dir/${exp}_R${rep}_client1_tcpdump.log" 2>&1 &
    TCP_CLIENT_PID=$!

    sleep 1
}

start_video() {
    local logfile="$1"

    sudo ip netns exec ns-video \
        ffmpeg -hide_banner -loglevel info \
        -re -i "$VIDEO" \
        -f mpegts \
        "udp://${CLIENT_IP}:${VIDEO_PORT}" \
        > "$logfile" 2>&1 &
    VIDEO_PID=$!
}

stop_pid() {
    local pid="${1:-}"

    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null || true
        wait "$pid" 2>/dev/null || true
    fi
}

run_experiment() {
    local exp="$1"
    local bandwidth="$2"
    local delay="$3"
    local loss="$4"
    local background="$5"
    local rep="$6"

    local dir="${BASE_DIR}/${exp}"
    mkdir -p "$dir"

    local prefix="${exp}_R${rep}"
    local video_log="${LOG_DIR}/${prefix}_ffmpeg.log"
    local iperf_log="${LOG_DIR}/${prefix}_iperf3.log"
    local run_log="${LOG_DIR}/${prefix}_execucao.log"

    echo
    echo "========================================"
    echo "Iniciando ${exp} - Repetição ${rep}/${REPETITIONS}"
    echo "Banda: ${bandwidth} Mbps | Atraso: ${delay} ms | Perda: ${loss}% | Fundo: ${background}"
    echo "========================================"

    cleanup_processes
    clear_tc
    apply_tc "$bandwidth" "$delay" "$loss"

    echo "tc aplicado:" | tee "$run_log"
    sudo ip netns exec ns-router tc qdisc show dev "$ROUTER_CLIENT_IF" \
        | tee -a "$run_log"

    start_iperf_server
    start_captures "$exp" "$rep" "$PCAP_DIR"

    # Pequena margem para os tcpdumps iniciarem antes do tráfego.
    sleep 1

    start_video "$video_log"

    if [[ "$background" == "com" ]]; then
        start_background "$iperf_log"
    fi

    # A execução dura DURATION segundos.
    sleep "$DURATION"

    # Finaliza os processos dessa repetição.
    stop_pid "${BG_PID:-}"
    stop_pid "${VIDEO_PID:-}"
    stop_pid "${TCP_ROUTER_PID:-}"
    stop_pid "${TCP_CLIENT_PID:-}"
    stop_pid "${IPERF_SERVER_PID:-}"

    cleanup_processes
    clear_tc

    {
        echo "Experimento: ${exp}"
        echo "Repetição: ${rep}"
        echo "Banda: ${bandwidth} Mbps"
        echo "Atraso: ${delay} ms"
        echo "Perda configurada: ${loss}%"
        echo "Tráfego de fundo: ${background}"
        echo "Duração: ${DURATION} s"
        echo "PCAP router: ${PCAP_DIR}/${prefix}_router.pcap"
        echo "PCAP client1: ${PCAP_DIR}/${prefix}_client1.pcap"
        echo "Log ffmpeg: ${video_log}"
        echo "Log iperf3: ${iperf_log}"
        echo "----------------------------------------"
        echo
    } >> "$run_log"

    echo "Finalizado ${exp} - Repetição ${rep}/${REPETITIONS}"
}

# Matriz: experimento|banda|atraso|perda|fundo
EXPERIMENTS=(
    "E1|200|0|0|sem"
    "E2|200|0|0|com"
    "E3|200|0|10|sem"
    "E4|200|0|10|com"
    "E5|200|50|0|sem"
    "E6|200|50|0|com"
    "E7|200|50|10|sem"
    "E8|200|50|10|com"
    "E9|100|0|0|sem"
    "E10|100|0|0|com"
    "E11|100|0|10|sem"
    "E12|100|0|10|com"
    "E13|100|50|0|sem"
    "E14|100|50|0|com"
    "E15|100|50|10|sem"
    "E16|100|50|10|com"
)

echo "========================================"
echo "PRÁTICA - EXECUÇÃO AUTOMÁTICA"
echo "16 experimentos x 5 repetições = 80 execuções"
echo "Duração por execução: ${DURATION} segundos"
echo "========================================"

for item in "${EXPERIMENTS[@]}"; do
    IFS='|' read -r exp bandwidth delay loss background <<< "$item"

    for ((rep=1; rep<=REPETITIONS; rep++)); do
        run_experiment \
            "$exp" "$bandwidth" "$delay" "$loss" "$background" "$rep"
    done
done

cleanup_processes
clear_tc

echo
echo "========================================"
echo "TODOS OS 16 EXPERIMENTOS FORAM EXECUTADOS"
echo "5 repetições por experimento"
echo "Total: 80 execuções"
echo "========================================"
echo "PCAPs: ${PCAP_DIR}/"
echo "Logs:  ${LOG_DIR}/"
echo "Experimentos: ${BASE_DIR}/"
