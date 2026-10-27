// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {Test, console2} from "forge-std/Test.sol";
import {LiqveraGuard} from "../../src/LiqveraGuard.sol";
import {
    IBorrowerOperationsSignatures,
    IBorrowerOperationsLite,
    ITroveManagerLite,
    IPriceFeedLite,
    IERC20Lite
} from "../../src/interfaces/IMezo.sol";

interface IBorrowerOperationsFork {
    function openTrove(uint256 debtAmount, address upperHint, address lowerHint) external payable;
    function borrowerOperationsSignaturesAddress() external view returns (address);
}

interface IEIP712Domain {
    function eip712Domain()
        external
        view
        returns (bytes1, string memory, string memory, uint256, address, bytes32, uint256[] memory);
}

interface IMUSDFork {
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
}

/// @notice Fork test against Mezo Testnet (chain 31611). Read-only for the real chain: all state
/// changes happen inside the local fork. Runs only when MEZO_TESTNET_RPC is set, e.g.
///   MEZO_TESTNET_RPC=https://rpc.test.mezo.org forge test --match-path 'test/fork/*' -vv
/// Optional: MEZO_FORK_BLOCK pins the block.
contract GuardForkTest is Test {
    address constant BO = 0xCdF7028ceAB81fA0C6971208e83fa7872994beE5;
    address constant SIGS = 0xD757e3646AF370b15f32EB557F0F8380Df7D639e;
    address constant TM = 0xE47c80e8c23f6B4A1aE41c34837a0599D5D16bb0;
    address constant FEED = 0x86bCF0841622a5dAC14A313a15f96A95421b9366;
    address constant MUSD = 0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503;
    /// @dev Blockscout-verified implementation behind the SIGS proxy (Q3), observed 27.10.2026.
    address constant SIGS_IMPL = 0xEec635aB00463A4a803DE38C9d858A0FE3bdc235;
    bytes32 constant EIP1967_IMPL = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;

    ITroveManagerLite tm = ITroveManagerLite(TM);
    IBorrowerOperationsSignatures sigs = IBorrowerOperationsSignatures(SIGS);
    IERC20Lite musd = IERC20Lite(MUSD);
    LiqveraGuard guard;

    uint256 constant PK = 0xF0F0_1234; // throwaway key; exists only inside the local fork
    address user;
    address keeper = makeAddr("liqvera-fork-keeper"); // 0xBEEF holds testnet funds; use a fresh address
    uint256 price;
    bool forked;

    function setUp() public {
        string memory rpc = vm.envOr("MEZO_TESTNET_RPC", string(""));
        if (bytes(rpc).length == 0) return;
        uint256 blk = vm.envOr("MEZO_FORK_BLOCK", uint256(0));
        if (blk == 0) vm.createSelectFork(rpc);
        else vm.createSelectFork(rpc, blk);
        forked = true;
        assertEq(block.chainid, 31611);

        user = vm.addr(PK);
        vm.deal(user, 100 ether);
        // The Mezo PriceFeed reads the Skip oracle precompile 0x7b7c..0015. A local fork (revm)
        // cannot execute Mezo precompiles, so read the live price from the node with eth_call
        // and pin it with mockCall. Tests then move the price with _mockPrice().
        string memory tag = blk == 0 ? "latest" : _hexQuantity(blk);
        bytes memory ret = vm.rpc(
            "eth_call",
            string.concat(
                '[{"to":"',
                vm.toString(FEED),
                '","data":"',
                vm.toString(abi.encodeWithSelector(IPriceFeedLite.fetchPrice.selector)),
                '"},"',
                tag,
                '"]'
            )
        );
        price = abi.decode(ret, (uint256));
        assertGt(price, 1000e18);
        _mockPrice(price);
        guard = new LiqveraGuard(sigs, IBorrowerOperationsLite(BO), tm, IPriceFeedLite(FEED), musd);
    }

    modifier onlyFork() {
        if (!forked) {
            vm.skip(true);
            return;
        }
        _;
    }

    // ------------------------------------------------------------ helpers

    function _hexQuantity(uint256 v) internal pure returns (string memory) {
        bytes memory digits = "0123456789abcdef";
        bytes memory buf = new bytes(64);
        uint256 n;
        do {
            buf[63 - n] = digits[v & 15];
            v >>= 4;
            n++;
        } while (v != 0);
        bytes memory out = new bytes(n + 2);
        out[0] = "0";
        out[1] = "x";
        for (uint256 i; i < n; i++) {
            out[i + 2] = buf[64 - n + i];
        }
        return string(out);
    }

    function _openTrove(uint256 debt, uint256 targetICR) internal {
        // Debt in Trove = debt + fee + 200 gas compensation. 1% margin covers the fee.
        uint256 coll = targetICR * (debt * 101 / 100 + 200e18) / price;
        vm.prank(user);
        IBorrowerOperationsFork(BO).openTrove{value: coll}(debt, address(0), address(0));
    }

    function _sign(LiqveraGuard.Action a, uint256 amount, uint256 deadline) internal view returns (bytes memory) {
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(PK, guard.digest(a, amount, user, sigs.getNonce(user), deadline));
        return abi.encodePacked(r, s, v);
    }

    function _mockPrice(uint256 p) internal {
        vm.mockCall(FEED, abi.encodeWithSelector(IPriceFeedLite.fetchPrice.selector), abi.encode(p));
    }

    /// @dev Price at which the user's Trove has the given ICR.
    function _priceForICR(uint256 icr) internal view returns (uint256) {
        return price * icr / tm.getCurrentICR(user, price);
    }

    // ------------------------------------------------------ Q1, Q3, consts

    function test_Q1_NonceGetter() public onlyFork {
        assertEq(sigs.getNonce(user), 0);
        (bool ok,) = SIGS.staticcall(abi.encodeWithSignature("nonces(address)", user));
        assertFalse(ok, "nonces(address) must not exist; mapping is private");
    }

    function test_Q3_DeployedImplementationAndDomain() public onlyFork {
        address impl = address(uint160(uint256(vm.load(SIGS, EIP1967_IMPL))));
        assertEq(impl, SIGS_IMPL);
        console2.log("impl codehash");
        console2.logBytes32(impl.codehash);
        assertEq(IBorrowerOperationsFork(BO).borrowerOperationsSignaturesAddress(), SIGS);
        (, string memory name, string memory version, uint256 chainId, address vc,,) =
            IEIP712Domain(SIGS).eip712Domain();
        assertEq(name, "BorrowerOperationsSignatures");
        assertEq(version, "1");
        assertEq(chainId, 31611);
        assertEq(vc, SIGS);
    }

    function test_MezoConstants() public onlyFork {
        assertEq(tm.MCR(), 1.1e18);
        assertEq(tm.MUSD_GAS_COMPENSATION(), 200e18);
        assertEq(IBorrowerOperationsLite(BO).minNetDebt(), 1800e18);
    }

    // ---------------------------------------------------------------- Q5

    function test_Q5_GetEntireDebtAndCollOrder() public onlyFork {
        uint256 debt = 3000e18;
        uint256 coll = 1.6e18 * (debt * 101 / 100 + 200e18) / price;
        vm.prank(user);
        IBorrowerOperationsFork(BO).openTrove{value: coll}(debt, address(0), address(0));
        (uint256 c, uint256 principal, uint256 interest, uint256 pc, uint256 pp, uint256 pi) =
            tm.getEntireDebtAndColl(user);
        assertEq(c, coll, "field 0 is coll");
        assertGe(principal, debt + 200e18, "field 1 is principal incl. gas comp and fee");
        assertLt(principal, debt * 101 / 100 + 200e18);
        assertEq(interest, 0, "no interest in the same block");
        assertEq(pc + pp + pi, 0, "no pending rewards for a new Trove");
        assertEq(tm.getCurrentICR(user, price), c * price / (principal + interest));
        assertEq(musd.balanceOf(user), debt);
        assertEq(tm.getTroveStatus(user), 1);
    }

    // --------------------------------------------------- Q2 + full repay

    function test_Q2_RepayPath_NoApproveNeeded() public onlyFork {
        _openTrove(3000e18, 1.6e18);
        uint256 deadline = block.timestamp + 1 days;
        vm.startPrank(user);
        IMUSDFork(MUSD).approve(address(guard), 520e18);
        guard.depositMUSD(520e18);
        guard.arm(
            LiqveraGuard.Action.RepayMUSD,
            1.3e18,
            500e18,
            20e18,
            uint64(deadline),
            _sign(LiqveraGuard.Action.RepayMUSD, 500e18, deadline)
        );
        vm.stopPrank();

        (bool ok, uint256 icr) = guard.checker(user);
        assertFalse(ok);
        assertGt(icr, 1.3e18);

        _mockPrice(_priceForICR(1.2e18));
        (ok, icr) = guard.checker(user);
        assertTrue(ok);

        // Q2: the Guard never approved anyone.
        assertEq(IMUSDFork(MUSD).allowance(address(guard), BO), 0);
        assertEq(IMUSDFork(MUSD).allowance(address(guard), SIGS), 0);
        (, uint256 p0, uint256 i0,,,) = tm.getEntireDebtAndColl(user);

        vm.prank(keeper);
        guard.protect(user, address(0), address(0));

        (, uint256 p1, uint256 i1,,,) = tm.getEntireDebtAndColl(user);
        assertEq(p0 + i0 - (p1 + i1), 500e18, "debt down by the signed amount");
        assertEq(musd.balanceOf(address(guard)), 0, "500 burned from the Guard, 20 to keeper");
        assertEq(musd.balanceOf(keeper), 20e18);
        assertEq(sigs.getNonce(user), 1);
        assertGt(tm.getCurrentICR(user, IPriceFeedLite(FEED).fetchPrice()), icr);
    }

    function test_AddCollPath() public onlyFork {
        _openTrove(3000e18, 1.6e18);
        uint256 deadline = block.timestamp + 1 days;
        uint256 amount = 0.01 ether;
        vm.startPrank(user);
        guard.depositBTC{value: amount + 0.0001 ether}();
        guard.arm(
            LiqveraGuard.Action.AddColl,
            1.3e18,
            uint128(amount),
            0.0001 ether,
            uint64(deadline),
            _sign(LiqveraGuard.Action.AddColl, amount, deadline)
        );
        vm.stopPrank();
        _mockPrice(_priceForICR(1.2e18));
        (uint256 c0,,,,,) = tm.getEntireDebtAndColl(user);
        vm.prank(keeper);
        guard.protect(user, address(0), address(0));
        (uint256 c1,,,,,) = tm.getEntireDebtAndColl(user);
        assertEq(c1 - c0, amount);
        assertEq(keeper.balance, 0.0001 ether);
        assertEq(address(guard).balance, 0);
    }

    // ------------------------------------------------- minNetDebt (R4)

    function test_MinNetDebt_Enforced() public onlyFork {
        _openTrove(3000e18, 1.6e18);
        (, uint256 p,,,,) = tm.getEntireDebtAndColl(user);
        uint256 maxRepay = p - 200e18 - 1800e18;
        uint256 deadline = block.timestamp + 1 days;
        vm.startPrank(user);
        IMUSDFork(MUSD).approve(address(guard), type(uint256).max);
        guard.depositMUSD(maxRepay + 1);
        vm.expectRevert(LiqveraGuard.BelowMinNetDebt.selector);
        guard.arm(LiqveraGuard.Action.RepayMUSD, 1.3e18, uint128(maxRepay + 1), 0, uint64(deadline), "");
        guard.arm(
            LiqveraGuard.Action.RepayMUSD,
            1.3e18,
            uint128(maxRepay),
            0,
            uint64(deadline),
            _sign(LiqveraGuard.Action.RepayMUSD, maxRepay, deadline)
        );
        vm.stopPrank();
        _mockPrice(_priceForICR(1.2e18));
        vm.prank(keeper);
        guard.protect(user, address(0), address(0));
        (, uint256 p1, uint256 i1,,,) = tm.getEntireDebtAndColl(user);
        assertEq(p1 + i1 - 200e18, 1800e18, "net debt exactly at the Mezo minimum");
    }

    // ------------------------------------------- stale nonce + front-run

    function test_FrontRun_StaleNonce() public onlyFork {
        _openTrove(3000e18, 1.6e18);
        uint256 deadline = block.timestamp + 1 days;
        bytes memory sig = _sign(LiqveraGuard.Action.RepayMUSD, 500e18, deadline);
        vm.startPrank(user);
        IMUSDFork(MUSD).approve(address(guard), 500e18);
        guard.depositMUSD(500e18);
        guard.arm(LiqveraGuard.Action.RepayMUSD, 1.3e18, 500e18, 0, uint64(deadline), sig);
        // Attacker = the user's own wallet funds here, to have MUSD; any address works.
        vm.stopPrank();
        address attacker = address(0xA77AC);
        vm.prank(user);
        musd.transfer(attacker, 500e18);
        vm.prank(attacker);
        sigs.repayMUSDWithSignature(500e18, address(0), address(0), user, sig, deadline);

        _mockPrice(_priceForICR(1.2e18));
        (LiqveraGuard.Status s,) = guard.status(user);
        assertEq(uint8(s), uint8(LiqveraGuard.Status.StaleNonce));
        vm.prank(keeper);
        vm.expectRevert(abi.encodeWithSelector(LiqveraGuard.NotExecutable.selector, LiqveraGuard.Status.StaleNonce));
        guard.protect(user, address(0), address(0));
        assertEq(guard.musdBalance(user), 500e18, "escrow untouched");
    }

    // --------------------------------------------------- Recovery Mode

    function test_RecoveryMode_RepayStillWorks() public onlyFork {
        _openTrove(3000e18, 3e18);
        uint256 deadline = block.timestamp + 1 days;
        vm.startPrank(user);
        IMUSDFork(MUSD).approve(address(guard), 500e18);
        guard.depositMUSD(500e18);
        guard.arm(
            LiqveraGuard.Action.RepayMUSD,
            2e18,
            500e18,
            0,
            uint64(deadline),
            _sign(LiqveraGuard.Action.RepayMUSD, 500e18, deadline)
        );
        vm.stopPrank();

        // Drop price until the system is in Recovery Mode (TCR < 150%).
        uint256 p = price;
        while (!tm.checkRecoveryMode(p)) p = p * 95 / 100;
        _mockPrice(p);
        uint256 icr = tm.getCurrentICR(user, p);
        console2.log("RM price", p, "user ICR", icr);
        assertGe(icr, 1.1e18, "test setup: Trove must not be liquidatable");
        assertLt(icr, 2e18);

        (bool ok,) = guard.checker(user);
        assertTrue(ok);
        vm.prank(keeper);
        guard.protect(user, address(0), address(0));
        assertGt(tm.getCurrentICR(user, p), icr);
    }
}
