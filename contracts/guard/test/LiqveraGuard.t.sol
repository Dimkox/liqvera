// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {Test} from "forge-std/Test.sol";
import {LiqveraGuard} from "../src/LiqveraGuard.sol";
import {
    IBorrowerOperationsSignatures,
    IBorrowerOperationsLite,
    ITroveManagerLite,
    IPriceFeedLite,
    IERC20Lite
} from "../src/interfaces/IMezo.sol";
import {MockMUSD, MockPriceFeed, MockBorrowerOperations, MockTroveManager, MockSignatures} from "./mocks/MockMezo.sol";

contract GuardBase is Test {
    MockMUSD musd;
    MockPriceFeed feed;
    MockBorrowerOperations bo;
    MockTroveManager tm;
    MockSignatures sigs;
    LiqveraGuard guard;

    uint256 constant PK = 0xA11CE;
    address user;
    address keeper = makeAddr("keeper");

    // Trove: 0.05 BTC, 3000 MUSD debt. Price 100k => ICR 166.6%.
    uint256 constant COLL = 0.05 ether;
    uint256 constant DEBT = 3000e18;

    function setUp() public virtual {
        vm.warp(1_800_000_000);
        user = vm.addr(PK);
        musd = new MockMUSD();
        feed = new MockPriceFeed();
        bo = new MockBorrowerOperations();
        tm = new MockTroveManager();
        sigs = new MockSignatures(tm, musd, bo, feed);
        musd.setBurner(address(sigs));
        guard = new LiqveraGuard(
            IBorrowerOperationsSignatures(address(sigs)),
            IBorrowerOperationsLite(address(bo)),
            ITroveManagerLite(address(tm)),
            IPriceFeedLite(address(feed)),
            IERC20Lite(address(musd))
        );
        tm.setTrove(user, 1, COLL, DEBT, 0);
        musd.mint(user, 10_000e18);
        vm.deal(user, 10 ether);
        vm.prank(user);
        musd.approve(address(guard), type(uint256).max);
    }

    function _sign(uint256 pk, LiqveraGuard.Action a, uint256 amount, uint256 nonce, uint256 deadline)
        internal
        view
        returns (bytes memory)
    {
        bytes32 d = guard.digest(a, amount, vm.addr(pk), nonce, deadline);
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(pk, d);
        return abi.encodePacked(r, s, v);
    }

    function _armRepay(uint128 amount, uint128 reward, uint96 trigger) internal returns (uint64 deadline) {
        deadline = uint64(block.timestamp + 7 days);
        vm.startPrank(user);
        guard.depositMUSD(uint256(amount) + reward);
        guard.arm(
            LiqveraGuard.Action.RepayMUSD,
            trigger,
            amount,
            reward,
            deadline,
            _sign(PK, LiqveraGuard.Action.RepayMUSD, amount, sigs.getNonce(user), deadline)
        );
        vm.stopPrank();
    }

    function _armAddColl(uint128 amount, uint128 reward, uint96 trigger) internal returns (uint64 deadline) {
        deadline = uint64(block.timestamp + 7 days);
        vm.startPrank(user);
        guard.depositBTC{value: uint256(amount) + reward}();
        guard.arm(
            LiqveraGuard.Action.AddColl,
            trigger,
            amount,
            reward,
            deadline,
            _sign(PK, LiqveraGuard.Action.AddColl, amount, sigs.getNonce(user), deadline)
        );
        vm.stopPrank();
    }

    /// @dev ICR = 0.05 * 72k / 3000 = 120%.
    function _dropPriceTo120() internal {
        feed.setPrice(72_000e18);
    }
}

