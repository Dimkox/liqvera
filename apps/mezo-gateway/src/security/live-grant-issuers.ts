/** Release-reviewed issuer trust root. Rotation requires a code/release edit. */
export const LIVE_GRANT_ISSUERS=Object.freeze({
  '468688f235df364eee8f37b3815808f2c6e4fc09dcc96015269b64405d0f8708':
    'fab4189d8fa6e7fa0c488e74914295e7b5fc9941f87348db7eaa40a9988e6822',
} as const);

export function assertApprovedLiveGrantIssuer(keyId:string,publicKey:Uint8Array):void{
  const expected=LIVE_GRANT_ISSUERS[keyId as keyof typeof LIVE_GRANT_ISSUERS];
  if(expected===undefined||Buffer.from(publicKey).toString('hex')!==expected)
    throw new Error('LIVE_GRANT_ISSUER_UNAPPROVED');
}
