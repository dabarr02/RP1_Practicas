import csv
from pathlib import Path
from statistics import mean, stdev

import matplotlib.pyplot as plt


FILES = {
    "Sin ahorro": "ping_none.csv",
    "Ahorro mínimo": "ping_minimum.csv",
    "Máx. 1": "ping_maximum_1.csv",
    "Máx. 3": "ping_maximum_3.csv",
    "Máx. 5": "ping_maximum_5.csv",
    "Máx. 10": "ping_maximum_10.csv",
}


def read_rtts(filename):
    with open(filename, newline="", encoding="utf-8") as file:
        return [
            float(row["rtt_ms"])
            for row in csv.DictReader(file)
            if row.get("rtt_ms")
        ]


labels = []
means = []
errors = []

for label, filename in FILES.items():
    path = Path(filename)

    if not path.exists():
        print(f"Aviso: no existe {filename}")
        continue

    rtts = read_rtts(filename)

    if not rtts:
        print(f"Aviso: {filename} no contiene medidas")
        continue

    labels.append(label)
    means.append(mean(rtts))
    errors.append(stdev(rtts) if len(rtts) > 1 else 0)

if not means:
    raise RuntimeError("No se encontraron datos para representar")

figure, axis = plt.subplots(figsize=(10, 6))
positions = range(len(labels))

axis.bar(
    positions,
    means,
    yerr=errors,
    capsize=5,
    color="steelblue",
    edgecolor="black",
    alpha=0.85,
)

axis.set_xticks(list(positions))
axis.set_xticklabels(labels, rotation=25, ha="right")
axis.set_xlabel("Configuración")
axis.set_ylabel("Tiempo medio de respuesta RTT [ms]")
axis.set_title("Tiempo medio de respuesta por captura")
axis.grid(True, axis="y", linestyle="--", alpha=0.5)

for position, value in zip(positions, means):
    axis.text(
        position,
        value,
        f"{value:.2f} ms",
        ha="center",
        va="bottom",
    )

plt.tight_layout()
plt.savefig("rtt_medias_barras.png", dpi=200)
plt.show()
