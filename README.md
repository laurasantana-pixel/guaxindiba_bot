# Guaxindiba Bot

Ferramentas para coletar e analisar focos de queimadas usando dados do TerraBrasilis.

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
