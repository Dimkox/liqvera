export function boundedFetch(fetcher: typeof fetch, url: string, init: RequestInit, timeoutMs?: number): Promise<Response>;
export function boundedResponseJson(response: Response, maximum: number): Promise<unknown>;
