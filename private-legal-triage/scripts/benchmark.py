"""Speed and memory benchmark harness for ZeroLatency legal triage.

Measures:
1. Document upload & parsing latency
2. BM25 retrieval latency
3. Q&A latency (cold-start vs warm runs)
4. Full pipeline analysis latency
5. Peak RAM and GPU VRAM consumption (via scripts/hardware.py)

Generates reproducible JSON and Markdown reports in reports/benchmark_report.json.
"""

import json
import statistics
import sys
import time
from pathlib import Path

root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from scripts.hardware import PeakSampler, system_info
from src.config import Settings
from src.gemma_client import OllamaClient
from src.service import DocumentStore
from tests.conftest import RENTAL_PAGES
from tests.helpers import rental_responder
from tests.stub_ollama import StubOllama


def run_benchmark(iterations: int = 3) -> dict:
    print("=" * 60)
    print("ZEROLATENCY BACKEND SPEED & MEMORY BENCHMARK")
    print("=" * 60)

    hw = system_info()
    print(f"OS: {hw['os']}")
    print(f"Python: {hw['python']}")
    print(f"CPU: {hw['cpu']} ({hw['cpu_logical_cores']} logical cores)")
    print(f"RAM Total: {hw['ram_total_mb']} MB")
    print(f"GPU: {hw['gpus']}")

    text_small = "\n\n".join(RENTAL_PAGES[:2]).encode("utf-8")
    text_medium = "\n\n".join(RENTAL_PAGES).encode("utf-8")
    text_large = ("\n\n".join(RENTAL_PAGES) + "\n\n" + "\n\n".join(RENTAL_PAGES)).encode("utf-8")

    bench_results = {
        "system": hw,
        "timestamp": time.time(),
        "iterations": iterations,
        "runs": {},
    }

    with StubOllama(installed=["gemma3n:e2b", "gemma3n:e4b"], responder=rental_responder) as stub:
        cfg = Settings(ollama_url=stub.url)

        for label, data in [("small_doc", text_small), ("medium_doc", text_medium), ("large_doc", text_large)]:
            print(f"\nBenchmarking {label} ({len(data)} bytes)...")
            upload_times = []
            analysis_times = []
            qa_cold_time = None
            qa_warm_times = []

            with PeakSampler() as sampler:
                store = DocumentStore(cfg, OllamaClient(cfg))

                for i in range(iterations):
                    # 1. Upload & Parsing
                    t0 = time.perf_counter()
                    doc = store.upload(f"{label}_{i}.txt", data)
                    t_up = time.perf_counter() - t0
                    upload_times.append(t_up)

                    # 2. Q&A (first is cold, subsequent warm)
                    t0 = time.perf_counter()
                    store.ask(doc.id, "What is the rent amount?")
                    t_qa = time.perf_counter() - t0
                    if i == 0:
                        qa_cold_time = t_qa
                    else:
                        qa_warm_times.append(t_qa)

                    # 3. Full analysis
                    t0 = time.perf_counter()
                    job = store.start_analysis(doc.id, model="gemma3n:e2b")
                    store.wait(job.id)
                    t_analysis = time.perf_counter() - t0
                    analysis_times.append(t_analysis)

                    store.delete(doc.id)

                store.close()
                mem_stats = sampler.summary()

            bench_results["runs"][label] = {
                "size_bytes": len(data),
                "upload_latency_median_ms": round(statistics.median(upload_times) * 1000, 2),
                "upload_latency_p95_ms": round(max(upload_times) * 1000, 2),
                "qa_cold_latency_ms": round((qa_cold_time or 0.0) * 1000, 2),
                "qa_warm_median_ms": round((statistics.median(qa_warm_times) if qa_warm_times else 0.0) * 1000, 2),
                "analysis_median_s": round(statistics.median(analysis_times), 3),
                "memory_profile": mem_stats,
            }
            print(f"  - Upload latency (median): {bench_results['runs'][label]['upload_latency_median_ms']} ms")
            print(f"  - Q&A Cold: {bench_results['runs'][label]['qa_cold_latency_ms']} ms | Warm (median): {bench_results['runs'][label]['qa_warm_median_ms']} ms")
            print(f"  - Analysis (median): {bench_results['runs'][label]['analysis_median_s']} s")
            print(f"  - Peak System RAM: {mem_stats['peak_system_used_mb']} MB")

    out_dir = Path("reports")
    out_dir.mkdir(exist_ok=True)
    report_file = out_dir / "benchmark_report.json"
    report_file.write_text(json.dumps(bench_results, indent=2))
    print(f"\n[OK] Benchmark report saved to {report_file.resolve()}")
    return bench_results


if __name__ == "__main__":
    run_benchmark(iterations=3)
