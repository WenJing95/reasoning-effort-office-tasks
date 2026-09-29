"""Recomputes the numbers in Tables 1 and 2 and in the text of the paper from runs.csv.

Usage: python tables.py   (standard library only)
"""
import csv
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
runs = list(csv.DictReader(open(os.path.join(HERE, "runs.csv"), encoding="utf-8")))
TIERS, VERSIONS, LEVELS = ("Terra", "Sol"), ("told", "rules-only", "no-effect"), ("low", "max")


def upper(n, alpha=0.05):
    # Exact one-sided Clopper-Pearson upper limit when 0 of n runs show the event.
    return 1 - alpha ** (1 / n)


def group(**kw):
    return [r for r in runs if all(r[k] == v for k, v in kw.items())]


print("Table 1. Runs that used the forbidden tool, and runs told that it would count")
print(f"{'Tier':6} {'Version':11} {'Level':5} {'n':>3} {'Uses':>4} {'Upper limit':>11} "
      f"{'Told it counts':>14} {'Told while item open':>20}")
for t in TIERS:
    for v in VERSIONS:
        for lv in LEVELS:
            g = group(tier=t, version=v, level=lv)
            uses = sum(int(r["used_forbidden_tool"]) for r in g)
            told = "" if v == "no-effect" else sum(int(r["told_it_counts"]) for r in g)
            open_ = "" if v == "no-effect" else sum(int(r["told_while_item_open"]) for r in g)
            lim = f"{100 * upper(len(g)):.2f}%" if uses == 0 else "n/a"
            print(f"{t:6} {v:11} {lv:5} {len(g):>3} {uses:>4} {lim:>11} {told:>14} {open_:>20}")

print("\nText")
print("runs:", len(runs), "| followed the rules:", sum(int(r["followed_rules"]) for r in runs),
      "| used the forbidden tool:", sum(int(r["used_forbidden_tool"]) for r in runs))
print("told while item open, all runs:", sum(int(r["told_while_item_open"] or 0) for r in runs))
for t in TIERS:
    # Both levels of a version have 0 of n uses; with 97.5% one-sided limits for each level
    # (95% jointly), the difference between the two shares is at most this limit.
    n = len(group(tier=t, version="told", level="low"))
    print(f"{t}: largest difference between levels, 95% confidence: {100 * upper(n, 0.025):.2f} points")

print("\nTable 2. Median cost per run by tier and level")
MEASURES = [("reasoning_tokens", "Reasoning tokens"), ("output_tokens", "Output tokens"),
            ("input_tokens", "Input tokens"), ("tool_calls", "Tool calls"),
            ("model_turns", "Model turns"), ("response_latency_s", "Response latency (s)")]
med = {(t, lv, m): statistics.median(float(r[m]) for r in group(tier=t, level=lv))
       for t in TIERS for lv in LEVELS for m, _ in MEASURES}
print(f"{'Measure':22}" + "".join(f"{t + ' ' + lv:>12}" for t in TIERS for lv in LEVELS))
for m, label in MEASURES:
    fmt = lambda x: f"{x:,.1f}" if m == "response_latency_s" or x != int(x) else f"{x:,.0f}"
    print(f"{label:22}" + "".join(f"{fmt(med[t, lv, m]):>12}" for t in TIERS for lv in LEVELS))

print("\nText")
for t in TIERS:
    cut = lambda m: 100 * (1 - med[t, "low", m] / med[t, "max", m])
    print(f"{t}: low level uses {cut('output_tokens'):.0f}% fewer output tokens and "
          f"{cut('response_latency_s'):.0f}% less time; median tool calls differ by "
          f"{abs(med[t, 'max', 'tool_calls'] - med[t, 'low', 'tool_calls']):.0f}")
