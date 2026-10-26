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

/** Mainnet metadata: https://mezo.org/docs/developers/getting-started/musd-payments-x402/ */
export const MEZO_MAINNET = {
  name: "Mezo Mainnet", chainId: 31612, caip2: "eip155:31612",
  rpcUrl: "https://mezo-mainnet.boar.network", explorerUrl: "https://explorer.mezo.org",
} as const;
export const MUSD_MAINNET = {
  name: "Mezo USD", symbol: "MUSD", address: "0xdD468A1DDc392dcdbEf6db6e34E89AA338F9F186", decimals: 18,
} as const;
export function mezoNetwork(name: unknown = "testnet") {
  if (name === "testnet") return {name: "testnet", chain: MEZO_TESTNET, asset: MUSD_TESTNET} as const;
  if (name === "mainnet") return {name: "mainnet", chain: MEZO_MAINNET, asset: MUSD_MAINNET} as const;
  throw new Error("MEZO_NETWORK_INVALID");
}

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

export const X402_PERMIT2 = {
  assetTransferMethod: "permit2",
  permit2Address: "0x000000000022D473030F116dDEE9F6B43aC78BA3",
  exactProxyAddress: "0x402085c248EeA27D92E8b30b2C58ed07f9E20001",
  approvalMode: "eip2612-gas-sponsoring",
  requiredExtension: "eip2612GasSponsoring",
  extensionDescription: "The facilitator accepts EIP-2612 gasless Permit to `Permit2` canonical contract.",
  authorizationIdentityVersion: "liqvera-permit2-eip2612-identity/v1",
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

/** Testnet basic pools: https://mezo.org/docs/developers/features/mezo-pools/#testnet--basic-pool-contracts
 * ABI provenance and proxy implementation observations: ../source-lock.json.
 * These addresses authorize read-only analytics only.
 */
export const MEZO_TESTNET_DEX = {
  router: "0x9a1ff7FE3a0F69959A3fBa1F1e5ee18e1A9CD7E9",
  poolFactory: "0x4947243CC818b627A5D06d14C4eCe7398A23Ce1A",
  musdBtcPool: "0xd16A5Df82120ED8D626a1a15232bFcE2366d6AA9",
  // Observed token1() on the sourced pool; see fixed-block protocol probe.
  btcToken: "0x7b7C000000000000000000000000000000000000",
} as const;

export const MEZO_TESTNET_POOL_ABI = [
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "amountIn",
        "type": "uint256"
      },
      {
        "internalType": "address",
        "name": "tokenIn",
        "type": "address"
      }
    ],
    "name": "getAmountOut",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "getReserves",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "_reserve0",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "_reserve1",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "_blockTimestampLast",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "stable",
    "outputs": [
      {
        "internalType": "bool",
        "name": "",
        "type": "bool"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "token0",
    "outputs": [
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "token1",
    "outputs": [
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  }
] as const;

export const MEZO_TESTNET_ROUTER_ABI = [
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "amountIn",
        "type": "uint256"
      },
      {
        "components": [
          {
            "internalType": "address",
            "name": "from",
            "type": "address"
          },
          {
            "internalType": "address",
            "name": "to",
            "type": "address"
          },
          {
            "internalType": "bool",
            "name": "stable",
            "type": "bool"
          },
          {
            "internalType": "address",
            "name": "factory",
            "type": "address"
          }
        ],
        "internalType": "struct IRouter.Route[]",
        "name": "routes",
        "type": "tuple[]"
      }
    ],
    "name": "getAmountsOut",
    "outputs": [
      {
        "internalType": "uint256[]",
        "name": "amounts",
        "type": "uint256[]"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "tokenA",
        "type": "address"
      },
      {
        "internalType": "address",
        "name": "tokenB",
        "type": "address"
      },
      {
        "internalType": "bool",
        "name": "stable",
        "type": "bool"
      },
      {
        "internalType": "address",
        "name": "_factory",
        "type": "address"
      }
    ],
    "name": "getReserves",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "reserveA",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "reserveB",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "amountIn",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "amountOutMin",
        "type": "uint256"
      },
      {
        "components": [
          {
            "internalType": "address",
            "name": "from",
            "type": "address"
          },
          {
            "internalType": "address",
            "name": "to",
            "type": "address"
          },
          {
            "internalType": "bool",
            "name": "stable",
            "type": "bool"
          },
          {
            "internalType": "address",
            "name": "factory",
            "type": "address"
          }
        ],
        "internalType": "struct IRouter.Route[]",
        "name": "routes",
        "type": "tuple[]"
      },
      {
        "internalType": "address",
        "name": "to",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "deadline",
        "type": "uint256"
      }
    ],
    "name": "swapExactTokensForTokens",
    "outputs": [
      {
        "internalType": "uint256[]",
        "name": "amounts",
        "type": "uint256[]"
      }
    ],
    "stateMutability": "nonpayable",
    "type": "function"
  }
] as const;

export const MEZO_TESTNET_ERC20_TRADE_ABI = [
  {"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
] as const;

export const MEZO_TESTNET_POOL_FACTORY_ABI = [
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "pool",
        "type": "address"
      },
      {
        "internalType": "bool",
        "name": "_stable",
        "type": "bool"
      }
    ],
    "name": "getFee",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  }
] as const;

