"""Clickstream sessionization with PySpark window functions.

Input : events with columns (user_id, ts, url)
Output: events + session_id, per-session table, sessions per day, avg session length.

A new session starts when the gap to the user's previous event is
>= SESSION_TIMEOUT_MINUTES (30 by default), or when it is the user's first event.
"""
import argparse

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

SESSION_TIMEOUT_MINUTES = 30


def assign_sessions(events: DataFrame, timeout_minutes: int = SESSION_TIMEOUT_MINUTES) -> DataFrame:
    """Add prev_ts, is_new_session, session_seq and session_id columns."""
    w = Window.partitionBy("user_id").orderBy("ts", "url")  # url = deterministic tie-breaker
    w_cum = w.rowsBetween(Window.unboundedPreceding, Window.currentRow)

    return (
        events
        .withColumn("ts", F.col("ts").cast("timestamp"))
        .withColumn("prev_ts", F.lag("ts").over(w))
        .withColumn(
            "is_new_session",
            F.when(
                F.col("prev_ts").isNull()
                | ((F.col("ts").cast("long") - F.col("prev_ts").cast("long")) >= timeout_minutes * 60),
                1,
            ).otherwise(0),
        )
        .withColumn("session_seq", F.sum("is_new_session").over(w_cum))
        .withColumn("session_id", F.concat_ws("_", F.col("user_id"), F.col("session_seq")))
    )


def build_sessions(sessioned: DataFrame) -> DataFrame:
    """One row per session: start, end, length in seconds, number of events."""
    return (
        sessioned.groupBy("session_id", "user_id")
        .agg(
            F.min("ts").alias("session_start"),
            F.max("ts").alias("session_end"),
            F.count("*").alias("n_events"),
        )
        .withColumn(
            "session_length_sec",
            F.col("session_end").cast("long") - F.col("session_start").cast("long"),
        )
        .withColumn("session_date", F.to_date("session_start"))  # session counted on its start day
    )


def sessions_per_day(sessions: DataFrame) -> DataFrame:
    return (
        sessions.groupBy("session_date")
        .agg(
            F.count("*").alias("sessions"),
            F.round(F.avg("session_length_sec"), 2).alias("avg_session_length_sec"),
        )
        .orderBy("session_date")
    )


def avg_session_length(sessions: DataFrame) -> float:
    return sessions.agg(F.avg("session_length_sec")).first()[0]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="data/sample_events.csv")
    p.add_argument("--output", default="output")
    p.add_argument("--timeout-minutes", type=int, default=SESSION_TIMEOUT_MINUTES)
    args = p.parse_args()

    spark = SparkSession.builder.appName("sessionization").master("local[*]").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    events = spark.read.option("header", True).csv(args.input)
    sessioned = assign_sessions(events, args.timeout_minutes)
    sessions = build_sessions(sessioned)
    per_day = sessions_per_day(sessions)

    print("\n=== Events with session ids ===")
    sessioned.select("user_id", "ts", "url", "session_id").orderBy("user_id", "ts").show(100, False)
    print("=== Sessions ===")
    sessions.orderBy("user_id", "session_start").show(100, False)
    print("=== Sessions per day ===")
    per_day.show(truncate=False)
    print(f"=== Average session length: {avg_session_length(sessions):.2f} seconds ===\n")

    sessioned.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{args.output}/events_with_sessions")
    sessions.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{args.output}/sessions")
    per_day.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{args.output}/sessions_per_day")
    spark.stop()


if __name__ == "__main__":
    main()
