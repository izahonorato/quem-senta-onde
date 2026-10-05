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

## Perguntas comuns

**Uma Assembleia aparece vazia.** O TSE só publica o arquivo de eleitos depois da totalização
final daquele estado. O site mostra o aviso e preenche sozinho na próxima rodada.

**O suplente que assumiu não aparece.** O TSE registra quem foi eleito. Posse de suplente
(por exemplo, quando um senador vira governador) é registro do Senado, não do TSE.

