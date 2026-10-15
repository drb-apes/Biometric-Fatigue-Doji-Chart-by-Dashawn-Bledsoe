"""Offline multi-sport fatigue-doji and tip-clearing simulation."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


CENT = Decimal("0.01")
DOJI_DELTA = Decimal("1")
DOJI_GAMMA = Decimal("10")


@dataclass(frozen=True)
class Candle:
    """OHLC values on a shared, normalized 0–100 readiness/stress index."""

    interval: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    peak_measurement: str

    def __post_init__(self) -> None:
        if not (0 <= self.low <= self.open <= self.high <= 100):
            raise ValueError("Candle low/open/high must be ordered within 0–100")
        if not (self.low <= self.close <= self.high):
            raise ValueError("Candle close must be between low and high")

    def is_doji(
        self, delta: Decimal = DOJI_DELTA, gamma: Decimal = DOJI_GAMMA
    ) -> bool:
        if delta < 0 or gamma < 0:
            raise ValueError("Doji thresholds must be non-negative")
        return abs(self.close - self.open) <= delta and (
            self.high - self.low
        ) >= gamma


@dataclass(frozen=True)
class SportScenario:
    name: str
    tip_pool: Decimal
    webhook_ms: int
    activation: str
    sensor_context: str
    fatigue_interpretation: str
    candles: tuple[Candle, ...]


def _candle(
    interval: str,
    opening: str,
    high: str,
    low: str,
    close: str,
    peak_measurement: str,
) -> Candle:
    return Candle(
        interval,
        Decimal(opening),
        Decimal(high),
        Decimal(low),
        Decimal(close),
        peak_measurement,
    )


SCENARIOS = {
    "racing": SportScenario(
        "Racing",
        Decimal("25000"),
        460,
        "2D broadcast lower-third, Jumbotron ticker, and geofenced QR offer",
        "steering torque, neck lateral G-force (up to 5.5G), core temperature, "
        "and brake pressure at a synthetic 1,000 Hz profile",
        "5.2G cornering with a compressed body signals steering micro-drift "
        "and exhaustion",
        (
            _candle("Lap 47", "78", "90", "70", "76", "5.0G cornering"),
            _candle("Lap 48", "62", "94", "30", "63", "5.2G cornering"),
        ),
    ),
    "boxing": SportScenario(
        "Boxing",
        Decimal("40000"),
        420,
        "Monster Energy Impact Alert on the PPV side banner and $1.00 "
        "energy-drink coupon",
        "smart-glove impact, mouthguard rotational acceleration, and "
        "cardiac telemetry at a synthetic 1,000 Hz profile",
        "Round 9 impact followed by recovery collapse; heart rate remains "
        "at 178 BPM",
        (
            _candle("Round 8", "80", "91", "68", "74", "38g glove impact"),
            _candle("Round 9", "60", "96", "28", "60.5", "42g glove impact"),
        ),
    ),
    "football": SportScenario(
        "American Football",
        Decimal("50000"),
        480,
        "McDonald's stadium Jumbotron, TV lower-third, and QR offer",
        "shoulder-pad collision force, cleat acceleration, and late-game "
        "two-minute-drill HRV at a synthetic 1,000 Hz profile",
        "after six consecutive plays, an 18.5 mph sprint coincides with a "
        "0.4-point compressed body",
        (
            _candle("Play 5", "76", "90", "66", "70", "17.8 mph sprint"),
            _candle("Play 6", "61", "95", "25", "61.4", "18.5 mph sprint"),
        ),
    ),
    "basketball": SportScenario(
        "Basketball",
        Decimal("30000"),
        410,
        "Nike 2D broadcast lower-third and venue ticker",
        "insole jump force and landing impact, waist IMU deceleration, and "
        "cardiac strain at a synthetic 1,000 Hz profile",
        "after 44 minutes, readiness barely moves from 88.4 to 88.6 despite "
        "a 38-inch jump",
        (
            _candle("Minute 43", "89.1", "96", "82", "88.0", "37-inch vertical"),
            _candle("Minute 44", "88.4", "98", "82", "88.6", "38-inch vertical"),
        ),
    ),
}


def clear_tip_pool(amount: Decimal) -> dict[str, Decimal]:
    """Split a positive USD pool into 60/20/10/10 buckets, rounded to cents."""
    amount = amount.quantize(CENT, rounding=ROUND_HALF_UP)
    if amount <= 0:
        raise ValueError("Tip pool must be greater than zero")

    athlete = (amount * Decimal("0.60")).quantize(CENT, rounding=ROUND_HALF_UP)
    team = (amount * Decimal("0.20")).quantize(CENT, rounding=ROUND_HALF_UP)
    sponsor = (amount * Decimal("0.10")).quantize(CENT, rounding=ROUND_HALF_UP)
    reserve = amount - athlete - team - sponsor
    return {
        "Athlete NIL wallet": athlete,
        "Team liquidity pool": team,
        "Sponsor royalty / custodial sweep": sponsor,
        "Platform reserve": reserve,
    }


def _state(candle: Candle, delta: Decimal, gamma: Decimal) -> str:
    if candle.is_doji(delta, gamma):
        return "FATIGUE_DOJI"
    if candle.close < candle.open:
        return "STRAINED"
    if candle.close > candle.open:
        return "RECOVERING"
    return "READY"


def simulate(
    scenario: SportScenario,
    tip_pool: Decimal | None = None,
    delta: Decimal = DOJI_DELTA,
    gamma: Decimal = DOJI_GAMMA,
) -> list[str]:
    """Return a readable offline simulation report for one sport."""
    if scenario.webhook_ms < 0:
        raise ValueError("Simulated webhook latency must be non-negative")
    amount = scenario.tip_pool if tip_pool is None else tip_pool
    lines = [
        f"\n=== {scenario.name} | offline simulation ===",
        "OHLC values use a shared normalized readiness/stress index (0–100).",
        f"Synthetic sensor profile: {scenario.sensor_context}.",
        f"Fatigue interpretation: {scenario.fatigue_interpretation}.",
    ]
    doji_found = False
    for candle in scenario.candles:
        state = _state(candle, delta, gamma)
        lines.append(
            f"{candle.interval}: O={candle.open} H={candle.high} "
            f"L={candle.low} C={candle.close} | "
            f"peak={candle.peak_measurement} | {state}"
        )
        if state == "FATIGUE_DOJI":
            doji_found = True

    if not doji_found:
        lines.append("No fatigue doji detected; no sponsor activation simulated.")
        return lines

    lines.extend(
        [
            f"Doji thresholds: |C - O| <= {delta} and H - L >= {gamma}.",
            f"Simulated POST /api/sponsor/activation/track: "
            f"{scenario.webhook_ms} ms (no request sent).",
            f"Activation: {scenario.activation}.",
            "Risk-event surcharge estimate (+25%, displayed separately): "
            f"${(amount * Decimal('0.25')).quantize(CENT):,.2f}.",
            "Clearing split (60/20/10/10, illustrative; no funds transferred):",
        ]
    )
    for bucket, value in clear_tip_pool(amount).items():
        lines.append(f"  {bucket}: ${value:,.2f}")
    lines.append(
        "Sponsor bucket destination is modeled as a custodial sweep "
        "(Morgan Stanley GSE 3.0, J.P. Morgan, or Capital One); "
        "3.1x–3.5x ROI is an unverified target, not a forecast or guarantee."
    )
    lines.append(
        "Example risk methods: Method 1 adaptive trailing stop, Method 2 "
        "pattern-only exit, Method 4 volatility hard threshold, "
        "Method 21 collapse prediction."
    )
    return lines


def _interactive() -> int:
    print("Offline biometric fatigue-doji simulation")
    print("No live sensor, webhook, payment, or custodial integrations are used.")
    print("Sports: " + ", ".join(SCENARIOS))
    selection = input("Choose a sport or 'all' [all]: ").strip().lower() or "all"
    if selection != "all" and selection not in SCENARIOS:
        print(f"Unknown sport: {selection}")
        return 2
    chosen = list(SCENARIOS.values()) if selection == "all" else [SCENARIOS[selection]]
    for scenario in chosen:
        raw_tip = input(
            f"{scenario.name} tip pool in USD "
            f"[{scenario.tip_pool:.2f}]: "
        ).strip()
        try:
            tip = Decimal(raw_tip) if raw_tip else scenario.tip_pool
            for line in simulate(scenario, tip):
                print(line)
        except (ValueError, ArithmeticError) as error:
            print(f"Invalid simulation input: {error}")
            return 2
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sport",
        choices=(*SCENARIOS, "all"),
        help="run one sport or all preset scenarios (omit for interactive mode)",
    )
    parser.add_argument("--tip", type=Decimal, help="override the USD tip pool")
    args = parser.parse_args()
    if args.sport is None:
        return _interactive()
    if args.sport == "all":
        for scenario in SCENARIOS.values():
            for line in simulate(scenario, args.tip):
                print(line)
    else:
        for line in simulate(SCENARIOS[args.sport], args.tip):
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
