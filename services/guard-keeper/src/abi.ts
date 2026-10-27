import { parseAbi } from "viem";

export const guardAbi = parseAbi([
  "event Armed(address indexed user, uint8 action, uint256 triggerICR, uint256 amount, uint256 keeperReward, uint256 deadline, uint256 sigNonce)",
  "event Disarmed(address indexed user)",
  "event Protected(address indexed user, address indexed keeper, uint8 action, uint256 amount, uint256 icrBefore, uint256 icrAfter, uint256 reward)",
  "function status(address borrower) view returns (uint8 s, uint256 icr)",
  "function policyOf(address user) view returns ((uint8 action, uint96 triggerICR, uint128 amount, uint128 keeperReward, uint64 deadline, uint256 sigNonce, bytes signature) p)",
  "function protect(address borrower, address upperHint, address lowerHint)",
]);

export const troveManagerAbi = parseAbi([
  "function getEntireDebtAndColl(address borrower) view returns (uint256 coll, uint256 principal, uint256 interest, uint256 pendingCollateral, uint256 pendingPrincipal, uint256 pendingInterest)",
]);
export const hintHelpersAbi = parseAbi([
  "function getApproxHint(uint256 CR, uint256 numTrials, uint256 inputRandomSeed) view returns (address hintAddress, uint256 diff, uint256 latestRandomSeed)",
]);
export const sortedTrovesAbi = parseAbi([
  "function findInsertPosition(uint256 NICR, address prevId, address nextId) view returns (address, address)",
]);
