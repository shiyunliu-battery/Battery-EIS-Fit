from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .config import FitConfig
from .pipeline import process_file, process_folder


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fit battery EIS data with an equivalent-circuit model.")
    parser.add_argument("path", help="CSV/Excel file or directory containing EIS data.")
    parser.add_argument("--out-dir", default="outputs", help="Directory for generated Excel and PNG outputs.")
    parser.add_argument("--pattern", default="*.csv", help="Glob pattern used when path is a directory.")
    parser.add_argument("--n-starts", type=int, default=40, help="Number of multi-start optimization runs.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for reproducible multi-start fitting.")
    parser.add_argument("--max-nfev", type=int, default=8000, help="Maximum function evaluations per optimizer start.")
    parser.add_argument("--tail", choices=["cpe", "warburg"], default="cpe", help="Low-frequency tail model.")
    parser.add_argument("--weight-func", choices=["modulus", "unit"], default="modulus", help="Residual weighting strategy.")
    parser.add_argument("--loss", default="soft_l1", help="scipy least_squares loss function.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cfg = FitConfig(n_starts=args.n_starts, seed=args.seed, max_nfev=args.max_nfev, tail=args.tail, weight_func=args.weight_func, loss=args.loss)

    import pathlib

    path = pathlib.Path(args.path)
    if path.is_dir():
        results = process_folder(path, pattern=args.pattern, cfg=cfg, out_dir=args.out_dir)
        summary = {name: (value.get("fit").parameters if "fit" in value else value) for name, value in results.items()}
    else:
        result = process_file(path, cfg=cfg, out_dir=args.out_dir)
        fit = result["fit"]
        summary = {"parameters": fit.parameters, "rmse": fit.rmse, "nrmse": fit.nrmse, "outputs": result["outputs"], "config": asdict(cfg)}

    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
