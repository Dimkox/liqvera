// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {Script, console2} from "forge-std/Script.sol";
import {LiqveraGuard} from "../src/LiqveraGuard.sol";
import {
    IBorrowerOperationsSignatures,
    IBorrowerOperationsLite,
    ITroveManagerLite,
    IPriceFeedLite,
    IERC20Lite
} from "../src/interfaces/IMezo.sol";

/// @notice Deploy LiqveraGuard on Mezo Testnet (chain 31611). NOT run in this PR.
/// Dry run:  forge script script/Deploy.s.sol --rpc-url $MEZO_TESTNET_RPC
/// Real run (needs owner approval): add --broadcast --account <keystore> --verify
contract Deploy is Script {
    address constant SIGS = 0xD757e3646AF370b15f32EB557F0F8380Df7D639e;
    address constant BO = 0xCdF7028ceAB81fA0C6971208e83fa7872994beE5;
    address constant TM = 0xE47c80e8c23f6B4A1aE41c34837a0599D5D16bb0;
    address constant FEED = 0x86bCF0841622a5dAC14A313a15f96A95421b9366;
    address constant MUSD = 0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503;

    function run() external returns (LiqveraGuard guard) {
        require(block.chainid == 31611, "Mezo Testnet only");
        vm.startBroadcast();
        guard = new LiqveraGuard(
            IBorrowerOperationsSignatures(SIGS),
            IBorrowerOperationsLite(BO),
            ITroveManagerLite(TM),
            IPriceFeedLite(FEED),
            IERC20Lite(MUSD)
        );
        vm.stopBroadcast();
        console2.log("LiqveraGuard", address(guard));
    }
}
