import { createHash } from 'node:crypto';
import { address, INSTRUMENT, PublicError, type QuoteInput } from '../domain/model.js';
export const digest = (bytes: string | Buffer): string => createHash('sha256').update(bytes).digest('hex');
export function capability(header: string | undefined): string {
  const token = /^Bearer ([A-Za-z0-9_-]{43})$/.exec(header ?? '')?.[1];
  if (!token) throw new PublicError('UNAUTHORIZED', 401);
  const raw = Buffer.from(token, 'base64url');
  if (raw.length !== 32 || raw.toString('base64url') !== token) throw new PublicError('UNAUTHORIZED', 401);
  return digest(raw);
}
export function idempotencyKey(value: string | undefined): string {
  if (!value || value.length > 128 || !/^[A-Za-z0-9._:-]+(?![\s\S])/.test(value)) throw new PublicError('INVALID_INPUT', 422);
  return value;
}
export function quoteInput(input: unknown): QuoteInput {
  if (!input || typeof input !== 'object' || Array.isArray(input)) throw new PublicError('INVALID_INPUT', 422);
  const body = input as Record<string, unknown>;
  if (Object.keys(body).sort().join(',') !== 'expected_payer,instrument_id,quantity_base,side') throw new PublicError('INVALID_INPUT', 422);
  if (body.instrument_id !== INSTRUMENT) throw new PublicError('UNSUPPORTED_INSTRUMENT', 422);
  if (body.side !== 'BUY' && body.side !== 'SELL') throw new PublicError('INVALID_INPUT', 422);
  if (typeof body.quantity_base !== 'string' || body.quantity_base.length > 32 ||
      !/^[+]?[0-9]+([.][0-9]{1,8})?$/.test(body.quantity_base) || /\s/.test(body.quantity_base)) throw new PublicError('INVALID_INPUT', 422);
  const [whole = '', fraction = ''] = body.quantity_base.replace(/^\+/, '').split('.');
  const integer = whole.replace(/^0+(?=\d)/, '');
  const decimal = fraction.replace(/0+$/, '');
  const quantity = decimal ? `${integer}.${decimal}` : integer;
  if (BigInt(integer + fraction.padEnd(8, '0')) <= 0n) throw new PublicError('INVALID_INPUT', 422);
  return { instrument_id: INSTRUMENT, side: body.side, quantity_base: quantity, expected_payer: address(body.expected_payer) };
}
export function paymentHeader(value: string): string {
  if (value.length > 21848 || !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(value))
    throw new PublicError('PAYMENT_REJECTED', 409);
  const bytes = Buffer.from(value, 'base64');
  if (bytes.length === 0 || bytes.length > 16384 || bytes.toString('base64') !== value) throw new PublicError('PAYMENT_REJECTED', 409);
  return value;
}
// Closed JSON request decoder also rejects duplicate field names. The four
// canonical input fields are scalars, so nested JSON is never accepted here.
export function decodeQuoteBody(raw: Buffer): QuoteInput {
  if (raw.length > 16384) throw new PublicError('INVALID_INPUT', 422);
  const source = new TextDecoder('utf-8', { fatal: true }).decode(raw);
  const keys = [...source.matchAll(/"((?:\\.|[^"\\])*)"\s*:/g)].map(m => JSON.parse(`"${m[1]}"`) as string);
  if (keys.length !== 4 || new Set(keys).size !== 4) throw new PublicError('INVALID_INPUT', 422);
  return quoteInput(JSON.parse(source));
}
