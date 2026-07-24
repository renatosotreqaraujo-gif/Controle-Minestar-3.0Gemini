# Ping Monitor v3

Nova versão da ferramenta de teste de ping, feita do zero em Python.

## O que muda em relação à v2.0

| v2.0 | v3 |
|---|---|
| Abre o CMD e roda `ping` um ativo por vez | Ping nativo (ICMP), assíncrono, dezenas em paralelo |
| Sem histórico | Histórico de latência e disponibilidade por ativo, com gráfico |
| Sem alerta | Alerta visual (toast na tela) quando um ativo cai, com confirmação por N falhas seguidas para evitar alarme falso |
| Sem relatório | Exportação de relatório em Excel (uptime %, RTT médio, status atual) |
| Cadastro manual único | Importação/atualização em massa via planilha Excel + cadastro manual na própria ferramenta |
| Uso local, uma máquina por vez | Aplicação web — qualquer pessoa na rede interna acessa pelo navegador |

## Como instalar (sem precisar de Python nos PCs finais)

A ideia é gerar **um único arquivo `PingMonitor.exe`** uma vez, e depois copiar esse
arquivo para qualquer PC Windows — nesses PCs finais não precisa instalar Python
nem nada, é só dar dois cliques.

Existem dois jeitos de gerar esse `.exe`:

### Opção A — GitHub Actions (sem instalar absolutamente nada na sua máquina)

O projeto já vem com um arquivo `.github/workflows/build.yml` pronto. O GitHub
compila o `.exe` para você, numa máquina Windows na nuvem dele.

1. Crie uma conta gratuita em [github.com](https://github.com) (se ainda não tiver).
2. Crie um repositório novo (pode ser privado) e envie esta pasta do projeto
   inteira para lá (pelo site mesmo: "Add file" → "Upload files", arraste tudo).
3. Vá na aba **Actions** do repositório. O build já roda sozinho assim que você
   sobe os arquivos (ou clique em "Run workflow" para rodar na hora).
4. Aguarde o ícone ficar verde (leva 2–4 minutos).
5. Clique no build concluído → na seção **Artifacts**, baixe o `PingMonitor-windows.zip`.
6. Dentro dele está o `PingMonitor.exe`, pronto pra copiar para qualquer PC Windows.

### Opção B — Build local (`build_windows.bat`)

Se preferir gerar o `.exe` numa máquina Windows com Python já instalado:

1. Extraia esta pasta do projeto.
2. Dê dois cliques em **`build_windows.bat`**.
3. Aguarde (a primeira vez demora alguns minutos, baixando as dependências e
   empacotando).
4. Ao final, o arquivo pronto estará em: `dist\PingMonitor.exe`

### Distribuir para os PCs finais (depois de gerado o .exe, por qualquer opção)

1. Copie **apenas o arquivo `dist\PingMonitor.exe`** para qualquer PC Windows
   (pendrive, rede, e-mail — como preferir). Não precisa copiar mais nada.
2. Dê dois cliques em `PingMonitor.exe`.
3. Uma janela preta (console) abre mostrando que o servidor subiu, e o navegador
   abre sozinho em `http://localhost:8000`.
4. Para acessar de outras máquinas da rede: `http://<IP-deste-PC>:8000`
5. Para parar, feche a janela preta (ou Ctrl+C).

> O banco de dados (`ping_tool.db`) é criado automaticamente na mesma pasta onde
> o `.exe` está — cada instalação tem seus próprios dados, independente das outras.

### Alternativa — rodar direto com Python (modo desenvolvimento)

Se preferir rodar sem gerar o `.exe` (útil para desenvolvimento/testes):
```
pip install -r requirements.txt
python run.py
```
ou, sem abrir o navegador automaticamente:
```
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Primeiro uso

1. Abra o painel no navegador.
2. Clique em **Importar Excel** e envie a planilha atual de ativos (precisa ter uma coluna de IP; colunas de nome e grupo são opcionais e reconhecidas automaticamente por vários nomes comuns, ex: "Nome", "IP", "Grupo").
3. O monitoramento começa sozinho, em ciclos de 30 segundos (ajustável em `app/main.py`, constante `CYCLE_SECONDS`).
4. Para adicionar um ativo novo sem mexer na planilha, use o botão **+ Ativo**.
5. Clique em um card para ver o histórico de latência; duplo clique para editar.

## Pontos de ajuste importantes

- `app/ping_service.py`:
  - `MAX_CONCURRENT_PINGS` (padrão 40) — quantos pings simultâneos. Em redes mais sensíveis, reduza.
  - `PING_COUNT` / `PING_TIMEOUT` — quantos pacotes e tempo de espera por tentativa.
- `app/main.py`:
  - `CYCLE_SECONDS` (padrão 30) — intervalo entre rodadas de ping.
  - `FAILURE_THRESHOLD` (padrão 2) — quantas falhas seguidas até disparar o alerta de queda.

## Banco de dados

Por padrão usa SQLite (`ping_tool.db`, criado automaticamente na primeira execução). Se no futuro quiser
usar o mesmo SQL Server do fleet monitoring, basta trocar a `DATABASE_URL` em `app/database.py` por uma
connection string SQL Server (via `pyodbc`).

## Observação sobre privilégios de rede

O ping é feito com `privileged=False` (via `icmplib`), o que evita precisar rodar o servidor como
administrador/root. Em algumas distribuições Linux pode ser necessário liberar um range de ping não
privilegiado (`net.ipv4.ping_group_range`) — no Windows normalmente funciona sem ajustes.
