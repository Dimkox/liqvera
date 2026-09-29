export async function boundedFetch(fetcher, url, init, timeoutMs = 15_000) {
  const controller = new AbortController();
  const deadline = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetcher(url, { ...init, cache: "no-store", credentials: "omit", redirect: "error", signal: controller.signal });
    if (response.status >= 300 && response.status < 400) throw new Error("Redirects are forbidden at the payment boundary.");
    return response;
  } finally { clearTimeout(deadline); }
}

export async function boundedResponseJson(response, maximum) {
  const declared = response.headers.get("content-length");
  if (declared !== null && (!/^[0-9]+$/.test(declared) || Number(declared) > maximum)) throw new Error("Response exceeds the payment boundary.");
  if (!response.body) throw new Error("Payment response body missing.");
  const reader = response.body.getReader(); const chunks = []; let size = 0;
  while (true) { const item = await reader.read(); if (item.done) break; size += item.value.byteLength; if (size > maximum) { await reader.cancel(); throw new Error("Response exceeds the payment boundary."); } chunks.push(item.value); }
  const bytes = new Uint8Array(size); let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
  return JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
}
