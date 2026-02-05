import argparse
from testgenai.orchestration.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TestGenAI pipeline runner")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    run_pipeline(args.config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
