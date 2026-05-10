import csv
from math import ceil
from pathlib import Path

import matplotlib.pyplot as plt


def read_measured(path):
    rows = []
    with path.open() as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                {
                    "qmax": int(row["qmax"]),
                    "rtt_ms": float(row["rtt_ms"]),
                    "tcrypto_ms": float(row["tcrypto_ms"]),
                    "m_requests": int(row["m_requests"]),
                    "amortized_ms_per_request": float(
                        row["amortized_ms_per_request"]
                    ),
                }
            )
    return rows


def compute_model(qmax_values, rtt_ms, tcrypto_ms, m_requests):
    rows = []
    for qmax in qmax_values:
        cproto = (rtt_ms + tcrypto_ms) * ceil(m_requests / qmax)
        amortized = cproto / m_requests
        rows.append(
            {
                "qmax": qmax,
                "rtt_ms": round(rtt_ms, 3),
                "tcrypto_ms": round(tcrypto_ms, 4),
                "m_requests": m_requests,
                "amortized_ms_per_request": round(amortized, 4),
            }
        )
    return rows


def write_csv(path, measured_rows, model_rows):
    fieldnames = [
        "source",
        "qmax",
        "rtt_ms",
        "tcrypto_ms",
        "m_requests",
        "amortized_ms_per_request",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in measured_rows:
            row_out = {**row, "source": "measured"}
            writer.writerow(row_out)
        for row in model_rows:
            row_out = {**row, "source": "paper_model"}
            writer.writerow(row_out)


def write_plot(path, measured_rows, model_rows):
    measured_rows = sorted(measured_rows, key=lambda r: r["qmax"])
    model_rows = sorted(model_rows, key=lambda r: r["qmax"])

    qmax_values = [row["qmax"] for row in measured_rows]
    measured = [row["amortized_ms_per_request"] for row in measured_rows]
    model = [row["amortized_ms_per_request"] for row in model_rows]

    plt.plot(qmax_values, measured, marker="o", label="Measured")
    plt.plot(qmax_values, model, marker="s", label="Paper model (tcrypto=7ms)")
    plt.title("Protocol Overhead: Measured vs Paper Model")
    plt.xlabel("Qmax (requests per token)")
    plt.ylabel("Overhead (ms/request)")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def main():
    output_dir = Path(__file__).parent
    measured_path = output_dir / "measured_protocol_overhead.csv"
    if not measured_path.exists():
        raise FileNotFoundError(f"Missing measured CSV: {measured_path}")

    measured_rows = read_measured(measured_path)
    qmax_values = sorted({row["qmax"] for row in measured_rows})
    rtt_ms = measured_rows[0]["rtt_ms"]
    m_requests = measured_rows[0]["m_requests"]

    # Paper model uses tcrypto=7ms; compare using measured RTT.
    model_rows = compute_model(qmax_values, rtt_ms, 7.0, m_requests)

    csv_path = output_dir / "comparison_protocol_overhead.csv"
    plot_path = output_dir / "comparison_protocol_overhead.png"

    write_csv(csv_path, measured_rows, model_rows)
    write_plot(plot_path, measured_rows, model_rows)

    print(f"Wrote {csv_path}")
    print(f"Wrote {plot_path}")


if __name__ == "__main__":
    main()
