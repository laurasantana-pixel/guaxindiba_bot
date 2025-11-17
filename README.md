# Guaxindiba Bot

Ferramentas para coletar e analisar focos de queimadas usando dados do TerraBrasilis.

## Pipeline ETL completo

O módulo `etl.pipeline` integra extração, transformação e carga dos dados em
um fluxo único. Ele coleta os focos de queimadas no TerraBrasilis, busca a
geometria da Estação Ecológica Estadual de Guaxindiba no OpenStreetMap,
marca os pontos que intersectam a reserva e persiste tanto a tabela final
quanto a geometria em disco.

### Como executar o pipeline

1. **Prepare o ambiente Python** (caso ainda não tenha sido feito):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # No Windows use `.venv\\Scripts\\activate`
   pip install --upgrade pip
   pip install pandas geopandas shapely selenium webdriver-manager
   ```

2. **Execute o pipeline via CLI**. Ajuste os caminhos conforme necessário:
   ```bash
   python -m etl.pipeline \
       --fires-output data/focos_processados.csv \
       --geometry-output data/reserva.geojson \
       --reserve-cache cache/reserva.geojson
   ```

   > 💡 No PowerShell, substitua as barras invertidas (`\`) por crases (`` ` ``)
   > ao quebrar linhas ou execute o comando em uma única linha:
   > ```powershell
   > python -m etl.pipeline `
   >     --fires-output data/focos_processados.csv `
   >     --geometry-output data/reserva.geojson `
   >     --reserve-cache cache/reserva.geojson
   > ```
   > ou
   > ```powershell
   > python -m etl.pipeline --fires-output data/focos_processados.csv --geometry-output data/reserva.geojson --reserve-cache cache/reserva.geojson
   > ```

3. **Revise as opções disponíveis**:
   ```bash
   python -m etl.pipeline --help
   ```

   Flags úteis:

   - `--headless`: executa o navegador em modo headless durante a coleta do
     TerraBrasilis.
   - `--no-mark-inside`: pula a etapa que marca focos dentro da reserva.
   - `--skip-geometry-output`: evita sobrescrever a geometria após a execução.

### Reutilizando em código Python

O pipeline também pode ser chamado programaticamente:

```python
from etl.pipeline import PipelineConfig, run_pipeline

config = PipelineConfig(
    dataframe_output="data/focos_processados.csv",
    geometry_output="data/reserva.geojson",
)
run_pipeline(config)
```

## Como testar a extração do TerraBrasilis

1. **Prepare o ambiente Python**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # No Windows use `.venv\\Scripts\\activate`
   pip install --upgrade pip
   pip install pandas selenium webdriver-manager
   ```

2. **Verifique se o Google Chrome está instalado.** O script usa `webdriver-manager` para baixar o ChromeDriver compatível automaticamente.

3. **Execute o coletor** (veja as opções com `--help`):
   ```bash
   python scripts/fetch_fires.py --help
   ```

   Para reproduzir a coleta padrão dos focos do Rio de Janeiro:
   ```bash
   python scripts/fetch_fires.py --output queimadas_rj.csv
   ```

4. **Personalize os filtros** conforme necessário, por exemplo:
   ```bash
   python scripts/fetch_fires.py \
       --continent "América do Sul" \
       --country 33 \
       --state '03333' \
       --satellite aqua_m-t
   ```

Durante a execução em modo gráfico, o navegador permanece aberto após clicar em **Aplicar** para permitir conferência manual. Use `--no-pause-after-apply` para automatizar totalmente ou `--headless` para executar sem interface.

## Dicas de solução de problemas

- Caso o Chrome não abra em ambientes headless (servidores remotos), combine `--headless --no-highlight`.
- Se o site demorar a responder, aumente o `--timeout` ou `--step-delay`.
- Se o script não conseguir localizar elementos, confirme se a interface do TerraBrasilis não mudou e tente executar novamente manualmente para investigar.
