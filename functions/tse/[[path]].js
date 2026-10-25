// Cloudflare Pages Function: repassa /tse/... para os arquivos públicos do TSE.
// Só é usada se o navegador não conseguir ler o TSE diretamente.
// Aceita apenas leituras de arquivos .json dentro de /oficial/.
export async function onRequestGet({ params, request }) {
  const parts = Array.isArray(params.path) ? params.path : [params.path];
  const path = parts.join("/");
  if (!/^[a-z0-9\/_.-]+\.json$/i.test(path) || path.includes("..")) {
    return new Response("Caminho inválido", { status: 400 });
  }
  const upstream = await fetch(`https://resultados.tse.jus.br/oficial/${path}`, {
    headers: { "If-None-Match": request.headers.get("If-None-Match") || "" },
    cf: { cacheTtl: 15, cacheEverything: true },
  });
  const headers = new Headers();
  for (const h of ["content-type", "etag", "last-modified"]) {
    const v = upstream.headers.get(h);
    if (v) headers.set(h, v);
  }
  headers.set("cache-control", "public, max-age=15");
  return new Response(upstream.body, { status: upstream.status, headers });
}
