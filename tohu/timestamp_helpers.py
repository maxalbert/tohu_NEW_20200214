import pandas as pd


def convert_to_pandas_timestamp(ts):
    if isinstance(ts, pd.Timestamp):
        return ts
    elif isinstance(ts, str):
        return pd.Timestamp(ts)
    else:
        raise NotImplementedError(f"Cannot convert input to pandas timestamp: {ts}")


def normalise_start_and_stop_timestamps_from_optional_start_stop_and_date(start, stop, date):
    if date is None:
        #
        # Start/stop arguments were specified
        #
        if start is None and stop is None:
            raise ValueError("Please provide arguments `start`/`stop` or `date`.")
        elif start is None:
            raise ValueError("Argument `start` is missing.")
        elif stop is None:
            raise ValueError("Argument `stop` is missing.")
        else:
            ts_start = convert_to_pandas_timestamp(start)
            ts_stop = convert_to_pandas_timestamp(stop)
            if ts_start == ts_stop:
                raise ValueError("`start` and `stop` timestamps must not be identical")
            elif ts_start > ts_stop:
                raise ValueError("`start` timestamp must be earlier than `stop`")
            else:
                return ts_start, ts_stop
    else:
        #
        # Date argument was specified; derive
        #
        if start is not None or stop is not None:
            raise ValueError("Arguments `start`/`stop` and `date` are mutually exclusive.")
        else:
            ts_date = pd.Timestamp(date)
            ts_start = ts_date
            ts_stop = ts_date + pd.Timedelta(days=1)
            return ts_start, ts_stop
