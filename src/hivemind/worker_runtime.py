import argparse
import os
import time

from .worker import CodexCliRunner, DryRunCodex, EmpireWorker, HttpWorkerApi, WorkerConfig


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    config = WorkerConfig(os.environ["HIVEMIND_API_URL"], os.environ["HIVEMIND_WORKER_ID"])
    runner = CodexCliRunner(binary=os.getenv("CODEX_BINARY", "codex")) if os.getenv("HIVEMIND_CODEX_MODE", "dry-run") == "real" else DryRunCodex()
    worker = EmpireWorker(config, HttpWorkerApi(config.api_base_url, os.environ["HIVEMIND_WORKER_TOKEN"]), runner)
    outcome = worker.run_once()
    print(outcome, flush=True)
    if args.once:
        return
    while True:
        time.sleep(15 if outcome == "IDLE" else 5)
        outcome = worker.run_once()
        print(outcome, flush=True)


if __name__ == "__main__":
    main()