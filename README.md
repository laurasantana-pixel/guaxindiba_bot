# Guaxindiba Bot

Ferramentas para coletar e analisar focos de queimadas usando dados do TerraBrasilis.

## Diagrama do projeto

```
python -m etl.pipeline
        │
        ├── etl.extract.terrabrasilis.fetch_fire_data
        │       └─ Abre o TerraBrasilis com Selenium e coleta a tabela de focos
        │
        ├── etl.extract.reserve.get_reserve_geometry
        │       └─ Busca a geometria da EEE Guaxindiba no OpenStreetMap (usa cache opcional)
        │
        ├── etl.transform.spatial.mark_points_inside
        │       └─ Converte para GeoDataFrame e marca pontos que intersectam a reserva
        │
        └── etl.load.csv
                ├─ save_dataframe → grava CSV com os focos processados
                └─ save_geometry  → grava GeoJSON da geometria (opcional)
```

### Pontos importantes

- **Configuração centralizada**: `etl.config` carrega variáveis do `.env` e já inicializa o logging ao ser importado.
- **Orquestração flexível**: `etl.pipeline.PipelineConfig` permite substituir funções de extração, transformação e gravação, além de habilitar/desabilitar marcação espacial ou persistência de geometria.
- **Coleta automatizada**: `etl.extract.terrabrasilis.fetch_fire_data` usa Selenium/ChromeDriver, com opções para headless, destaque visual dos elementos e filtros customizados (continente, país, estado e satélite).
- **Geometria da reserva**: `etl.extract.reserve.get_reserve_geometry` consulta o OpenStreetMap, normaliza nomes e reaproveita cache GeoJSON quando disponível.
- **Transformação espacial**: `etl.transform.spatial.mark_points_inside` aceita `DataFrame`, `GeoDataFrame` ou mapeamentos de geometrias e adiciona colunas booleanas indicando interseção.
- **Persistência resiliente**: `etl.load.csv.save_dataframe` e `save_geometry` garantem criação de diretórios antes de salvar CSV/GeoJSON e validam tipos de entrada.

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
   pip install -r requirements.txt
   ```

   O `requirements.txt` já inclui dependências opcionais como `lxml` (usada
   pelo pandas/geopandas ao ler dados do TerraBrasilis/BDQueimadas). Se você
   recebeu erros de `ImportError` para `lxml`, atualize o ambiente com o
   comando acima para garantir que o pacote foi instalado.

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
   - `--city-name "NOME DA CIDADE"`: filtra os focos retornados pelo
     TerraBrasilis/BDQueimadas para o município informado (comparação textual
     por colunas de município/município/cidade). Caso nenhuma coluna compatível
     exista, o pipeline avisa no log e segue sem filtrar.
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

### Agendando a execução a cada 10 minutos (Windows)

- **Agendamento local com Agendador de Tarefas**:
  1. Crie um arquivo `run_pipeline.bat` no diretório do projeto:
     ```bat
     @echo off
     cd /d C:\caminho\para\guaxindiba_bot
     call .venv\Scripts\activate
     python -m etl.pipeline --fires-output data\focos_processados.csv --geometry-output data\reserva.geojson --reserve-cache cache\reserva.geojson --headless
     ```
  2. Abra **Agendador de Tarefas → Criar Tarefa Básica**.
  3. Defina o gatilho como **Diariamente** e, nas configurações avançadas, marque **Repetir a cada: 10 minutos**.
  4. Em **Ação**, escolha **Iniciar um programa** e selecione o `run_pipeline.bat`.
  5. Marque **Executar com privilégios mais altos** para permitir gravação nos diretórios configurados.

- **Hospedagem/automação para rodar a cada 10 minutos**:
  - **PC ou servidor Windows**: usar o Agendador de Tarefas (acima) em uma máquina ligada/VM Windows.
  - **Máquina virtual Windows em nuvem**: hospedar o projeto em uma VM do Azure/AWS/GCP com o mesmo agendamento.
   - **GitHub Actions** (runner `ubuntu-latest` ou `windows-latest`): criar um workflow agendado com cron como `*/10 * * * *` para baixar o repositório, preparar o ambiente e rodar `python -m etl.pipeline`.

### Execução agendada no GitHub Actions (a cada 10 minutos)

O repositório já inclui um workflow funcional em `.github/workflows/pipeline.yml` que roda a cada 10 minutos (cron `*/10 * * * *`) e também pode ser disparado manualmente. Ele:

- Usa `ubuntu-latest` com Python 3.11, cache de dependências (`requirements.txt`).
- Executa `python -m etl.pipeline` em modo headless e armazena saídas em `data/` e `cache/`. O workflow padrão coleta diretamente do TerraBrasilis/BDQueimadas; se o ambiente não tiver acesso à internet, adicione manualmente a flag `--offline-sample` para usar os dados de exemplo versionados.
- Publica os artefatos `focos_processados.csv`, `reserva.geojson` e o cache da geometria ao final da execução.

Para customizar:

- Ajuste o cron ou runner editando `.github/workflows/pipeline.yml`.
- Inclua flags adicionais na etapa **Run pipeline** conforme necessário (`--no-mark-inside`, `--skip-geometry-output`, `--offline-sample`, etc.).
- Caso precise de variáveis sensíveis, defina segredos no repositório e referencie-os como `env:` ou `secrets.*` no workflow.

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
