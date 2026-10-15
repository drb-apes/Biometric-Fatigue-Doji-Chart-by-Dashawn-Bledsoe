import unittest
from decimal import Decimal

from fatigue_simulation import Candle, SCENARIOS, clear_tip_pool, simulate


class CandleTests(unittest.TestCase):
    def test_doji_requires_small_body_and_wide_range(self):
        candle = Candle(
            "test",
            Decimal("50"),
            Decimal("90"),
            Decimal("20"),
            Decimal("50.5"),
            "test peak",
        )
        self.assertTrue(candle.is_doji(Decimal("1"), Decimal("10")))
        self.assertFalse(candle.is_doji(Decimal("0.1"), Decimal("10")))
        self.assertFalse(candle.is_doji(Decimal("1"), Decimal("80")))

    def test_invalid_ohlc_order_is_rejected(self):
        with self.assertRaises(ValueError):
            Candle(
                "test",
                Decimal("50"),
                Decimal("40"),
                Decimal("20"),
                Decimal("30"),
                "test peak",
            )


class ClearingTests(unittest.TestCase):
    def test_clearing_allocations_sum_to_tip_pool(self):
        allocations = clear_tip_pool(Decimal("25000"))
        self.assertEqual(
            allocations,
            {
                "Athlete NIL wallet": Decimal("15000.00"),
                "Team liquidity pool": Decimal("5000.00"),
                "Sponsor royalty / custodial sweep": Decimal("2500.00"),
                "Platform reserve": Decimal("2500.00"),
            },
        )
        self.assertEqual(sum(allocations.values()), Decimal("25000.00"))

    def test_non_positive_tip_pool_is_rejected(self):
        with self.assertRaises(ValueError):
            clear_tip_pool(Decimal("0"))


class SimulationTests(unittest.TestCase):
    def test_each_preset_scenario_triggers_doji_and_clearing(self):
        for scenario in SCENARIOS.values():
            with self.subTest(sport=scenario.name):
                report = "\n".join(simulate(scenario))
                self.assertIn("FATIGUE_DOJI", report)
                self.assertIn("60/20/10/10", report)
                self.assertIn("no request sent", report)

    def test_custom_tip_amount_is_used(self):
        report = "\n".join(simulate(SCENARIOS["racing"], Decimal("100")))
        self.assertIn("Athlete NIL wallet: $60.00", report)
        self.assertIn("Platform reserve: $10.00", report)


if __name__ == "__main__":
    unittest.main()
