"""Alvo híbrido do Caçador: ATR + bounce mediano + teto da estratégia."""

from __future__ import annotations

import unittest

from app.hunter import analyze_candles, suggested_levels


def _bars(*, n: int = 40, close: float = 100.0, rng: float = 2.0, step_ms: int = 4 * 3_600_000):
    rows = []
    ts = 1_700_000_000_000
    px = close
    for i in range(n):
        # pequeno ruído + dips a cada 8 barras
        dip = 2.4 if i % 8 == 4 else 0.0
        c = px - dip
        rows.append(
            {
                "ts": ts + i * step_ms,
                "o": px,
                "h": c + rng,
                "l": c - rng,
                "c": c,
            }
        )
        px = c + (0.8 if dip else 0.1)
    return rows


class HunterTargetTest(unittest.TestCase):
    def test_preset_only_without_features(self):
        out = suggested_levels(1.0, profit_target_pct=2.2, fee_rate_pct=0.10, spread_pct_val=0.25)
        self.assertEqual(out["suggested_target_source"], "preset")
        self.assertAlmostEqual(out["suggested_target_pct"], 2.2)
        self.assertAlmostEqual(out["suggested_target_gross_pct"], 2.65)
        self.assertAlmostEqual(out["suggested_target_px"], 1.0265)

    def test_atr_caps_huge_preset(self):
        candles = _bars(n=48, rng=1.0)
        feat = analyze_candles(candles, horizon="weekly")
        self.assertTrue(feat.get("ok"))
        self.assertIsNotNone(feat.get("atr_daily_pct"))
        feat["bounce_median_pct"] = None
        out = suggested_levels(
            candles[-1]["c"],
            profit_target_pct=20.0,
            fee_rate_pct=0.10,
            spread_pct_val=0.10,
            horizon="weekly",
            features=feat,
        )
        self.assertEqual(out["suggested_target_source"], "atr")
        self.assertLess(out["suggested_target_pct"], 20.0)
        self.assertGreater(out["suggested_target_pct"], 0.15)

    def test_bounce_can_bind(self):
        candles = _bars(n=56, rng=0.4)
        feat = analyze_candles(candles, horizon="daily")
        self.assertTrue(feat.get("ok"))
        bounce = feat.get("bounce_median_pct")
        if bounce is None:
            self.skipTest("sem amostra de bounce neste sintético")
        out = suggested_levels(
            candles[-1]["c"],
            profit_target_pct=12.0,
            fee_rate_pct=0.10,
            spread_pct_val=0.05,
            horizon="daily",
            features={**feat, "atr_daily_pct": 30.0},
        )
        self.assertEqual(out["suggested_target_source"], "bounce")
        self.assertAlmostEqual(out["suggested_target_pct"], bounce, places=3)

    def test_floor_when_all_tiny(self):
        out = suggested_levels(
            1.0,
            profit_target_pct=0.02,
            fee_rate_pct=0.10,
            spread_pct_val=0.05,
            horizon="daily",
            features={"ok": True, "atr_daily_pct": 0.01, "bounce_median_pct": 0.02},
        )
        self.assertEqual(out["suggested_target_source"], "floor")
        self.assertAlmostEqual(out["suggested_target_pct"], 0.15)


if __name__ == "__main__":
    unittest.main()
