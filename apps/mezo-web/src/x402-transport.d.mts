export function boundedFetch(fetcher: typeof fetch, url: string, init: RequestInit, timeoutMs?: number): Promise<Response>;
export function boundedFetchJson(fetcher: typeof fetch, url: string, init: RequestInit, maximum: number, timeoutMs?: number): Promise<{response: Response; body: unknown}>;
export function boundedResponseJson(response: Response, maximum: number): Promise<unknown>;
