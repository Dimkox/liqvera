/**
 * Narrow protocol metadata for Liqvera's Mezo Testnet payment boundary.
 *
 * The exported ABI is intentionally limited to read-only verification and the
 * Transfer event. Payment authorization and settlement belong to the official
 * x402 SDK; this package does not expose token administration or a direct
 * transaction-construction surface.
 */

export const MEZO_TESTNET = {
  name: "Mezo Matsnet",
  chainId: 31611,
  caip2: "eip155:31611",
  rpcUrl: "https://rpc.test.mezo.org",
  explorerUrl: "https://explorer.test.mezo.org",
} as const;

export type MezoTestnetChainId = typeof MEZO_TESTNET.chainId;
export type MezoTestnetNetwork = typeof MEZO_TESTNET.caip2;

export const MUSD_TESTNET = {
  name: "Mezo USD",
  symbol: "MUSD",
  address: "0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503",
  decimals: 18,
} as const;

export type MusdTestnetAddress = typeof MUSD_TESTNET.address;

export const MUSD_TRANSFER_EVENT = {
  name: "Transfer",
  signature: "Transfer(address,address,uint256)",
  topic0: "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
  inputs: [
    { name: "from", type: "address", indexed: true },
    { name: "to", type: "address", indexed: true },
    { name: "value", type: "uint256", indexed: false },
  ],
} as const;

export const MUSD_PERMIT = {
  standard: "EIP-2612",
  supportsEip2612: true,
  supportsPermit2: true,
  domainName: MUSD_TESTNET.name,
  domainVersion: "1",
  primaryType: "Permit",
  fields: [
    { name: "owner", type: "address" },
    { name: "spender", type: "address" },
    { name: "value", type: "uint256" },
    { name: "nonce", type: "uint256" },
    { name: "deadline", type: "uint256" },
  ],
} as const;

/**
 * Read-only verification ABI derived verbatim, item by item, from the pinned
 * Matsnet MUSD deployment artifact. The full upstream ABI remains vendored.
 */
export const MUSD_ABI = [
  {
    inputs: [],
    name: "name",
    outputs: [{ internalType: "string", name: "", type: "string" }],
    stateMutability: "view",
    type: "function",
  },
  {
    inputs: [],
    name: "symbol",
    outputs: [{ internalType: "string", name: "", type: "string" }],
    stateMutability: "view",
    type: "function",
  },
  {
    inputs: [],
    name: "decimals",
    outputs: [{ internalType: "uint8", name: "", type: "uint8" }],
    stateMutability: "view",
    type: "function",
  },
  {
    inputs: [{ internalType: "address", name: "account", type: "address" }],
    name: "balanceOf",
    outputs: [{ internalType: "uint256", name: "", type: "uint256" }],
    stateMutability: "view",
    type: "function",
  },
  {
    inputs: [
      { internalType: "address", name: "owner", type: "address" },
      { internalType: "address", name: "spender", type: "address" },
    ],
    name: "allowance",
    outputs: [{ internalType: "uint256", name: "", type: "uint256" }],
    stateMutability: "view",
    type: "function",
  },
  {
    inputs: [{ internalType: "address", name: "owner", type: "address" }],
    name: "nonces",
    outputs: [{ internalType: "uint256", name: "", type: "uint256" }],
    stateMutability: "view",
    type: "function",
  },
  {
    inputs: [],
    name: "DOMAIN_SEPARATOR",
    outputs: [{ internalType: "bytes32", name: "", type: "bytes32" }],
    stateMutability: "view",
    type: "function",
  },
  {
    inputs: [],
    name: "eip712Domain",
    outputs: [
      { internalType: "bytes1", name: "fields", type: "bytes1" },
      { internalType: "string", name: "name", type: "string" },
      { internalType: "string", name: "version", type: "string" },
      { internalType: "uint256", name: "chainId", type: "uint256" },
      {
        internalType: "address",
        name: "verifyingContract",
        type: "address",
      },
      { internalType: "bytes32", name: "salt", type: "bytes32" },
      {
        internalType: "uint256[]",
        name: "extensions",
        type: "uint256[]",
      },
    ],
    stateMutability: "view",
    type: "function",
  },
  {
    anonymous: false,
    inputs: [
      {
        indexed: true,
        internalType: "address",
        name: "from",
        type: "address",
      },
      {
        indexed: true,
        internalType: "address",
        name: "to",
        type: "address",
      },
      {
        indexed: false,
        internalType: "uint256",
        name: "value",
        type: "uint256",
      },
    ],
    name: "Transfer",
    type: "event",
  },
] as const;

export function isMezoTestnetChainId(
  chainId: unknown,
): chainId is MezoTestnetChainId {
  return chainId === MEZO_TESTNET.chainId;
}

export function assertMezoTestnetChainId(
  chainId: unknown,
): asserts chainId is MezoTestnetChainId {
  if (!isMezoTestnetChainId(chainId)) {
    throw new Error(`Expected Mezo Testnet chain ID ${MEZO_TESTNET.chainId}`);
  }
}
