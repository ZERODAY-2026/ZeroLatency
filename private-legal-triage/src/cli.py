import argparse
import sys

from .config import settings
from .errors import TriageError
from .gemma_client import OllamaClient
from .pipeline import DocumentSession
from .privacy import network_guard
from .report import to_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="triage")
    parser.add_argument("path")
    parser.add_argument("--ask", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        with network_guard():
            client = OllamaClient(settings)
            client.check_ready()
            session = DocumentSession(args.path, client, settings)
            result = session.analyze(lambda done, total: print(f"analysed {done}/{total}", file=sys.stderr))
            answers = [session.ask(question) for question in args.ask]
    except TriageError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    if args.json:
        print(result.model_dump_json(indent=2))
    else:
        print(to_markdown(result, answers))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
