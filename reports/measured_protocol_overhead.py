import csv
import time
from math import ceil
from pathlib import Path

import requests

from saga import config as saga_config
from saga.common import crypto as sc


def measure_rtt_ms(url, samples=20, timeout=3.0):
    latencies = []
    for _ in range(samples):
        start = time.perf_counter()
        try:
            requests.get(url, verify=False, timeout=timeout)
            elapsed = (time.perf_counter() - start) * 1000.0
            latencies.append(elapsed)
        except requests.RequestException:
            # Skip failed sample
            continue
    if not latencies:
        raise RuntimeError("Unable to measure RTT (no successful samples).")
    latencies.sort()
    median = latencies[len(latencies) // 2]
    return median, latencies


def measure_crypto_ms(iterations=2000):
    # Measure representative crypto cost: key gen + signature verify + DH + token encrypt/decrypt.
    # This is a local proxy for tcrypto (ms).
    start = time.perf_counter()
    for _ in range(iterations):
        sk_a, pk_a = sc.generate_ed25519_keypair()
        sk_b, pk_b = sc.generate_ed25519_keypair()
        msg = b"ping"
        sig = sk_a.sign(msg)
        pk_a.verify(sig, msg)

        sac, pac = sc.generate_x25519_keypair()
        sotk, otk = sc.generate_x25519_keypair()
        sdhk = sac.exchange(otk)
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        token = {
            "nonce": b"0" * 12,
            "issue_timestamp": now,
            "expiration_timestamp": now + timedelta(minutes=1),
            "communication_quota": 10,
            "recipient_pac": pac,
        }
        import base64
        enc = sc.encrypt_token(token, sdhk)
        if isinstance(enc, bytes):
            enc = base64.b64encode(enc).decode("utf-8")
        sc.decrypt_token(enc, sdhk)
    elapsed = (time.perf_counter() - start) * 1000.0
    return elapsed / iterations


def compute_overhead(qmax_values, rtt_ms, tcrypto_ms, m_requests):
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


def write_csv(rows, path):
    fieldnames = [
        "qmax",
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

    qmax_values = [row["qmax"] for row in rows]
    series = [row["amortized_ms_per_request"] for row in rows]

    plt.plot(qmax_values, series, marker="o", label="Measured")
    plt.title("Measured Amortized Protocol Overhead per Request")
    plt.xlabel("Qmax (requests per token)")
    plt.ylabel("Overhead (ms/request)")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def main():
    output_dir = Path(__file__).parent
    qmax_values = [1, 5, 10, 20, 30]
    m_requests = 100

    provider_url = saga_config.PROVIDER_CONFIG["endpoint"].rstrip("/")
    rtt_ms, samples = measure_rtt_ms(f"{provider_url}/")
    tcrypto_ms = measure_crypto_ms()

    rows = compute_overhead(qmax_values, rtt_ms, tcrypto_ms, m_requests)

    csv_path = output_dir / "measured_protocol_overhead.csv"
    plot_path = output_dir / "measured_protocol_overhead.png"
    samples_path = output_dir / "measured_rtt_samples.csv"

    write_csv(rows, csv_path)
    write_plot(rows, plot_path)

    with samples_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["sample_ms"])
        for value in samples:
            writer.writerow([round(value, 3)])

    print(f"Provider: {provider_url}")
    print(f"Median RTT (ms): {rtt_ms:.3f}")
    print(f"Crypto cost (ms): {tcrypto_ms:.4f}")
    print(f"Wrote {csv_path}")
    print(f"Wrote {plot_path}")
    print(f"Wrote {samples_path}")


if __name__ == "__main__":
    main()