/** Testnet MUSD proxies: https://mezo.org/docs/developers/musd/musd-redemptions/#contract-addresses
 * Narrow read-only ABI exports derive from the separately retained verified
 * implementation artifacts. Proxy discovery metadata remains in source-lock.json.
 */
export const MEZO_TESTNET_TROVES = {
  troveManager: "0xE47c80e8c23f6B4A1aE41c34837a0599D5D16bb0",
  borrowerOperations: "0xCdF7028ceAB81fA0C6971208e83fa7872994beE5",
  hintHelpers: "0x4e4cBA3779d56386ED43631b4dCD6d8EacEcBCF6",
  sortedTroves: "0x722E4D24FD6Ff8b0AC679450F3D91294607268fA",
  priceFeed: "0x86bCF0841622a5dAC14A313a15f96A95421b9366",
} as const;

export const MEZO_TESTNET_BORROWER_OPERATIONS_ABI = [
  {"inputs":[],"name":"governableVariables","outputs":[{"internalType":"contract IGovernableVariables","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"borrowingRate","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"_debt","type":"uint256"}],"name":"getBorrowingFee","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"getEntireSystemColl","outputs":[{"internalType":"uint256","name":"entireSystemColl","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"getEntireSystemDebt","outputs":[{"internalType":"uint256","name":"entireSystemDebt","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"_amount","type":"uint256"},{"internalType":"address","name":"_upperHint","type":"address"},{"internalType":"address","name":"_lowerHint","type":"address"}],"name":"withdrawMUSD","outputs":[],"stateMutability":"nonpayable","type":"function"},
  {
    "inputs": [],
    "name": "minNetDebt",
    "outputs": [{"internalType":"uint256","name":"","type":"uint256"}],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "_upperHint",
        "type": "address"
      },
      {
        "internalType": "address",
        "name": "_lowerHint",
        "type": "address"
      }
    ],
    "name": "addColl",
    "outputs": [],
    "stateMutability": "payable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "_amount",
        "type": "uint256"
      },
      {
        "internalType": "address",
        "name": "_upperHint",
        "type": "address"
      },
      {
        "internalType": "address",
        "name": "_lowerHint",
        "type": "address"
      }
    ],
    "name": "repayMUSD",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
] as const;

export const MEZO_TESTNET_HINT_HELPERS_ABI = [
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "_coll",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "_debt",
        "type": "uint256"
      }
    ],
    "name": "computeNominalCR",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "pure",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "_CR",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "_numTrials",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "_inputRandomSeed",
        "type": "uint256"
      }
    ],
    "name": "getApproxHint",
    "outputs": [
      {
        "internalType": "address",
        "name": "hintAddress",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "diff",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "latestRandomSeed",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  }
] as const;

export const MEZO_TESTNET_TROVE_MANAGER_ABI = [
  {"inputs":[{"internalType":"address","name":"_borrower","type":"address"}],"name":"getTroveMaxBorrowingCapacity","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {
    "inputs": [],
    "name": "CCR",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "DECIMAL_PRECISION",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "MCR",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "MUSD_GAS_COMPENSATION",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "_borrower",
        "type": "address"
      },
      {
        "internalType": "uint256",
        "name": "_price",
        "type": "uint256"
      }
    ],
    "name": "getCurrentICR",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "_borrower",
        "type": "address"
      }
    ],
    "name": "getEntireDebtAndColl",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "coll",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "principal",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "interest",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "pendingCollateral",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "pendingPrincipal",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "pendingInterest",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "getEntireSystemColl",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "entireSystemColl",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "getEntireSystemDebt",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "entireSystemDebt",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "_price",
        "type": "uint256"
      }
    ],
    "name": "getTCR",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "_index",
        "type": "uint256"
      }
    ],
    "name": "getTroveFromTroveOwnersArray",
    "outputs": [
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "getTroveOwnersCount",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "_borrower",
        "type": "address"
      }
    ],
    "name": "getTroveStatus",
    "outputs": [
      {
        "internalType": "enum ITroveManager.Status",
        "name": "",
        "type": "uint8"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  }
] as const;

export const MEZO_TESTNET_SORTED_TROVES_ABI = [
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "_id",
        "type": "address"
      }
    ],
    "name": "contains",
    "outputs": [
      {
        "internalType": "bool",
        "name": "",
        "type": "bool"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "getFirst",
    "outputs": [
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "getLast",
    "outputs": [
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "_id",
        "type": "address"
      }
    ],
    "name": "getNext",
    "outputs": [
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "_id",
        "type": "address"
      }
    ],
    "name": "getPrev",
    "outputs": [
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "getSize",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "_NICR",
        "type": "uint256"
      },
      {
        "internalType": "address",
        "name": "_prevId",
        "type": "address"
      },
      {
        "internalType": "address",
        "name": "_nextId",
        "type": "address"
      }
    ],
    "name": "findInsertPosition",
    "outputs": [
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      },
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  }
] as const;

export const MEZO_TESTNET_PRICE_FEED_ABI = [
  {
    "inputs": [],
    "name": "fetchPrice",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  }
] as const;

/** IGovernableVariables interface retained in BorrowerOperationsImplementation.source.testnet.json AdditionalSources. */
export const MEZO_TESTNET_GOVERNABLE_VARIABLES_ABI = [
 {"type":"function","name":"isAccountFeeExempt","inputs":[{"name":"_account","type":"address"}],"outputs":[{"name":"","type":"bool"}],"stateMutability":"view"}
] as const;
