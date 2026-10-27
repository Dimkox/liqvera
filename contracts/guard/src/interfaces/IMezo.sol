// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

/// @notice Minimal views of the Mezo MUSD contracts that LiqveraGuard uses.
/// Signatures checked against mezo-org/musd commit da7888a and the Blockscout-verified
/// implementation on Mezo Testnet (chain 31611). See docs/guard.md, Q1-Q5.

interface IBorrowerOperationsSignatures {
    /// @dev Signed struct: AddColl(uint256 assetAmount,address borrower,uint256 nonce,uint256 deadline).
    /// assetAmount is msg.value of the caller.
    function addCollWithSignature(
        address upperHint,
        address lowerHint,
        address borrower,
        bytes memory signature,
        uint256 deadline
    ) external payable;

    /// @dev Signed struct: RepayMUSD(uint256 amount,address borrower,uint256 nonce,uint256 deadline).
    /// MUSD is burned from msg.sender (the caller), not from the borrower.
    function repayMUSDWithSignature(
        uint256 amount,
        address upperHint,
        address lowerHint,
        address borrower,
        bytes memory signature,
        uint256 deadline
    ) external;

    /// @dev The `nonces` mapping is private in the deployed code. This is the only getter (Q1).
    function getNonce(address user) external view returns (uint256);
}

interface ITroveManagerLite {
    function getCurrentICR(address borrower, uint256 price) external view returns (uint256);

    /// @dev 0 nonExistent, 1 active, 2 closedByOwner, 3 closedByLiquidation, 4 closedByRedemption.
    function getTroveStatus(address borrower) external view returns (uint8);

    /// @dev Order confirmed on the fork (Q5).
    function getEntireDebtAndColl(address borrower)
        external
        view
        returns (
            uint256 coll,
            uint256 principal,
            uint256 interest,
            uint256 pendingCollateral,
            uint256 pendingPrincipal,
            uint256 pendingInterest
        );

    function checkRecoveryMode(uint256 price) external view returns (bool);

    function MCR() external view returns (uint256);

    function MUSD_GAS_COMPENSATION() external view returns (uint256);
}

interface IBorrowerOperationsLite {
    function minNetDebt() external view returns (uint256);
}

interface IPriceFeedLite {
    function fetchPrice() external view returns (uint256);
}

interface IERC20Lite {
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}
