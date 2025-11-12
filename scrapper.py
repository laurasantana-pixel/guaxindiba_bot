"""
queimadas_rj_scraper_click.py
-------------------------------------------------------
• Filtros aplicados no TerraBrasilis:
    – Continente .......... América do Sul
    – País ................ Brasil
    – Estado .............. Rio de Janeiro
    – Satélites ........... TODOS
• Captura a tabela <table id="attributes-table"> (dentro do div .dataTables_scrollBody)
• Salva o resultado completo em queimadas_rj.csv
-------------------------------------------------------
Requisitos:
    pip install selenium webdriver-manager pandas lxml
    • Chrome / Chromium instalado
"""

from etl.extract.terrabrasilis import (
    TerraBrasilisConfig,
    TerraBrasilisFilters,
    fetch_fire_data,
)

# ───────── CONFIGURAÇÃO RÁPIDA ─────────
HEADLESS = False  # True = roda escondido
STEP_DELAY = 1.5  # segundos entre cada ação (↑ p/ mais devagar)
PAUSE_AFTER_APPLY = True  # pausa p/ inspecionar após “Aplicar”
OUTPUT_CSV = "queimadas_rj.csv"
TIMEOUT = 25  # seg máx para aguardar elementos
# ────────────────────────────────────────

DEFAULT_FILTERS = TerraBrasilisFilters()
DEFAULT_CONFIG = TerraBrasilisConfig(
    headless=HEADLESS,
    step_delay=STEP_DELAY,
    pause_after_apply=PAUSE_AFTER_APPLY,
    timeout=TIMEOUT,
)


def main() -> None:
    df = fetch_fire_data(DEFAULT_FILTERS, config=DEFAULT_CONFIG)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"✅ CSV salvo: {OUTPUT_CSV}  ({len(df)} linhas)")


if __name__ == "__main__":
    main()