contract LiqveraGuardTest is GuardBase {
    // ------------------------------------------------ mock sanity

    function test_MockICR_Settable() public {
        assertApproxEqRel(tm.getCurrentICR(user, feed.price()), 1.6667e18, 1e14);
        _dropPriceTo120();
        assertEq(tm.getCurrentICR(user, feed.price()), 1.2e18);
    }

    function test_DigestMatchesMezoDomain() public view {
        assertEq(guard.domainSeparator(), sigs.domainSeparator());
    }

    function test_Constructor_RevertsOnZero() public {
        vm.expectRevert(LiqveraGuard.ZeroAddress.selector);
        new LiqveraGuard(
            IBorrowerOperationsSignatures(address(0)),
            IBorrowerOperationsLite(address(bo)),
            ITroveManagerLite(address(tm)),
            IPriceFeedLite(address(feed)),
            IERC20Lite(address(musd))
        );
    }

    // ------------------------------------------------------ escrow

    function test_DepositMUSD_IncreasesBalance() public {
        vm.expectEmit(true, false, false, true);
        emit LiqveraGuard.Deposited(user, false, 100e18);
        vm.prank(user);
        guard.depositMUSD(100e18);
        assertEq(guard.musdBalance(user), 100e18);
        assertEq(guard.totalMUSDEscrow(), 100e18);
        assertEq(musd.balanceOf(address(guard)), 100e18);
    }

    function test_DepositBTC_IncreasesBalance() public {
        vm.prank(user);
        guard.depositBTC{value: 1 ether}();
        assertEq(guard.btcBalance(user), 1 ether);
        assertEq(address(guard).balance, 1 ether);
    }

    function test_Deposit_RevertsOnZero() public {
        vm.startPrank(user);
        vm.expectRevert(LiqveraGuard.ZeroAmount.selector);
        guard.depositMUSD(0);
        vm.expectRevert(LiqveraGuard.ZeroAmount.selector);
        guard.depositBTC();
        vm.expectRevert(LiqveraGuard.ZeroAmount.selector);
        guard.withdrawMUSD(0);
        vm.expectRevert(LiqveraGuard.ZeroAmount.selector);
        guard.withdrawBTC(0);
        vm.stopPrank();
    }

    function test_DirectBTC_Rejected() public {
        vm.prank(user);
        (bool ok,) = address(guard).call{value: 1}("");
        assertFalse(ok);
    }

    function test_Withdraw_ReturnsFunds() public {
        vm.startPrank(user);
        guard.depositMUSD(100e18);
        guard.depositBTC{value: 1 ether}();
        guard.withdrawMUSD(40e18);
        guard.withdrawBTC(0.4 ether);
        vm.stopPrank();
        assertEq(guard.musdBalance(user), 60e18);
        assertEq(guard.btcBalance(user), 0.6 ether);
        assertEq(musd.balanceOf(user), 10_000e18 - 60e18);
    }

    function test_Withdraw_RevertsAboveFree() public {
        _armRepay(500e18, 10e18, 1.3e18);
        vm.startPrank(user);
        vm.expectRevert(LiqveraGuard.InsufficientFreeBalance.selector);
        guard.withdrawMUSD(1);
        guard.depositMUSD(5e18);
        guard.withdrawMUSD(5e18); // free part can leave
        vm.expectRevert(LiqveraGuard.InsufficientFreeBalance.selector);
        guard.withdrawBTC(1);
        vm.stopPrank();
    }

    function test_Withdraw_AfterDisarm() public {
        _armRepay(500e18, 10e18, 1.3e18);
        vm.startPrank(user);
        guard.disarm();
        guard.withdrawMUSD(510e18);
        vm.stopPrank();
        assertEq(guard.musdBalance(user), 0);
    }

    function test_OtherUserCannotTouchEscrow() public {
        vm.prank(user);
        guard.depositMUSD(100e18);
        vm.prank(keeper);
        vm.expectRevert(LiqveraGuard.InsufficientFreeBalance.selector);
        guard.withdrawMUSD(1);
    }

    // -------------------------------------------------------- arm

    function test_Arm_StoresPolicy() public {
        uint64 d = _armRepay(500e18, 10e18, 1.3e18);
        LiqveraGuard.Policy memory p = guard.policyOf(user);
        assertEq(uint8(p.action), uint8(LiqveraGuard.Action.RepayMUSD));
        assertEq(p.triggerICR, 1.3e18);
        assertEq(p.amount, 500e18);
        assertEq(p.keeperReward, 10e18);
        assertEq(p.deadline, d);
        assertEq(p.sigNonce, 0);
        assertEq(guard.freeMUSD(user), 0);
    }

    function test_Arm_RevertsWhenTriggerBelowMCR() public {
        vm.startPrank(user);
        guard.depositMUSD(510e18);
        bytes memory sig = _sign(PK, LiqveraGuard.Action.RepayMUSD, 500e18, 0, block.timestamp + 1 days);
        vm.expectRevert(LiqveraGuard.TriggerOutOfRange.selector);
        guard.arm(LiqveraGuard.Action.RepayMUSD, 1.1e18, 500e18, 10e18, uint64(block.timestamp + 1 days), sig);
        vm.expectRevert(LiqveraGuard.TriggerOutOfRange.selector);
        guard.arm(LiqveraGuard.Action.RepayMUSD, 11e18, 500e18, 10e18, uint64(block.timestamp + 1 days), sig);
        vm.stopPrank();
    }

    function test_Arm_RevertsOnBadDeadline() public {
        vm.startPrank(user);
        guard.depositMUSD(510e18);
        vm.expectRevert(LiqveraGuard.DeadlineOutOfRange.selector);
        guard.arm(LiqveraGuard.Action.RepayMUSD, 1.3e18, 500e18, 10e18, uint64(block.timestamp - 1), "");
        vm.expectRevert(LiqveraGuard.DeadlineOutOfRange.selector);
        guard.arm(LiqveraGuard.Action.RepayMUSD, 1.3e18, 500e18, 10e18, uint64(block.timestamp + 31 days), "");
        vm.stopPrank();
    }

    function test_Arm_RevertsOnNoneOrZero() public {
        vm.startPrank(user);
        vm.expectRevert(LiqveraGuard.InvalidAction.selector);
        guard.arm(LiqveraGuard.Action.None, 1.3e18, 1, 0, uint64(block.timestamp + 1), "");
        vm.expectRevert(LiqveraGuard.ZeroAmount.selector);
        guard.arm(LiqveraGuard.Action.RepayMUSD, 1.3e18, 0, 0, uint64(block.timestamp + 1), "");
        vm.stopPrank();
    }

    function test_Arm_RevertsWhenEscrowInsufficient() public {
        vm.startPrank(user);
        guard.depositMUSD(500e18);
        bytes memory sig = _sign(PK, LiqveraGuard.Action.RepayMUSD, 500e18, 0, block.timestamp + 1 days);
        vm.expectRevert(LiqveraGuard.InsufficientFreeBalance.selector);
        guard.arm(LiqveraGuard.Action.RepayMUSD, 1.3e18, 500e18, 10e18, uint64(block.timestamp + 1 days), sig);
        vm.expectRevert(LiqveraGuard.InsufficientFreeBalance.selector);
        guard.arm(LiqveraGuard.Action.AddColl, 1.3e18, 1, 0, uint64(block.timestamp + 1 days), sig);
        vm.stopPrank();
    }

    function test_Arm_RevertsWhenNoTrove() public {
        tm.setTrove(user, 3, 0, 0, 0); // liquidated
        vm.prank(user);
        vm.expectRevert(LiqveraGuard.TroveNotActive.selector);
        guard.arm(LiqveraGuard.Action.RepayMUSD, 1.3e18, 1, 0, uint64(block.timestamp + 1), "");
    }

    function test_Arm_RevertsBelowMinNetDebt() public {
        // Net debt 3000 - 200 = 2800. Repay 1001 => 1799 < 1800.
        vm.startPrank(user);
        guard.depositMUSD(1001e18);
        vm.expectRevert(LiqveraGuard.BelowMinNetDebt.selector);
        guard.arm(LiqveraGuard.Action.RepayMUSD, 1.3e18, 1001e18, 0, uint64(block.timestamp + 1 days), "");
        vm.stopPrank();
    }

    function test_Arm_AllowsExactlyMinNetDebt() public {
        _armRepay(1000e18, 0, 1.3e18);
        assertEq(guard.policyOf(user).amount, 1000e18);
    }

    function test_Arm_RevertsOnForeignSignature() public {
        vm.startPrank(user);
        guard.depositMUSD(510e18);
        uint64 d = uint64(block.timestamp + 1 days);
        bytes memory sig = _sign(0xB0B, LiqveraGuard.Action.RepayMUSD, 500e18, 0, d);
        vm.expectRevert(LiqveraGuard.BadSignature.selector);
        guard.arm(LiqveraGuard.Action.RepayMUSD, 1.3e18, 500e18, 10e18, d, sig);
        vm.stopPrank();
    }

    function test_Arm_RevertsOnWrongAmountOrNonceOrLength() public {
        vm.startPrank(user);
        guard.depositMUSD(1000e18);
        uint64 d = uint64(block.timestamp + 1 days);
        bytes memory sig = _sign(PK, LiqveraGuard.Action.RepayMUSD, 400e18, 0, d);
        vm.expectRevert(LiqveraGuard.BadSignature.selector);
        guard.arm(LiqveraGuard.Action.RepayMUSD, 1.3e18, 500e18, 0, d, sig);
        sig = _sign(PK, LiqveraGuard.Action.RepayMUSD, 500e18, 1, d);
        vm.expectRevert(LiqveraGuard.BadSignature.selector);
        guard.arm(LiqveraGuard.Action.RepayMUSD, 1.3e18, 500e18, 0, d, sig);
        vm.expectRevert(LiqveraGuard.BadSignature.selector);
        guard.arm(LiqveraGuard.Action.RepayMUSD, 1.3e18, 500e18, 0, d, hex"1234");
        // AddColl type hash differs from RepayMUSD type hash.
        sig = _sign(PK, LiqveraGuard.Action.AddColl, 500e18, 0, d);
        vm.expectRevert(LiqveraGuard.BadSignature.selector);
        guard.arm(LiqveraGuard.Action.RepayMUSD, 1.3e18, 500e18, 0, d, sig);
        vm.stopPrank();
    }

    function test_Arm_RevertsOnHighS() public {
        vm.startPrank(user);
        guard.depositMUSD(500e18);
        uint64 d = uint64(block.timestamp + 1 days);
        bytes32 h = guard.digest(LiqveraGuard.Action.RepayMUSD, 500e18, user, 0, d);
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(PK, h);
        uint256 n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141;
        bytes memory malleable = abi.encodePacked(r, bytes32(n - uint256(s)), v == 27 ? uint8(28) : uint8(27));
        vm.expectRevert(LiqveraGuard.BadSignature.selector);
        guard.arm(LiqveraGuard.Action.RepayMUSD, 1.3e18, 500e18, 0, d, malleable);
        vm.stopPrank();
    }

    function test_Arm_ReplacesPolicy() public {
        _armRepay(500e18, 10e18, 1.3e18);
        _armAddColl(0.01 ether, 0.0001 ether, 1.25e18);
        LiqveraGuard.Policy memory p = guard.policyOf(user);
        assertEq(uint8(p.action), uint8(LiqveraGuard.Action.AddColl));
        assertEq(guard.freeMUSD(user), 510e18); // old MUSD reservation released
        assertEq(guard.freeBTC(user), 0);
    }

    function test_Disarm_EmitsAndClears() public {
        _armRepay(500e18, 10e18, 1.3e18);
        vm.expectEmit(true, false, false, false);
        emit LiqveraGuard.Disarmed(user);
        vm.prank(user);
        guard.disarm();
        assertEq(uint8(guard.policyOf(user).action), 0);
        vm.prank(user);
        vm.expectRevert(abi.encodeWithSelector(LiqveraGuard.NotExecutable.selector, LiqveraGuard.Status.NoPolicy));
        guard.disarm();
    }

    // ------------------------------------------------------ checker

    function test_Checker_States() public {
        (bool ok,) = guard.checker(user);
        assertFalse(ok);
        (LiqveraGuard.Status s,) = guard.status(user);
        assertEq(uint8(s), uint8(LiqveraGuard.Status.NoPolicy));

        _armRepay(500e18, 10e18, 1.3e18);
        (ok,) = guard.checker(user);
        assertFalse(ok);
        (s,) = guard.status(user);
        assertEq(uint8(s), uint8(LiqveraGuard.Status.Healthy));

        _dropPriceTo120();
        uint256 icr;
        (ok, icr) = guard.checker(user);
        assertTrue(ok);
        assertEq(icr, 1.2e18);
    }

    function test_Checker_StaleNonce() public {
        _armRepay(500e18, 10e18, 1.3e18);
        _dropPriceTo120();
        sigs.bumpNonce(user);
        (LiqveraGuard.Status s,) = guard.status(user);
        assertEq(uint8(s), uint8(LiqveraGuard.Status.StaleNonce));
    }

    function test_Checker_Expired() public {
        uint64 d = _armRepay(500e18, 10e18, 1.3e18);
        _dropPriceTo120();
        vm.warp(d + 1);
        (LiqveraGuard.Status s,) = guard.status(user);
        assertEq(uint8(s), uint8(LiqveraGuard.Status.Expired));
    }

    function test_Checker_TroveClosed() public {
        _armRepay(500e18, 10e18, 1.3e18);
        tm.setTrove(user, 2, 0, 0, 0);
        (LiqveraGuard.Status s,) = guard.status(user);
        assertEq(uint8(s), uint8(LiqveraGuard.Status.TroveNotActive));
    }

    function test_Checker_MinNetDebtAfterInterestChange() public {
        // Arm at the limit, then debt falls (e.g. partial redemption): repay now breaks minNetDebt.
        _armRepay(1000e18, 0, 1.3e18);
        tm.setTrove(user, 1, COLL, 2900e18, 0);
        feed.setPrice(60_000e18);
        (LiqveraGuard.Status s,) = guard.status(user);
        assertEq(uint8(s), uint8(LiqveraGuard.Status.BelowMinNetDebt));
    }

    function test_Checker_StillBelowMCR() public {
        _armRepay(100e18, 0, 1.3e18);
        feed.setPrice(60_000e18); // ICR 100%. Repay 100 => 103% < 110%.
        (LiqveraGuard.Status s,) = guard.status(user);
        assertEq(uint8(s), uint8(LiqveraGuard.Status.StillBelowMCR));
        vm.prank(keeper);
        vm.expectRevert(abi.encodeWithSelector(LiqveraGuard.NotExecutable.selector, LiqveraGuard.Status.StillBelowMCR));
        guard.protect(user, address(0), address(0));
    }

    function test_Checker_MatchesProtect() public {
        _armRepay(500e18, 10e18, 1.3e18);
        (bool ok,) = guard.checker(user);
        assertFalse(ok);
        vm.prank(keeper);
        vm.expectRevert(abi.encodeWithSelector(LiqveraGuard.NotExecutable.selector, LiqveraGuard.Status.Healthy));
        guard.protect(user, address(0), address(0));

        _dropPriceTo120();
        (ok,) = guard.checker(user);
        assertTrue(ok);
        vm.prank(keeper);
        guard.protect(user, address(0), address(0));
    }

    // ------------------------------------------------------ protect

    function test_Protect_RevertsWhenHealthy() public {
        _armRepay(500e18, 10e18, 1.3e18);
        vm.prank(keeper);
        vm.expectRevert(abi.encodeWithSelector(LiqveraGuard.NotExecutable.selector, LiqveraGuard.Status.Healthy));
        guard.protect(user, address(0), address(0));
    }

    function test_Protect_RevertsWithoutPolicy() public {
        vm.prank(keeper);
        vm.expectRevert(abi.encodeWithSelector(LiqveraGuard.NotExecutable.selector, LiqveraGuard.Status.NoPolicy));
        guard.protect(user, address(0), address(0));
    }

    function test_Protect_RepayPath_CallsSignatures() public {
        _armRepay(500e18, 10e18, 1.3e18);
        _dropPriceTo120();
        vm.expectCall(
            address(sigs),
            abi.encodeCall(
                MockSignatures.repayMUSDWithSignature,
                (500e18, address(1), address(2), user, guard.policyOf(user).signature, guard.policyOf(user).deadline)
            )
        );
        vm.expectEmit(true, true, false, true);
        emit LiqveraGuard.Protected(user, keeper, LiqveraGuard.Action.RepayMUSD, 500e18, 1.2e18, 1.44e18, 10e18);
        vm.prank(keeper);
        guard.protect(user, address(1), address(2));
        (, uint256 principal,,,,) = tm.getEntireDebtAndColl(user);
        assertEq(principal, 2500e18);
        assertEq(sigs.getNonce(user), 1);
        assertEq(guard.musdBalance(user), 0);
        assertEq(musd.balanceOf(address(guard)), 0); // 500 burned, 10 paid
    }

    function test_Protect_RepayPath_InterestFirst() public {
        tm.setTrove(user, 1, COLL, 2900e18, 100e18);
        _armRepay(500e18, 0, 1.3e18);
        _dropPriceTo120();
        vm.prank(keeper);
        guard.protect(user, address(0), address(0));
        (, uint256 principal, uint256 interest,,,) = tm.getEntireDebtAndColl(user);
        assertEq(interest, 0);
        assertEq(principal, 2500e18);
    }

    function test_Protect_AddCollPath_SendsValue() public {
        _armAddColl(0.01 ether, 0.0001 ether, 1.3e18);
        _dropPriceTo120();
        uint256 sigsBefore = address(sigs).balance;
        vm.prank(keeper);
        guard.protect(user, address(0), address(0));
        assertEq(address(sigs).balance - sigsBefore, 0.01 ether);
        (uint256 coll,,,,,) = tm.getEntireDebtAndColl(user);
        assertEq(coll, 0.06 ether);
        assertEq(keeper.balance, 0.0001 ether);
        assertEq(guard.btcBalance(user), 0);
        assertEq(address(guard).balance, 0);
    }

    function test_Protect_PaysKeeper() public {
        _armRepay(500e18, 10e18, 1.3e18);
        _dropPriceTo120();
        vm.prank(keeper);
        guard.protect(user, address(0), address(0));
        assertEq(musd.balanceOf(keeper), 10e18);
    }

    function test_Protect_ZeroReward() public {
        _armRepay(500e18, 0, 1.3e18);
        _dropPriceTo120();
        vm.prank(keeper);
        guard.protect(user, address(0), address(0));
        assertEq(musd.balanceOf(keeper), 0);
    }

    function test_Protect_RevertsOnStaleNonce() public {
        _armRepay(500e18, 10e18, 1.3e18);
        _dropPriceTo120();
        sigs.bumpNonce(user);
        vm.prank(keeper);
        vm.expectRevert(abi.encodeWithSelector(LiqveraGuard.NotExecutable.selector, LiqveraGuard.Status.StaleNonce));
        guard.protect(user, address(0), address(0));
        // Escrow stays with the user and can be withdrawn after disarm.
        vm.startPrank(user);
        guard.disarm();
        guard.withdrawMUSD(510e18);
        vm.stopPrank();
    }

    function test_Protect_RevertsAfterDeadline() public {
        uint64 d = _armRepay(500e18, 10e18, 1.3e18);
        _dropPriceTo120();
        vm.warp(d + 1);
        vm.prank(keeper);
        vm.expectRevert(abi.encodeWithSelector(LiqveraGuard.NotExecutable.selector, LiqveraGuard.Status.Expired));
        guard.protect(user, address(0), address(0));
    }

    function test_Protect_CannotRunTwice() public {
        _armRepay(500e18, 10e18, 1.3e18);
        vm.prank(user);
        guard.depositMUSD(1000e18);
        _dropPriceTo120();
        vm.prank(keeper);
        guard.protect(user, address(0), address(0));
        feed.setPrice(50_000e18);
        vm.prank(keeper);
        vm.expectRevert(abi.encodeWithSelector(LiqveraGuard.NotExecutable.selector, LiqveraGuard.Status.NoPolicy));
        guard.protect(user, address(0), address(0));
    }

    /// @dev Front-running (R2): someone takes the public signature from `arm` calldata and calls
    /// Mezo directly with their own MUSD. Borrower debt goes down for free; the Guard policy
    /// becomes stale; the borrower's escrow is not touched.
    function test_FrontRun_DirectSignatureUse_HarmlessToBorrower() public {
        _armRepay(500e18, 10e18, 1.3e18);
        _dropPriceTo120();
        address attacker = makeAddr("attacker");
        musd.mint(attacker, 500e18);
        LiqveraGuard.Policy memory p = guard.policyOf(user);
        vm.prank(attacker);
        sigs.repayMUSDWithSignature(p.amount, address(0), address(0), user, p.signature, p.deadline);

        (bool ok,) = guard.checker(user);
        assertFalse(ok);
        vm.prank(keeper);
        vm.expectRevert(abi.encodeWithSelector(LiqveraGuard.NotExecutable.selector, LiqveraGuard.Status.StaleNonce));
        guard.protect(user, address(0), address(0));
        assertEq(guard.musdBalance(user), 510e18);
        assertEq(musd.balanceOf(attacker), 0);
    }

    function test_Protect_WorksInRecoveryMode() public {
        tm.setRecoveryMode(true);
        _armRepay(500e18, 10e18, 1.3e18);
        _dropPriceTo120();
        vm.prank(keeper);
        guard.protect(user, address(0), address(0));
        assertEq(sigs.getNonce(user), 1);
    }

    function test_Protect_RevertsWhenICRNotImproved() public {
        _armAddColl(0.01 ether, 0, 1.3e18);
        _dropPriceTo120();
        // Mezo call succeeds but the Trove is unchanged (simulated broken integration).
        vm.mockCall(address(sigs), abi.encodeWithSelector(MockSignatures.addCollWithSignature.selector), "");
        vm.prank(keeper);
        vm.expectRevert(abi.encodeWithSelector(LiqveraGuard.ICRNotImproved.selector, 1.2e18, 1.2e18));
        guard.protect(user, address(0), address(0));
    }

    function test_Protect_ReentrancyBlocked() public {
        _armAddColl(0.01 ether, 0.001 ether, 1.3e18);
        _dropPriceTo120();
        Reenterer r = new Reenterer(guard, user);
        vm.expectRevert(LiqveraGuard.TransferFailed.selector);
        r.go();
    }
}

