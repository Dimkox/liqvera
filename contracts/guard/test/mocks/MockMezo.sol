// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

/// @notice Small stand-ins for the Mezo contracts. Behaviour follows mezo-org/musd commit da7888a
/// for the parts the Guard depends on: EIP-712 digest, sequential nonce, burn from caller,
/// minNetDebt and MCR rules.

contract MockMUSD {
    string public constant name = "Mock MUSD";
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    address public burner;

    function setBurner(address b) external {
        burner = b;
    }

    function mint(address to, uint256 amount) external {
        balanceOf[to] += amount;
    }

    function burn(address from, uint256 amount) external {
        require(msg.sender == burner, "MockMUSD: not burner");
        balanceOf[from] -= amount;
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        return true;
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        allowance[from][msg.sender] -= amount;
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        return true;
    }
}

contract MockPriceFeed {
    uint256 public price = 100_000e18;

    function setPrice(uint256 p) external {
        price = p;
    }

    function fetchPrice() external view returns (uint256) {
        return price;
    }
}

contract MockBorrowerOperations {
    uint256 public minNetDebt = 1800e18;
}

contract MockTroveManager {
    struct T {
        uint8 status;
        uint256 coll;
        uint256 principal;
        uint256 interest;
    }

    /// @dev Pending redistribution rewards not yet applied to the stored Trove.
    struct Pending {
        uint256 coll;
        uint256 principal;
        uint256 interest;
    }

    uint256 public constant MCR = 1.1e18;
    uint256 public constant MUSD_GAS_COMPENSATION = 200e18;
    bool public recoveryMode;
    mapping(address => T) public troves;
    mapping(address => Pending) public pending;

    function setTrove(address b, uint8 status, uint256 coll, uint256 principal, uint256 interest) external {
        troves[b] = T(status, coll, principal, interest);
        delete pending[b];
    }

    /// @dev Test helper: give the Trove pending liquidation (redistribution) rewards.
    function setPending(address b, uint256 coll, uint256 principal, uint256 interest) external {
        pending[b] = Pending(coll, principal, interest);
    }

    function setRecoveryMode(bool on) external {
        recoveryMode = on;
    }

    function getTroveStatus(address b) external view returns (uint8) {
        return troves[b].status;
    }

    function getEntireDebtAndColl(address b)
        external
        view
        returns (uint256, uint256, uint256, uint256, uint256, uint256)
    {
        // Like Mezo: the first three values ALREADY include the pending rewards.
        T storage t = troves[b];
        Pending storage p = pending[b];
        return (t.coll + p.coll, t.principal + p.principal, t.interest + p.interest, p.coll, p.principal, p.interest);
    }

    /// @dev Like Mezo: ICR uses the entire (pending-inclusive) collateral and debt.
    function getCurrentICR(address b, uint256 price) public view returns (uint256) {
        T storage t = troves[b];
        Pending storage p = pending[b];
        uint256 debt = t.principal + t.interest + p.principal + p.interest;
        return debt == 0 ? type(uint256).max : (t.coll + p.coll) * price / debt;
    }

    /// @dev Like Mezo `_applyPendingRewards`: move pending rewards into the stored Trove.
    function _applyPending(address b) internal {
        T storage t = troves[b];
        Pending memory p = pending[b];
        t.coll += p.coll;
        t.principal += p.principal;
        t.interest += p.interest;
        delete pending[b];
    }

    function checkRecoveryMode(uint256) external view returns (bool) {
        return recoveryMode;
    }

    /// @dev Called by MockSignatures. Applies interest first, like Mezo.
    function applyRepay(address b, uint256 amount) external {
        _applyPending(b);
        T storage t = troves[b];
        uint256 fromInterest = amount > t.interest ? t.interest : amount;
        t.interest -= fromInterest;
        t.principal -= amount - fromInterest;
    }

    function applyAddColl(address b, uint256 amount) external {
        _applyPending(b);
        troves[b].coll += amount;
    }
}

contract MockSignatures {
    bytes32 internal constant REPAY =
        keccak256("RepayMUSD(uint256 amount,address borrower,uint256 nonce,uint256 deadline)");
    bytes32 internal constant ADDCOLL =
        keccak256("AddColl(uint256 assetAmount,address borrower,uint256 nonce,uint256 deadline)");

    mapping(address => uint256) private nonces;
    MockTroveManager public tm;
    MockMUSD public musd;
    MockBorrowerOperations public bo;
    MockPriceFeed public feed;

    constructor(MockTroveManager tm_, MockMUSD musd_, MockBorrowerOperations bo_, MockPriceFeed feed_) {
        tm = tm_;
        musd = musd_;
        bo = bo_;
        feed = feed_;
    }

    function getNonce(address u) external view returns (uint256) {
        return nonces[u];
    }

    /// @dev Test helper: the borrower did another signed Mezo operation.
    function bumpNonce(address u) external {
        nonces[u]++;
    }

    function domainSeparator() public view returns (bytes32) {
        return keccak256(
            abi.encode(
                keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"),
                keccak256("BorrowerOperationsSignatures"),
                keccak256("1"),
                block.chainid,
                address(this)
            )
        );
    }

    function _verify(bytes32 typeHash, bytes memory data, address borrower, bytes memory sig, uint256 deadline)
        internal
    {
        require(block.timestamp <= deadline, "Signature expired");
        bytes32 h = keccak256(abi.encodePacked(typeHash, data, nonces[borrower], deadline));
        bytes32 d = keccak256(abi.encodePacked("\x19\x01", domainSeparator(), h));
        (bytes32 r, bytes32 s) = abi.decode(sig, (bytes32, bytes32));
        uint8 v = uint8(sig[64]);
        require(ecrecover(d, v, r, s) == borrower, "BorrowerOperationsSignatures: Invalid signature");
        nonces[borrower]++;
    }

    function repayMUSDWithSignature(
        uint256 amount,
        address,
        address,
        address borrower,
        bytes memory sig,
        uint256 deadline
    ) external {
        _verify(REPAY, abi.encode(amount, borrower), borrower, sig, deadline);
        (, uint256 p, uint256 i,,,) = tm.getEntireDebtAndColl(borrower);
        require(
            p + i - 200e18 - amount >= bo.minNetDebt(), "BorrowerOps: Trove's net debt must be greater than minimum"
        );
        require(musd.balanceOf(msg.sender) >= amount, "BorrowerOps: Caller doesnt have enough mUSD to make repayment");
        musd.burn(msg.sender, amount);
        tm.applyRepay(borrower, amount);
        require(
            tm.getCurrentICR(borrower, feed.price()) >= 1.1e18,
            "BorrowerOps: An operation that would result in ICR < MCR is not permitted"
        );
    }

    function addCollWithSignature(address, address, address borrower, bytes memory sig, uint256 deadline)
        external
        payable
    {
        _verify(ADDCOLL, abi.encode(msg.value, borrower), borrower, sig, deadline);
        tm.applyAddColl(borrower, msg.value);
    }
}
