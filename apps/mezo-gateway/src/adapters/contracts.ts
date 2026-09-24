import { readFile } from 'node:fs/promises';
import { Ajv2020 } from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { PublicError } from '../domain/model.js';
import { StateMachines, type Machine } from '../domain/states.js';
const BASE = 'https://schemas.liqvera.invalid/mezo-evidence/v1/';
export class Contracts {
  private readonly ajv = new Ajv2020({ strict: false, allErrors: false });
  private constructor(readonly states: StateMachines) { addFormats(this.ajv); }
  static async load(root: URL): Promise<Contracts> {
    const states = JSON.parse(await readFile(new URL('states.json',root),'utf8')) as { machines: Machine[] };
    const result = new Contracts(new StateMachines(states.machines));
    for (const file of ['primitives','reasons','quote-request','report','resources','error']) {
      result.ajv.addSchema(JSON.parse(await readFile(new URL(`${file}.schema.json`,root),'utf8')));
    }
    return result;
  }
  assert(name: string, value: unknown): void {
    const path = name === 'report' || name === 'error' ? `${name}.schema.json` : `resources.schema.json#/$defs/${name}`;
    const check = this.ajv.getSchema(`${BASE}${path}`);
    if (!check || !check(value)) throw new PublicError('ARTIFACT_INTEGRITY_FAILURE',503);
  }
}