contract Reenterer {
    LiqveraGuard g;
    address victim;

    constructor(LiqveraGuard g_, address v) {
        g = g_;
        victim = v;
    }

    function go() external {
        g.protect(victim, address(0), address(0));
    }

    receive() external payable {
        // Any re-entry must fail; the failure bubbles up as TransferFailed.
        g.withdrawBTC(1);
    }
}

/// @dev Fuzz + invariant: sum of user balances == contract holdings == totals.
contract GuardHandler is Test {
    LiqveraGuard g;
    MockMUSD m;
    address[] public actors;

    constructor(LiqveraGuard g_, MockMUSD m_) {
        g = g_;
        m = m_;
        for (uint256 i; i < 3; i++) {
            address a = address(uint160(0x1000 + i));
            actors.push(a);
            m.mint(a, 1e30);
            vm.deal(a, 1e30);
            vm.prank(a);
            m.approve(address(g), type(uint256).max);
        }
    }

    function depositMUSD(uint256 who, uint256 amt) external {
        amt = bound(amt, 1, 1e24);
        vm.prank(actors[who % 3]);
        g.depositMUSD(amt);
    }

    function depositBTC(uint256 who, uint256 amt) external {
        amt = bound(amt, 1, 1e24);
        vm.prank(actors[who % 3]);
        g.depositBTC{value: amt}();
    }

    function withdrawMUSD(uint256 who, uint256 amt) external {
        address a = actors[who % 3];
        uint256 free = g.freeMUSD(a);
        if (free == 0) return;
        vm.prank(a);
        g.withdrawMUSD(bound(amt, 1, free));
    }

    function withdrawBTC(uint256 who, uint256 amt) external {
        address a = actors[who % 3];
        uint256 free = g.freeBTC(a);
        if (free == 0) return;
        vm.prank(a);
        g.withdrawBTC(bound(amt, 1, free));
    }

    function sumMUSD() external view returns (uint256 s) {
        for (uint256 i; i < 3; i++) {
            s += g.musdBalance(actors[i]);
        }
    }

    function sumBTC() external view returns (uint256 s) {
        for (uint256 i; i < 3; i++) {
            s += g.btcBalance(actors[i]);
        }
    }
}

