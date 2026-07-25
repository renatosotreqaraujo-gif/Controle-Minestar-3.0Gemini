# Ping Monitor v4 — Sotreq CAT

Sistema de monitoramento de ping por equipamento, com login e perfis de
usuário, teste pontual via CMD, monitoramento contínuo controlado
manualmente, e identidade visual CAT.

## Primeiro acesso

Usuário padrão criado automaticamente na primeira execução:

```
usuário: admin
senha:   admin123
```

**Troque essa senha assim que possível** (crie um novo admin com senha própria
pela tela de "Usuários" e remova ou reserve o `admin` padrão).

## Perfis de usuário

| Perfil | Pode |
|---|---|
| **Admin** | Tudo, incluindo cadastrar/remover usuários e ver o log de auditoria |
| **Operador** | Tudo, exceto gerenciar usuários (importar planilha, editar ativos, controlar play/pause do monitoramento, testar ping) |
| **Leitura** | Só visualizar o painel e testar ping pontual (aba 1) |

Todo login/logout e ação importante (criar usuário, importar planilha,
editar ativo, iniciar/parar monitoramento, testar ping) fica registrado
no log de auditoria, visível para o Admin.

## As duas abas

**1 · Teste Pontual** — escolha um equipamento, marque quais dos 4 ativos
quer testar, escolha pontual (4 pacotes) ou contínuo (`-t`), e o sistema
abre uma janela de CMD por ativo já rodando o ping. Só abre CMD de verdade
quando rodando no Windows (é o caso do `.exe`).

**2 · Monitoramento** — grade de todos os equipamentos, com ícone por tipo
(caminhão, escavadeira, trator, carregadeira, perfuratriz, motoniveladora
etc.) e um indicador por ativo (MEMS / DISPLAY / DIM-RIM-PLE / AVI LTE).
**Não inicia sozinho** — só começa a pingar quando você aperta
"Iniciar Monitoramento", e para quando aperta de novo. Filtros de grupo
(tipo de equipamento), status e busca, com contadores Geral e Filtrado.
Clique num indicador de ativo pra ver o histórico de latência — quedas
aparecem marcadas em vermelho no gráfico.

## Importando os ativos

Botão **Importar Excel** na aba de Monitoramento, apontando para a aba
**"IPs"** da planilha de automação (ex: `IPs_Automação_Mina_Convencional`).
Cada linha (TAG) vira um equipamento com 4 ativos: MEMS, DISPLAY (IP da
coluna G407/G610), DIM/RIM/PLE e AVI LTE. Reimportar atualiza os IPs sem
duplicar equipamentos.

O tipo de equipamento e o ícone são deduzidos automaticamente pelo prefixo
do TAG (CA=caminhão, EC/ES=escavadeira, PC=carregadeira, TT/TU=trator,
PZ=perfuratriz, MA/GD=motoniveladora, BM/1LT=veículo de apoio/leve).

## Como instalar (sem precisar de Python nos PCs finais)

Igual à versão anterior — veja a seção completa mais abaixo. Resumo:

- **Opção A (sem instalar nada):** suba este projeto num repositório GitHub
  (o workflow `.github/workflows/build.yml` já está incluso) e baixe o
  `.exe` pronto na aba Actions → Artifacts.
- **Opção B:** rode `build_windows.bat` numa máquina Windows com Python.

Depois, copie só o `PingMonitor.exe` gerado para qualquer PC Windows.

### Opção A — GitHub Actions (sem instalar absolutamente nada na sua máquina)

1. Crie uma conta gratuita em [github.com](https://github.com).
2. Crie um repositório novo (pode ser privado) e envie os arquivos do
   projeto (extraia o zip antes — pastas precisam existir de verdade no
   repositório, não dentro de um zip).
3. Vá na aba **Actions**. O build roda sozinho a cada envio de arquivo, ou
   clique em "Run workflow".
4. Quando ficar verde, baixe o artifact **PingMonitor-windows** — dentro
   está o `.exe`.

### Opção B — Build local (`build_windows.bat`)

Numa máquina Windows com Python instalado, dê dois cliques em
`build_windows.bat`. O `.exe` fica em `dist\PingMonitor.exe`.

### Rodando o .exe

Dois cliques no `PingMonitor.exe` — abre uma janela de console e o
navegador sozinho em `http://localhost:8000`. Outros PCs da rede acessam
via `http://<IP-deste-PC>:8000`. O banco de dados (`ping_tool.db`) e a
chave de sessão (`.secret_key`) ficam salvos ao lado do `.exe`.

## Fuso horário

Tudo é salvo internamente em UTC e convertido para horário de Brasília
(America/Sao_Paulo, UTC-3) na hora de exibir — não precisa configurar nada.

## Ajustes finos

- `app/monitoring.py`: `CYCLE_SECONDS` (30s) e `FAILURE_THRESHOLD` (2
  falhas seguidas até alertar).
- `app/ping_service.py`: `MAX_CONCURRENT_PINGS`, `PING_COUNT`, `PING_TIMEOUT`.
- `app/equipment_types.py`: mapa de prefixo de TAG → tipo/ícone de
  equipamento — ajuste aqui se algum prefixo novo aparecer sem classificação.
