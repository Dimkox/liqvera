import { cp, mkdir } from 'node:fs/promises';
const target=process.argv.includes('--test')?'../test-dist/src/':'../dist/';
await mkdir(new URL(`${target}contracts/`, import.meta.url), { recursive: true });
await cp(new URL('../../../schemas/mezo-evidence/v1/', import.meta.url), new URL(`${target}contracts/`, import.meta.url), { recursive: true });
await cp(new URL('../migrations/', import.meta.url), new URL(`${target}migrations/`, import.meta.url), { recursive: true });
await cp(new URL('../src/p3-plan.mjs', import.meta.url), new URL(`${target}p3-plan.mjs`, import.meta.url));
