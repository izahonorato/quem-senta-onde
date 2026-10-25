# Quem senta onde

Site que mostra quem ocupa cada cadeira do Senado, da Câmara dos Deputados, das Assembleias
Legislativas e das câmaras municipais. **Todos os nomes, partidos e eleitos vêm do TSE.**
Um robô gratuito do GitHub confere os arquivos oficiais a cada hora e, quando algo muda,
republica o site no **Cloudflare Pages** (gratuito, tráfego ilimitado e permite anúncios).

## De onde vêm os dados

| O quê | Fonte oficial do TSE |
|---|---|
| Senadores, deputados federais, estaduais e distritais eleitos em 2026 | resultados.tse.jus.br (eleição 6259) |
| Senadores eleitos em 2022 (mandato até 2031) | Portal de Dados Abertos (candidatos 2022) |
| Prefeitos e vereadores eleitos em 2024 | Portal de Dados Abertos (candidatos 2024) |

A única informação que não vem do TSE é a cor de esquerda/centro/direita, que é uma
classificação acadêmica explicada no rodapé do site.

## Apuração ao vivo (Presidente)

A página `site/apuracao/` mostra a apuração presidencial em tempo real. Ela não depende do robô:
o navegador de quem visita lê direto os arquivos públicos do TSE a cada 30 segundos.

| Turno | Código da eleição | Endereço |
|---|---|---|
| 1º turno (04/10/2026) | 6257 | quem-senta-onde.pages.dev/apuracao/?eleicao=6257 |
| 2º turno (25/10/2026) | 6258 | quem-senta-onde.pages.dev/apuracao/ |

`?demo=1` mostra uma simulação com números inventados, para testar o visual.

Se um dia o TSE bloquear a leitura direta pelo navegador, a página passa a buscar os mesmos
arquivos por `functions/tse/[[path]].js`, uma função do Cloudflare Pages que só repassa
arquivos `.json` de `resultados.tse.jus.br/oficial/`. Ela é publicada junto com o site pelo
`wrangler pages deploy`, que procura a pasta `functions` na raiz do repositório.

Mapa dos estados: MapSVG, licença CC BY 4.0.

## Projeção ao vivo

A página `site/projecao/` estima o resultado final a partir do que já foi apurado. Ela divide o
país em 143 pedaços (as 115 maiores cidades e capitais, o resto de cada estado e o exterior),
compara cada pedaço com o 1º turno (eleição 6257) e projeta as urnas que faltam. A conta roda no
navegador de quem visita, a cada minuto. O método está explicado na própria página. É uma
versão simplificada, inspirada em github.com/rodrigomahlmeister/projecao-2026-metodo, sem usar
o código dele. `?demo=1` mostra uma simulação.

## Perguntas comuns

**Uma Assembleia aparece vazia.** O TSE só publica o arquivo de eleitos depois da totalização
final daquele estado. O site mostra o aviso e preenche sozinho na próxima rodada.

**O suplente que assumiu não aparece.** O TSE registra quem foi eleito. Posse de suplente
(por exemplo, quando um senador vira governador) é registro do Senado, não do TSE.

