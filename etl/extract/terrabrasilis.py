"""Utilities to extract fire data from TerraBrasilis."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Iterable, Sequence

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

import time

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TerraBrasilisFilters:
    """Selection filters used in the TerraBrasilis attribute table."""

    continent: str = "América do Sul"
    country_values: Sequence[str] = field(default_factory=lambda: ("33",))
    state_values: Sequence[str] = field(default_factory=lambda: ("03333",))
    satellite_value: str = "all"

    def __post_init__(self) -> None:
        self.country_values = tuple(self._normalize_iterable(self.country_values))
        self.state_values = tuple(self._normalize_iterable(self.state_values))

    @staticmethod
    def _normalize_iterable(values: Sequence[str] | str) -> Iterable[str]:
        if isinstance(values, str):
            return (values,)
        return tuple(values)


@dataclass(slots=True)
class TerraBrasilisConfig:
    """General configuration for the TerraBrasilis webdriver session."""

    url: str = "https://terrabrasilis.dpi.inpe.br/queimadas/bdqueimadas"
    headless: bool = False
    window_size: str = "1400,900"
    step_delay: float = 1.5
    pause_after_apply: bool = True
    timeout: int = 25
    highlight_elements: bool = True
    close_browser_on_finish: bool | None = None
    extra_chrome_args: Sequence[str] = field(default_factory=tuple)

    def should_close_browser(self) -> bool:
        if self.close_browser_on_finish is not None:
            return self.close_browser_on_finish
        return self.headless or not self.pause_after_apply


def _highlight(
    driver: webdriver.Chrome,
    element,
    *,
    color: str = "red",
    border: str = "2px solid",
    enable: bool = True,
) -> None:
    if not enable:
        return
    driver.execute_script(
        "arguments[0].style.border='%s %s'" % (border, color), element
    )


def _sleep(delay: float) -> None:
    if delay > 0:
        time.sleep(delay)


def fetch_fire_data(filters: TerraBrasilisFilters, *, config: TerraBrasilisConfig | None = None) -> pd.DataFrame:
    """Fetch fire data from TerraBrasilis using Selenium."""

    cfg = config or TerraBrasilisConfig()

    logger.info(
        "Iniciando coleta no TerraBrasilis (headless=%s, estados=%s, países=%s, satélite=%s)",
        cfg.headless,
        filters.state_values,
        filters.country_values,
        filters.satellite_value,
    )

    options = Options()
    if cfg.headless:
        options.add_argument("--headless=new")
    if cfg.window_size:
        options.add_argument(f"--window-size={cfg.window_size}")
    for arg in cfg.extra_chrome_args:
        options.add_argument(arg)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    wait = WebDriverWait(driver, cfg.timeout)

    try:
        driver.get(cfg.url)
        _sleep(cfg.step_delay)
        logger.info("Página carregada: %s", cfg.url)

        table_button = wait.until(
            EC.element_to_be_clickable((By.ID, "table-button"))
        )
        _highlight(driver, table_button, enable=cfg.highlight_elements and not cfg.headless)
        table_button.click()
        _sleep(cfg.step_delay)
        logger.debug("Tabela de atributos aberta")

        Select(driver.find_element(By.ID, "continents")).select_by_visible_text(filters.continent)
        _sleep(cfg.step_delay)
        logger.debug("Continente selecionado: %s", filters.continent)

        countries = Select(driver.find_element(By.ID, "countries"))
        countries.deselect_all()
        for value in filters.country_values:
            countries.select_by_value(value)
        _sleep(cfg.step_delay)
        logger.debug("Países selecionados: %s", filters.country_values)

        states = Select(driver.find_element(By.ID, "states"))
        states.deselect_all()
        for value in filters.state_values:
            states.select_by_value(value)
        _sleep(cfg.step_delay)
        logger.debug("Estados selecionados: %s", filters.state_values)

        satellite = driver.find_element(By.ID, "filter-satellite")
        driver.execute_script(
            """
            const sel = arguments[0];
            [...sel.options].forEach(o => o.selected = false);
            sel.value = arguments[1];
            sel.dispatchEvent(new Event('change', {bubbles:true}));
            """,
            satellite,
            filters.satellite_value,
        )
        _highlight(driver, satellite, color="orange", enable=cfg.highlight_elements and not cfg.headless)
        _sleep(cfg.step_delay)
        logger.debug("Satélite selecionado: %s", filters.satellite_value)

        apply_button = driver.find_element(By.ID, "filter-button")
        _highlight(driver, apply_button, color="lime", enable=cfg.highlight_elements and not cfg.headless)
        apply_button.click()
        logger.info("Botão 'Aplicar' acionado; aguardando tabela filtrada")
        _sleep(cfg.step_delay)

        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#attributes-table tbody tr"))
        )
        _sleep(cfg.step_delay)
        logger.debug("Tabela filtrada disponível")

        if cfg.pause_after_apply and not cfg.headless:
            input(
                "\n🔎  Tabela filtrada pronta no navegador.\n"
                "   Pressione <Enter> para exportar CSV..."
            )

        table_html = driver.find_element(By.ID, "attributes-table").get_attribute("outerHTML")
        dataframe = pd.read_html(table_html)[0]
        logger.info("Dados extraídos do TerraBrasilis: %s linhas", len(dataframe))
        return dataframe

    finally:
        if cfg.should_close_browser():
            driver.quit()
        else:
            logger.info("Navegador permanecerá aberto para inspeção manual")
