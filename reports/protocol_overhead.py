import csv
from math import ceil
from pathlib import Path


def compute_overhead(qmax_values, rtts, tcrypto_ms, m_requests):
    rows = []
    for qmax in qmax_values:
        for region, rtt in rtts.items():
            cproto = (rtt + tcrypto_ms) * ceil(m_requests / qmax)
            amortized = cproto / m_requests
            rows.append(
                {
                    "qmax": qmax,
                    "region": region,
                    "rtt_ms": rtt,
                    "tcrypto_ms": tcrypto_ms,
                    "m_requests": m_requests,
                    "amortized_ms_per_request": round(amortized, 4),
                }
            )
    return rows


def write_csv(rows, path):
    fieldnames = [
        "qmax",
        "region",
        "rtt_ms",
        "tcrypto_ms",
        "m_requests",
        "amortized_ms_per_request",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_plot(rows, path):
    import matplotlib.pyplot as plt

    qmax_values = sorted({row["qmax"] for row in rows})
    regions = sorted({row["region"] for row in rows})

    for region in regions:
        series = [
            row["amortized_ms_per_request"]
            for row in rows
            if row["region"] == region
        ]
        plt.plot(qmax_values, series, marker="o", label=region)

    plt.title("Amortized Protocol Overhead per Request")
    plt.xlabel("Qmax (requests per token)")
    plt.ylabel("Overhead (ms/request)")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def main():
    output_dir = Path(__file__).parent

    # Assumptions for a local simulation (ms)
    rtts = {
        "US-West": 40,
        "US-East": 60,
        "EU": 90,
        "Asia": 150,
    }
    tcrypto_ms = 7
    m_requests = 100
    qmax_values = [1, 5, 10, 20, 30]

    rows = compute_overhead(qmax_values, rtts, tcrypto_ms, m_requests)

    csv_path = output_dir / "protocol_overhead.csv"
    plot_path = output_dir / "protocol_overhead.png"

    write_csv(rows, csv_path)
    write_plot(rows, plot_path)

    print(f"Wrote {csv_path}")
    print(f"Wrote {plot_path}")


if __name__ == "__main__":
    main()
