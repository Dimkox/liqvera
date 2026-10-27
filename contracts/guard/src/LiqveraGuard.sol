// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {
    IBorrowerOperationsSignatures,
    ITroveManagerLite,
    IBorrowerOperationsLite,
    IPriceFeedLite,
    IERC20Lite
} from "./interfaces/IMezo.sol";

/// @title LiqveraGuard
/// @notice Keeper-executed protection for Mezo Troves. TESTNET ONLY. NOT AUDITED.
/// @dev Flow:
///  1. The borrower deposits a MUSD or BTC buffer into this contract (escrow).
///  2. The borrower signs ONE Mezo `RepayMUSD` or `AddColl` EIP-712 message for
///     BorrowerOperationsSignatures with a fixed amount, their current nonce and a deadline.
///  3. The borrower calls `arm()` with a trigger ICR. The Guard checks the signature on-chain.
///  4. Any keeper calls `checker()` (view). When it returns true, the keeper calls `protect()`.
///  5. `protect()` re-checks everything on-chain with the Mezo PriceFeed, pays the signed
///     amount from the borrower's escrow into Mezo, checks that ICR went up, and pays the keeper.
/// The Trove stays in the borrower's wallet. The Guard never holds the Trove collateral.
/// The design idea (ratio trigger + bot executes) follows DeFi Saver / Summer.fi automation, and
/// `checker()` follows the Gelato / Chainlink Automation "check, then perform" shape. No code copied.
contract LiqveraGuard {
    // ---------------------------------------------------------------- types

    enum Action {
        None,
        RepayMUSD,
        AddColl
    }

    /// @notice Why a policy can or cannot execute now. `Ready` is the only executable state.
    enum Status {
        Ready,
        NoPolicy,
        Expired,
        StaleNonce,
        TroveNotActive,
        Healthy,
        BelowMinNetDebt,
        StillBelowMCR
    }

    struct Policy {
        Action action;
        uint96 triggerICR; // 1e18 = 100%
        uint128 amount; // MUSD wei (RepayMUSD) or BTC wei (AddColl); exactly the signed amount
        uint128 keeperReward; // same asset as `amount`
        uint64 deadline; // the signed deadline
        uint256 sigNonce; // Mezo nonce that the signature commits to
        bytes signature;
    }

    // ------------------------------------------------------------ constants

    uint8 internal constant TROVE_ACTIVE = 1;
    /// @notice Upper bound for signature deadlines (risk R7).
    uint256 public constant MAX_SIGNATURE_TTL = 30 days;
    /// @notice Upper bound for the trigger. Prevents nonsense triggers (1000%).
    uint256 public constant MAX_TRIGGER_ICR = 10e18;

    bytes32 internal constant DOMAIN_TYPEHASH =
        keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)");
    bytes32 internal constant NAME_HASH = keccak256("BorrowerOperationsSignatures");
    bytes32 internal constant VERSION_HASH = keccak256("1");
    bytes32 public constant REPAY_MUSD_TYPEHASH =
        keccak256("RepayMUSD(uint256 amount,address borrower,uint256 nonce,uint256 deadline)");
    bytes32 public constant ADD_COLL_TYPEHASH =
        keccak256("AddColl(uint256 assetAmount,address borrower,uint256 nonce,uint256 deadline)");
    /// @dev secp256k1n / 2. Same malleability rule as OpenZeppelin ECDSA used by Mezo.
    uint256 internal constant HALF_N = 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5D576E7357A4501DDFE92F46681B20A0;

    // ----------------------------------------------------------- immutables

    IBorrowerOperationsSignatures public immutable signatures;
    IBorrowerOperationsLite public immutable borrowerOperations;
    ITroveManagerLite public immutable troveManager;
    IPriceFeedLite public immutable priceFeed;
    IERC20Lite public immutable musd;

    // ---------------------------------------------------------------- state

    mapping(address => uint256) public musdBalance;
    mapping(address => uint256) public btcBalance;
    mapping(address => Policy) internal _policies;
    uint256 public totalMUSDEscrow;
    uint256 public totalBTCEscrow;
    uint256 private _lock = 1;

    // --------------------------------------------------------------- events

    event Deposited(address indexed user, bool isBTC, uint256 amount);
    event Withdrawn(address indexed user, bool isBTC, uint256 amount);
    event Armed(
        address indexed user,
        Action action,
        uint256 triggerICR,
        uint256 amount,
        uint256 keeperReward,
        uint256 deadline,
        uint256 sigNonce
    );
    event Disarmed(address indexed user);
    event Protected(
        address indexed user,
        address indexed keeper,
        Action action,
        uint256 amount,
        uint256 icrBefore,
        uint256 icrAfter,
        uint256 reward
    );

    // --------------------------------------------------------------- errors

    error Reentrancy();
    error ZeroAddress();
    error ZeroAmount();
    error InsufficientFreeBalance();
    error TransferFailed();
    error InvalidAction();
    error TriggerOutOfRange();
    error DeadlineOutOfRange();
    error TroveNotActive();
    error BadSignature();
    error BelowMinNetDebt();
    error NotExecutable(Status status);
    error ICRNotImproved(uint256 icrBefore, uint256 icrAfter);
    error DirectBTCNotAccepted();

    modifier nonReentrant() {
        if (_lock != 1) revert Reentrancy();
        _lock = 2;
        _;
        _lock = 1;
    }

    constructor(
        IBorrowerOperationsSignatures signatures_,
        IBorrowerOperationsLite borrowerOperations_,
        ITroveManagerLite troveManager_,
        IPriceFeedLite priceFeed_,
        IERC20Lite musd_
    ) {
        if (
            address(signatures_) == address(0) || address(borrowerOperations_) == address(0)
                || address(troveManager_) == address(0) || address(priceFeed_) == address(0)
                || address(musd_) == address(0)
        ) revert ZeroAddress();
        signatures = signatures_;
        borrowerOperations = borrowerOperations_;
        troveManager = troveManager_;
        priceFeed = priceFeed_;
        musd = musd_;
    }

    /// @dev Plain BTC transfers are rejected so that every wei in the contract is accounted for.
    receive() external payable {
        revert DirectBTCNotAccepted();
    }

    // --------------------------------------------------------------- escrow

    function depositMUSD(uint256 amount) external nonReentrant {
        if (amount == 0) revert ZeroAmount();
        uint256 before = musd.balanceOf(address(this));
        if (!musd.transferFrom(msg.sender, address(this), amount)) revert TransferFailed();
        // Credit only what arrived (defensive; MUSD has no transfer fee).
        uint256 received = musd.balanceOf(address(this)) - before;
        musdBalance[msg.sender] += received;
        totalMUSDEscrow += received;
        emit Deposited(msg.sender, false, received);
    }

    function depositBTC() external payable nonReentrant {
        if (msg.value == 0) revert ZeroAmount();
        btcBalance[msg.sender] += msg.value;
        totalBTCEscrow += msg.value;
        emit Deposited(msg.sender, true, msg.value);
    }

    function withdrawMUSD(uint256 amount) external nonReentrant {
        if (amount == 0) revert ZeroAmount();
        if (amount > freeMUSD(msg.sender)) revert InsufficientFreeBalance();
        musdBalance[msg.sender] -= amount;
        totalMUSDEscrow -= amount;
        if (!musd.transfer(msg.sender, amount)) revert TransferFailed();
        emit Withdrawn(msg.sender, false, amount);
    }

    function withdrawBTC(uint256 amount) external nonReentrant {
        if (amount == 0) revert ZeroAmount();
        if (amount > freeBTC(msg.sender)) revert InsufficientFreeBalance();
        btcBalance[msg.sender] -= amount;
        totalBTCEscrow -= amount;
        _sendBTC(msg.sender, amount);
        emit Withdrawn(msg.sender, true, amount);
    }

    /// @notice MUSD that is not reserved by an armed RepayMUSD policy.
    function freeMUSD(address user) public view returns (uint256) {
        return musdBalance[user] - _reserved(user, Action.RepayMUSD);
    }

    /// @notice BTC that is not reserved by an armed AddColl policy.
    function freeBTC(address user) public view returns (uint256) {
        return btcBalance[user] - _reserved(user, Action.AddColl);
    }

    // --------------------------------------------------------------- policy

    /// @notice Store a protection policy and the borrower's Mezo signature.
    /// @dev Replaces an existing policy. The signature must be made by msg.sender over the
    /// CURRENT Mezo nonce. A later signed Mezo operation of the borrower makes it stale (R1).
    function arm(
        Action action,
        uint96 triggerICR,
        uint128 amount,
        uint128 keeperReward,
        uint64 deadline,
        bytes calldata signature
    ) external nonReentrant {
        if (action == Action.None) revert InvalidAction();
        if (amount == 0) revert ZeroAmount();
        if (triggerICR <= troveManager.MCR() || triggerICR > MAX_TRIGGER_ICR) revert TriggerOutOfRange();
        if (deadline < block.timestamp || deadline > block.timestamp + MAX_SIGNATURE_TTL) {
            revert DeadlineOutOfRange();
        }
        if (troveManager.getTroveStatus(msg.sender) != TROVE_ACTIVE) revert TroveNotActive();

        // Release the old reservation before the balance check.
        delete _policies[msg.sender];

        uint256 needed = uint256(amount) + keeperReward;
        if (action == Action.RepayMUSD) {
            if (needed > musdBalance[msg.sender]) revert InsufficientFreeBalance();
            (, uint256 debt) = _entireCollAndDebt(msg.sender);
            if (!_repayKeepsMinNetDebt(debt, amount)) revert BelowMinNetDebt();
        } else {
            if (needed > btcBalance[msg.sender]) revert InsufficientFreeBalance();
        }

        uint256 nonce = signatures.getNonce(msg.sender);
        if (_recover(_digest(action, amount, msg.sender, nonce, deadline), signature) != msg.sender) {
            revert BadSignature();
        }

        _policies[msg.sender] = Policy({
            action: action,
            triggerICR: triggerICR,
            amount: amount,
            keeperReward: keeperReward,
            deadline: deadline,
            sigNonce: nonce,
            signature: signature
        });
        emit Armed(msg.sender, action, triggerICR, amount, keeperReward, deadline, nonce);
    }

    function disarm() external nonReentrant {
        if (_policies[msg.sender].action == Action.None) revert NotExecutable(Status.NoPolicy);
        delete _policies[msg.sender];
        emit Disarmed(msg.sender);
    }

    function policyOf(address user) external view returns (Policy memory) {
        return _policies[user];
    }

    // -------------------------------------------------------- check/perform

    /// @notice Gelato/Chainlink-style view check. True iff `protect(borrower, ..)` would pass the
    /// Guard checks now (Mezo hints can still make the call revert; the keeper recomputes them).
    function checker(address borrower) external view returns (bool canExec, uint256 icr) {
        Status s;
        (s, icr,) = _evaluate(borrower);
        canExec = s == Status.Ready;
    }

    /// @notice Same as `checker` but with the reason. For keepers and the UI.
    function status(address borrower) external view returns (Status s, uint256 icr) {
        (s, icr,) = _evaluate(borrower);
    }

    /// @notice Execute the stored policy. Permissionless. Pays the keeper from the user's escrow.
    function protect(address borrower, address upperHint, address lowerHint) external nonReentrant {
        (Status s, uint256 icrBefore, uint256 price) = _evaluate(borrower);
        if (s != Status.Ready) revert NotExecutable(s);

        Policy memory p = _policies[borrower];

        // Effects first (CEI): debit escrow and remove the policy. One signature = one execution.
        delete _policies[borrower];
        uint256 total = uint256(p.amount) + p.keeperReward;
        if (p.action == Action.RepayMUSD) {
            musdBalance[borrower] -= total;
            totalMUSDEscrow -= total;
            // No approve: BorrowerOperations burns MUSD from this contract directly (Q2).
            signatures.repayMUSDWithSignature(p.amount, upperHint, lowerHint, borrower, p.signature, p.deadline);
        } else {
            btcBalance[borrower] -= total;
            totalBTCEscrow -= total;
            signatures.addCollWithSignature{value: p.amount}(upperHint, lowerHint, borrower, p.signature, p.deadline);
        }

        uint256 icrAfter = troveManager.getCurrentICR(borrower, price);
        if (icrAfter <= icrBefore) revert ICRNotImproved(icrBefore, icrAfter);

        if (p.keeperReward > 0) {
            if (p.action == Action.RepayMUSD) {
                if (!musd.transfer(msg.sender, p.keeperReward)) revert TransferFailed();
            } else {
                _sendBTC(msg.sender, p.keeperReward);
            }
        }
        emit Protected(borrower, msg.sender, p.action, p.amount, icrBefore, icrAfter, p.keeperReward);
    }

    // ------------------------------------------------------------- EIP-712

    /// @notice Domain separator of Mezo BorrowerOperationsSignatures on this chain.
    function domainSeparator() public view returns (bytes32) {
        return keccak256(abi.encode(DOMAIN_TYPEHASH, NAME_HASH, VERSION_HASH, block.chainid, address(signatures)));
    }

    /// @notice The EIP-712 digest that the borrower must sign. Helper for UIs and tests.
    function digest(Action action, uint256 amount, address borrower, uint256 nonce, uint256 deadline)
        external
        view
        returns (bytes32)
    {
        return _digest(action, amount, borrower, nonce, deadline);
    }

    // ------------------------------------------------------------ internal

    function _evaluate(address borrower) internal view returns (Status, uint256 icr, uint256 price) {
        Policy storage p = _policies[borrower];
        if (p.action == Action.None) return (Status.NoPolicy, 0, 0);
        if (block.timestamp > p.deadline) return (Status.Expired, 0, 0);
        if (signatures.getNonce(borrower) != p.sigNonce) return (Status.StaleNonce, 0, 0);
        if (troveManager.getTroveStatus(borrower) != TROVE_ACTIVE) return (Status.TroveNotActive, 0, 0);

        price = priceFeed.fetchPrice();
        icr = troveManager.getCurrentICR(borrower, price);
        if (icr >= p.triggerICR) return (Status.Healthy, icr, price);

        (uint256 coll, uint256 debt) = _entireCollAndDebt(borrower);
        uint256 newColl = coll;
        uint256 newDebt = debt;
        if (p.action == Action.RepayMUSD) {
            if (!_repayKeepsMinNetDebt(debt, p.amount)) return (Status.BelowMinNetDebt, icr, price);
            newDebt = debt - p.amount;
        } else {
            newColl = coll + p.amount;
        }
        // Mezo liquidates below MCR in Normal AND Recovery Mode, and Normal Mode rejects an
        // adjustment that leaves ICR < MCR. An action that cannot lift ICR to MCR is useless.
        if (newColl * price / newDebt < troveManager.MCR()) return (Status.StillBelowMCR, icr, price);
        return (Status.Ready, icr, price);
    }

    function _entireCollAndDebt(address borrower) internal view returns (uint256 coll, uint256 debt) {
        (uint256 c, uint256 principal, uint256 interest, uint256 pc, uint256 pp, uint256 pi) =
            troveManager.getEntireDebtAndColl(borrower);
        coll = c + pc;
        debt = principal + interest + pp + pi;
    }

    /// @dev Mezo rule: (debt - gas compensation) - repayment >= minNetDebt (risk R4).
    function _repayKeepsMinNetDebt(uint256 debt, uint256 amount) internal view returns (bool) {
        uint256 gasComp = troveManager.MUSD_GAS_COMPENSATION();
        if (debt < gasComp + amount) return false;
        return debt - gasComp - amount >= borrowerOperations.minNetDebt();
    }

    function _reserved(address user, Action asset) internal view returns (uint256) {
        Policy storage p = _policies[user];
        if (p.action != asset) return 0;
        return uint256(p.amount) + p.keeperReward;
    }

    function _digest(Action action, uint256 amount, address borrower, uint256 nonce, uint256 deadline)
        internal
        view
        returns (bytes32)
    {
        bytes32 typeHash = action == Action.RepayMUSD ? REPAY_MUSD_TYPEHASH : ADD_COLL_TYPEHASH;
        bytes32 structHash = keccak256(abi.encode(typeHash, amount, borrower, nonce, deadline));
        return keccak256(abi.encodePacked("\x19\x01", domainSeparator(), structHash));
    }

    function _recover(bytes32 hash, bytes calldata sig) internal pure returns (address) {
        if (sig.length != 65) return address(0);
        bytes32 r = bytes32(sig[0:32]);
        bytes32 s = bytes32(sig[32:64]);
        uint8 v = uint8(sig[64]);
        if (uint256(s) > HALF_N || (v != 27 && v != 28)) return address(0);
        return ecrecover(hash, v, r, s);
    }

    function _sendBTC(address to, uint256 amount) internal {
        (bool ok,) = to.call{value: amount}("");
        if (!ok) revert TransferFailed();
    }
}
