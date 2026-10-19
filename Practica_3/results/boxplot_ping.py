import csv
from pathlib import Path

import matplotlib.pyplot as plt


FILES = {
    "Sin ahorro": "ping_none.csv",
    "Ahorro mínimo": "ping_minimum.csv",
    "Máx. 1": "ping_maximum_1.csv",
    "Máx. 3": "ping_maximum_3.csv",
    "Máx. 5": "ping_maximum_5.csv",
    "Máx. 10": "ping_maximum_10.csv",
}


datasets = []
labels = []

for label, filename in FILES.items():
    path = Path(filename)

    if not path.exists():
        print(f"Aviso: no existe {filename}")
        continue

    values = []

    with open(filename, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            values.append(float(row["rtt_ms"]))

    if not values:
        print(f"Aviso: {filename} no contiene medidas")
        continue

    datasets.append(values)
    labels.append(label)


if not datasets:
    raise RuntimeError("No se encontraron datos para representar")


figure, axis = plt.subplots(figsize=(10, 6))

axis.boxplot(
    datasets,
    tick_labels=labels,
    showmeans=True,
    meanline=True,
    showfliers=True,
)

axis.set_xlabel("Configuración")
axis.set_ylabel("Tiempo de respuesta RTT [ms]")
axis.set_title("Distribución de los tiempos de respuesta")
axis.grid(True, axis="y", linestyle="--", alpha=0.5)

plt.xticks(rotation=25, ha="right")
plt.tight_layout()
plt.savefig("rtt_boxplot.png", dpi=200)
plt.show()