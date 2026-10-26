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

## Resultado do 2º turno (Presidente)

A página `site/apuracao/` mostra o resultado final do 2º turno presidencial. Durante a apuração ela lia
o TSE ao vivo; agora lê a cópia final que o robô salva em `site/data/presidente_2t.json` (e as fotos em
`site/fotos/`). Se esse arquivo ainda não existir, ela lê o TSE uma única vez.

| Turno | Código da eleição | Endereço |
|---|---|---|
| 1º turno (04/10/2026) | 6257 | quem-senta-onde.pages.dev/apuracao/?eleicao=6257 |
| 2º turno (25/10/2026) | 6258 | quem-senta-onde.pages.dev/apuracao/ |

`?demo=1` mostra uma simulação com números inventados, para testar o visual.

A função `functions/tse/` que servia de reserva durante a apuração foi removida depois da eleição.

Contornos do mapa: malhas municipais do IBGE (via ibge-cidades-com-poligonos e kml-brasil, licenças ISC e MIT).

## Projeção do 2º turno

A página `site/projecao/` estima o resultado final a partir do que já foi apurado. Ela divide o
país em 143 pedaços (as 115 maiores cidades e capitais, o resto de cada estado e o exterior),
compara cada pedaço com o 1º turno (eleição 6257) e projeta as urnas que faltam. A conta roda no
navegador de quem visita. Agora que a eleição acabou, a página compara as leituras registradas
durante a noite (`site/data/historico_2t.json`) com o resultado final e mostra o índice de acerto. É uma
versão simplificada, inspirada em github.com/rodrigomahlmeister/projecao-2026-metodo, sem usar
o código dele. `?demo=1` mostra uma simulação.

## Mapa com zoom (regiões e cidades)

Na página de resultado, o mapa aproxima por região, estado e cidade. Os contornos ficam em `site/data/mapa/`
(gerados uma vez a partir das malhas do IBGE; veja `scripts/mapa/LEIAME.md`) e o resultado de cada cidade em
`site/data/pres2t_mun/`, que o robô baixa uma única vez do TSE depois da totalização final.

## Segurança

- Cabeçalhos de segurança (CSP e outros) em `site/_headers`. Por causa da CSP, o JavaScript das páginas fica em
  `site/js/` e não pode haver `<script>` nem `onclick=` dentro do HTML.
- As ações do GitHub ficam fixadas por SHA; o Dependabot (`.github/dependabot.yml`) abre um pull request quando houver versão nova.
- O token do Cloudflare deve ter só a permissão "Cloudflare Pages: Edit".

## Perguntas comuns

**Uma Assembleia aparece vazia.** O TSE só publica o arquivo de eleitos depois da totalização
final daquele estado. O site mostra o aviso e preenche sozinho na próxima rodada.

**O suplente que assumiu não aparece.** O TSE registra quem foi eleito. Posse de suplente
(por exemplo, quando um senador vira governador) é registro do Senado, não do TSE.

