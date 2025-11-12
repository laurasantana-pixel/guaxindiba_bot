"""Command line interface to download fire data from TerraBrasilis."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _ensure_project_root_on_path() -> None:
    """Make the repository root importable when running as a script."""

    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


_ensure_project_root_on_path()

from etl.extract.terrabrasilis import (  # noqa: E402  (import after path fix)
    TerraBrasilisConfig,
    TerraBrasilisFilters,
    fetch_fire_data,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("queimadas_rj.csv"),
        help="Arquivo CSV onde os dados serão salvos.",
    )
    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Executa o navegador em modo headless.",
    )
    parser.add_argument(
        "--step-delay",
        type=float,
        default=None,
        help="Intervalo em segundos entre cada interação com a página.",
    )
    parser.add_argument(
        "--pause-after-apply",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Pausa a execução após clicar em 'Aplicar' para inspeção manual.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Tempo máximo (em segundos) para aguardar elementos da página.",
    )
    parser.add_argument(
        "--continent",
        default=None,
        help="Nome visível do continente a ser selecionado.",
    )
    parser.add_argument(
        "--country",
        dest="countries",
        action="append",
        help="Valores do select de países (pode ser informado múltiplas vezes).",
    )
    parser.add_argument(
        "--state",
        dest="states",
        action="append",
        help="Valores do select de estados (pode ser informado múltiplas vezes).",
    )
    parser.add_argument(
        "--satellite",
        default=None,
        help="Valor utilizado no filtro de satélite.",
    )
    parser.add_argument(
        "--no-highlight",
        action="store_true",
        help="Desabilita o destaque visual dos elementos na página.",
    )
    parser.add_argument(
        "--keep-browser-open",
        action="store_true",
        help="Mantém o navegador aberto após o término da execução.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    config_kwargs: dict[str, object] = {}
    if args.headless is not None:
        config_kwargs["headless"] = args.headless
    if args.step_delay is not None:
        config_kwargs["step_delay"] = args.step_delay
    if args.pause_after_apply is not None:
        config_kwargs["pause_after_apply"] = args.pause_after_apply
    if args.timeout is not None:
        config_kwargs["timeout"] = args.timeout
    if args.no_highlight:
        config_kwargs["highlight_elements"] = False
    if args.keep_browser_open:
        config_kwargs["close_browser_on_finish"] = False

    config = TerraBrasilisConfig(**config_kwargs)

    filters_kwargs: dict[str, object] = {}
    if args.continent:
        filters_kwargs["continent"] = args.continent
    if args.countries:
        filters_kwargs["country_values"] = tuple(args.countries)
    if args.states:
        filters_kwargs["state_values"] = tuple(args.states)
    if args.satellite:
        filters_kwargs["satellite_value"] = args.satellite

    filters = TerraBrasilisFilters(**filters_kwargs)

    dataframe = fetch_fire_data(filters, config=config)
    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"✅ CSV salvo: {output_path}  ({len(dataframe)} linhas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
