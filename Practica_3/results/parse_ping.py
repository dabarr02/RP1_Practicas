# parse_ping.py
import re
import csv
import sys

if len(sys.argv) != 3:
    print("Uso: python3 parse_ping.py ping.txt resultado.csv")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

pattern = re.compile(
    r"icmp_seq[= ](\d+).*time[=<]([\d.]+)\s*ms"
)

with open(input_file, encoding="utf-8") as source, \
     open(output_file, "w", newline="", encoding="utf-8") as target:

    writer = csv.writer(target)
    writer.writerow(["sequence", "rtt_ms"])

    for line in source:
        match = pattern.search(line)
        if match:
            writer.writerow([
                int(match.group(1)),
                float(match.group(2))
            ])