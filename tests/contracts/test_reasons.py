"""Tests for stable normalized-pair shadow rejection reasons."""

import unittest

from mee_contracts.reasons import (
    SHADOW_REASON_ORDER,
    ShadowRejectCode,
)


class ShadowReasonOrderTests(unittest.TestCase):
    def test_shadow_reason_order_is_the_v2_contract(self) -> None:
        self.assertEqual(
            SHADOW_REASON_ORDER,
            (
                ShadowRejectCode.MARKET_MAPPING_REJECTED,
                ShadowRejectCode.UNSUPPORTED_PAYOFF,
                ShadowRejectCode.COST_MODEL_INCOMPLETE,
                ShadowRejectCode.TARGET_OVERSHOOT,
                ShadowRejectCode.QUANTITY_UNSUPPORTED,
                ShadowRejectCode.DEPTH_INSUFFICIENT,
                ShadowRejectCode.NON_POSITIVE_AFTER_COSTS,
            ),
        )


if __name__ == "__main__":
    unittest.main()