contract LiqveraGuardInvariantTest is GuardBase {
    GuardHandler h;

    function setUp() public override {
        super.setUp();
        h = new GuardHandler(guard, musd);
        targetContract(address(h));
    }

    function invariant_EscrowFullyBacked() public view {
        assertEq(h.sumMUSD(), guard.totalMUSDEscrow());
        assertEq(h.sumBTC(), guard.totalBTCEscrow());
        assertGe(musd.balanceOf(address(guard)), guard.totalMUSDEscrow());
        assertGe(address(guard).balance, guard.totalBTCEscrow());
    }

    function testFuzz_EscrowAccounting(uint96 a, uint96 b, uint96 w) public {
        vm.assume(a > 0 && b > 0);
        vm.deal(user, uint256(b));
        musd.mint(user, uint256(a));
        vm.startPrank(user);
        guard.depositMUSD(a);
        guard.depositBTC{value: b}();
        uint256 wm = bound(w, 0, a);
        if (wm > 0) guard.withdrawMUSD(wm);
        vm.stopPrank();
        assertEq(guard.musdBalance(user), uint256(a) - wm);
        assertEq(musd.balanceOf(address(guard)), guard.totalMUSDEscrow());
        assertEq(address(guard).balance, guard.totalBTCEscrow());
    }

    function testFuzz_ProtectAccounting(uint128 amount, uint128 reward) public {
        amount = uint128(bound(amount, 300e18, 1000e18));
        reward = uint128(bound(reward, 0, 50e18));
        _armRepay(amount, reward, 1.3e18);
        _dropPriceTo120();
        uint256 before = musd.balanceOf(address(guard));
        vm.prank(keeper);
        guard.protect(user, address(0), address(0));
        assertEq(before - musd.balanceOf(address(guard)), uint256(amount) + reward);
        assertEq(musd.balanceOf(address(guard)), guard.totalMUSDEscrow());
        assertGt(tm.getCurrentICR(user, feed.price()), 1.2e18);
    }
}
