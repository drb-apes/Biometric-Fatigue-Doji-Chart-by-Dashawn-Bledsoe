# Biometric-Fatigue-Doji-Chart-by-Dashawn-Bledsoe

Japanese Candlestick-style biometric fatigue-doji simulation.

## Run the simulation

Requires Python 3.10 or newer; there are no third-party dependencies.

```bash
python fatigue_simulation.py
```

The interactive prompt runs preset racing, boxing, American football, or
basketball scenarios, or all four. You can also run one or all without prompts
and optionally override the simulated tip pool:

```bash
python fatigue_simulation.py --sport racing --tip 25000
python fatigue_simulation.py --sport all
```

The demo uses synthetic scenario data on a shared normalized 0–100 index.
Fatigue doji detection follows `|Close - Open| <= delta` and
`High - Low >= gamma`. A matching candle prints a simulated sponsor activation
and an exact 60/20/10/10 allocation, with the sponsor share shown as a
prospective custodial sweep. Webhook latency and the separately displayed 25%
risk-event surcharge are illustrative only. The script sends no network
requests, processes no live biometric data, and transfers no money. The
referenced 3.1x–3.5x ROI is an unverified target, not a financial forecast.

Run the focused tests with:

```bash
python -m unittest discover -s tests -v
```
