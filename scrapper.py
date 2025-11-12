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

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

# ───────── CONFIGURAÇÃO RÁPIDA ─────────
HEADLESS           = False   # True = roda escondido
STEP_DELAY         = 1.5     # segundos entre cada ação (↑ p/ mais devagar)
PAUSE_AFTER_APPLY  = True    # pausa p/ inspecionar após “Aplicar”
URL                = (
    "https://terrabrasilis.dpi.inpe.br/queimadas/bdqueimadas"
)
OUTPUT_CSV         = "queimadas_rj.csv"
TIMEOUT            = 25      # seg máx para aguardar elementos
# ────────────────────────────────────────


def highlight(el, drv, *, color="red", border="2px solid"):
    """Desenha uma borda no elemento para facilitar a visualização."""
    drv.execute_script(
        "arguments[0].style.border='%s %s'" % (border, color), el
    )


def main() -> None:
    # Configuração do Chrome
    opts = Options()
    if HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1400,900")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=opts
    )
    wait = WebDriverWait(driver, TIMEOUT)

    try:
        driver.get(URL)
        time.sleep(STEP_DELAY)

        # 1) Abre a aba “Tabela de Atributos”
        tbl_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "table-button"))
        )
        highlight(tbl_btn, driver)
        tbl_btn.click()
        time.sleep(STEP_DELAY)

        # 2) Seleciona Continente → América do Sul
        Select(driver.find_element(By.ID, "continents")) \
            .select_by_visible_text("América do Sul")
        time.sleep(STEP_DELAY)

        # 3) Seleciona País → Brasil
        country = Select(driver.find_element(By.ID, "countries"))
        country.deselect_all()
        country.select_by_value("33")  # Brasil
        time.sleep(STEP_DELAY)

        # 4) Seleciona Estado → Rio de Janeiro
        state = Select(driver.find_element(By.ID, "states"))
        state.deselect_all()
        state.select_by_value("03333")  # RJ
        time.sleep(STEP_DELAY)

        # 5) Seleciona Satélites → TODOS (dispara evento 'change')
        sat_elem = driver.find_element(By.ID, "filter-satellite")
        driver.execute_script("""
            const sel = arguments[0];
            [...sel.options].forEach(o => o.selected = false);
            sel.value = 'all';
            sel.dispatchEvent(new Event('change', {bubbles:true}));
        """, sat_elem)
        highlight(sat_elem, driver, color="orange")
        time.sleep(STEP_DELAY)

        # 6) Clica em “Aplicar”
        apply_btn = driver.find_element(By.ID, "filter-button")
        highlight(apply_btn, driver, color="lime")
        apply_btn.click()
        print("✔ Botão 'Aplicar' clicado.")
        time.sleep(STEP_DELAY)

        # 7) Aguarda a tabela real (#attributes-table) carregar
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#attributes-table tbody tr"))
        )
        time.sleep(STEP_DELAY)

        if PAUSE_AFTER_APPLY:
            input(
                "\n🔎  Tabela filtrada pronta no navegador.\n"
                "   Pressione <Enter> para exportar CSV..."
            )

        # 8) Extrai SOMENTE o HTML da tabela visível (#attributes-table)
        table_html = driver.find_element(
            By.ID, "attributes-table"
        ).get_attribute("outerHTML")

        # 9) Converte a tabela para DataFrame e salva CSV
        df = pd.read_html(table_html)[0]
        df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
        print(f"✅ CSV salvo: {OUTPUT_CSV}  ({len(df)} linhas)")

    finally:
        if HEADLESS or not PAUSE_AFTER_APPLY:
            driver.quit()
        else:
            print("\n(O Chrome continuará aberto, feche-o quando terminar.)")


if __name__ == "__main__":
    main()