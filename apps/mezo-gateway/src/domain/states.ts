import { PublicError, type AttemptState, type QuoteState, type RequestState } from './model.js';
// Events and guards are loaded from the frozen F2 contract. Every caller supplies
// each named guard explicitly; missing guards never default to success.
export interface Machine { name: string; initial: string; states: string[];
  transitions: { from: string; event: string; to: string; guards: string[]; effects: string[] }[] }
export class StateMachines {
  constructor(private readonly machines: Machine[]) {}
  next<T extends RequestState | QuoteState | AttemptState | 'NOT_ATTEMPTED' | 'ATTEMPTED'>(
    machine: string, from: T, event: string, guards: Record<string, boolean>): T {
    const step = this.machines.find(m => m.name === machine)?.transitions.find(t => t.from === from && t.event === event);
    if (!step || step.guards.some(g => guards[g] !== true)) throw new PublicError('INVALID_STATE', 409);
    return step.to as T;
  }
}
