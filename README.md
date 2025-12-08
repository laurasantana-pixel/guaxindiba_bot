# Guaxindiba Bot

Ferramentas em Python para baixar focos de queimadas do TerraBrasilis, buscar a geometria de uma área (OSM ou GeoJSON próprio), marcar quais pontos estão dentro dessa área e salvar tudo em CSV/GeoJSON.

## Estrutura do projeto (visão geral)
```
guaxindiba_bot/
├─ etl/
│  ├─ pipeline.py          # Orquestração do fluxo completo (CLI e função)
│  ├─ extract/
│  │   ├─ terrabrasilis.py # Coleta os focos via Selenium no TerraBrasilis
│  │   └─ reserve.py       # Busca a geometria no OSM ou em arquivo/local cache
│  ├─ transform/
│  │   └─ spatial.py       # Converte para GeoDataFrame e marca interseções
│  └─ load/
│      └─ csv.py           # Salva CSV de focos e GeoJSON de geometria
├─ scripts/
│  └─ fetch_fires.py       # Exemplo de coleta isolada do TerraBrasilis
├─ data/                   # Saídas padrão (CSV/GeoJSON)
└─ cache/                  # Cache opcional de geometria (GeoJSON)
```

### Módulos principais
- `etl.pipeline`: monta o pipeline (extrai focos, carrega geometria, marca interseções e grava saídas). Exposto via CLI (`python -m etl.pipeline`) e programaticamente.
- `etl.extract.terrabrasilis`: abre o TerraBrasilis com Selenium, aplica filtros (continente/país/estado/satélite) e lê a tabela em HTML para DataFrame.
- `etl.extract.reserve`: resolve a geometria da área. Tenta OSM com múltiplos tags/fallback de geocodificação ou usa um GeoJSON informado; pode ler/escrever cache.
- `etl.transform.spatial`: `mark_points_inside` cria GeoDataFrame e adiciona colunas booleanas indicando se cada foco intersecta a geometria.
- `etl.load.csv`: `save_dataframe` grava CSV (focos processados) e `save_geometry` grava GeoJSON da área, garantindo criação de diretórios.
- `scripts/fetch_fires.py`: utilitário simples para coletar focos do TerraBrasilis sem rodar o pipeline completo.

## O que é salvo
- `data/focos_processados.csv` (padrão de `--fires-output`): tabela dos focos coletados do TerraBrasilis, com colunas extras de geometria e marcação de interseção.
- `data/reserva.geojson` (padrão de `--geometry-output`): geometria da área usada na checagem de interseção.
- Cache opcional da geometria (`--reserve-cache`): se existir, é reutilizado e a busca no OSM é pulada.

## Pré-requisitos
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Como rodar o pipeline
### Execução padrão (Guaxindiba, RJ)
```bash
python -m etl.pipeline \
  --fires-output data/focos_processados.csv \
  --geometry-output data/reserva.geojson \
  --reserve-cache cache/reserva.geojson
```
PowerShell (quebra de linha com crase):
```powershell
python -m etl.pipeline `
  --fires-output data/focos_processados.csv `
  --geometry-output data/reserva.geojson `
  --reserve-cache cache/reserva.geojson
```

### Usar outra área (OSM)
- Troque o nome e delimite a busca com um lugar:
```bash
python -m etl.pipeline \
  --fires-output data/focos_processados.csv \
  --geometry-output data/reserva.geojson \
  --reserve-cache cache/rio_bonito.geojson \
  --reserve-name "Rio Bonito, Rio de Janeiro, Brazil" \
  --reserve-search-place "Rio de Janeiro, Brazil"
```
- PowerShell:
```powershell
python -m etl.pipeline `
  --fires-output data/focos_processados.csv `
  --geometry-output data/reserva.geojson `
  --reserve-cache cache/rio_bonito.geojson `
  --reserve-name "Rio Bonito, Rio de Janeiro, Brazil" `
  --reserve-search-place "Rio de Janeiro, Brazil"
```
- Dica: use um cache diferente por área ou remova o cache anterior para não reaproveitar a geometria errada.

### Usar uma geometria própria (pular OSM)
```bash
python -m etl.pipeline \
  --fires-output data/focos_processados.csv \
  --geometry-output data/reserva.geojson \
  --reserve-cache cache/minha_area.geojson \
  --reserve-geometry-file data/minha_area.geojson
```

### Filtrar focos por município (texto nas colunas de município)
```bash
python -m etl.pipeline \
  --fires-output data/focos_processados.csv \
  --geometry-output data/reserva.geojson \
  --reserve-cache cache/reserva.geojson \
  --city-name "Campos dos Goytacazes"
```

### Modo offline (dados de exemplo)
Usa `focos_ficticios.csv` e o GeoJSON local (ou `EEEG_polygon.geojson` se nada for informado):
```bash
python -m etl.pipeline --offline-sample \
  --fires-output data/focos_processados.csv \
  --geometry-output data/reserva.geojson \
  --reserve-geometry-file data/minha_area.geojson  # opcional, para trocar a área
```

## Opções úteis
- `--headless`: roda o Selenium sem interface gráfica.
- `--no-mark-inside`: pula a etapa de interseção; salva o CSV bruto coletado.
- `--skip-geometry-output`: não grava o GeoJSON ao final.
- `--reserve-search-place` pode ser repetido para testar recortes diferentes.

## Agendar execução (exemplo rápido)
- Windows: crie um `.bat` que ativa o venv e roda `python -m etl.pipeline ...` e agende no Agendador de Tarefas.
- GitHub Actions: veja `.github/workflows/pipeline.yml` (cron `*/10 * * * *`).

## Dicas de solução de problemas
- Certifique-se de ter o Google Chrome instalado; o `webdriver-manager` baixa o ChromeDriver compatível.
- Se a página demorar, aumente `--timeout` ou `--step-delay`.
- Se trocar de cidade/área e estiver usando cache, mude o caminho do cache ou remova o arquivo existente.
