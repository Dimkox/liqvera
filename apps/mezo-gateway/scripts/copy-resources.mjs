import { cp, mkdir } from 'node:fs/promises';
await mkdir(new URL('../dist/contracts/', import.meta.url), { recursive: true });
await cp(new URL('../../../schemas/mezo-evidence/v1/', import.meta.url), new URL('../dist/contracts/', import.meta.url), { recursive: true });
await cp(new URL('../migrations/', import.meta.url), new URL('../dist/migrations/', import.meta.url), { recursive: true });
