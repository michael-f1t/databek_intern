# Clickstream Sessionization with PySpark

Assigns session ids to clickstream events `(user_id, ts, url)` using **PySpark window functions**
(a new session starts after 30 minutes of inactivity), then computes **sessions per day** and
**average session length**.

## How it works

For each user, events are ordered by time and three window functions do the work:

1. `lag(ts)` over `PARTITION BY user_id ORDER BY ts` gets the previous event time.
2. `is_new_session = 1` if there is no previous event or the gap is **>= 30 minutes**, else `0`.
3. A running `sum(is_new_session)` over the same window gives a per-user `session_seq`;
   `session_id = user_id + "_" + session_seq`.

Then events are aggregated per session:

- `session_length_sec = max(ts) - min(ts)` (a one-event session has length 0)
- `session_date` = date the session **started** (a session crossing midnight counts once, on its start day)

## Project structure

```
data/sample_events.csv     # sample input (21 events, 4 users, edge cases included)
src/sessionize.py          # the pipeline
tests/test_sessionize.py   # pytest unit tests
requirements.txt
```

## Run

Requires Python 3.9+ and Java 8/11/17+.

```bash
pip install -r requirements.txt
python src/sessionize.py                       # uses data/sample_events.csv
python src/sessionize.py --input my.csv --timeout-minutes 30 --output output
pytest -q
```

Input CSV needs a header: `user_id,ts,url` with `ts` like `2024-03-01 09:00:00`.
Results are printed and written as CSV to `output/` (`events_with_sessions`, `sessions`, `sessions_per_day`).

## Sample result

| session_date | sessions | avg_session_length_sec |
|--------------|---------:|-----------------------:|
| 2024-03-01   | 8        | 824.75                 |
| 2024-03-02   | 4        | 45.00                  |

**Overall average session length: 564.83 seconds (~9.4 min)** across 12 sessions.

Edge cases covered in the sample data:

- gap of exactly 30:00 (`u2` 11:00 -> 11:30) starts a new session; 29:59 gaps (`u3`) do not
- session crossing midnight (`u2` 23:50 -> 00:10) counted on its start date
- single-event sessions (length 0)
- users are sessionized independently

## Assumptions / notes

- "After 30 minutes of inactivity" is implemented as gap `>= 30 min`; change `>=` to `>` in
  `assign_sessions` for the strict interpretation.
- Average session length includes single-event sessions (length 0). Filter `n_events > 1` if you prefer to exclude them.
- Ties on identical timestamps are broken by `url` for deterministic output.
- Window functions partition by `user_id`, so the job scales horizontally across users.
