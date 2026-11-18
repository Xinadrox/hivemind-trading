CREATE TABLE eodhd_daily_prices (
    symbol text NOT NULL CHECK (symbol ~ '^[A-Z0-9][A-Z0-9-]{0,19}\.ST$'),
    trading_date date NOT NULL,
    open numeric(24, 12) NOT NULL CHECK (open > 0 AND open < 'NaN'::numeric),
    high numeric(24, 12) NOT NULL CHECK (high > 0 AND high < 'NaN'::numeric),
    low numeric(24, 12) NOT NULL CHECK (low > 0 AND low < 'NaN'::numeric),
    close numeric(24, 12) NOT NULL CHECK (close > 0 AND close < 'NaN'::numeric),
    adjusted_close numeric(24, 12) NOT NULL
        CHECK (adjusted_close > 0 AND adjusted_close < 'NaN'::numeric),
    volume bigint NOT NULL CHECK (volume > 0),
    PRIMARY KEY (symbol, trading_date),
    CHECK (open BETWEEN low AND high AND close BETWEEN low AND high)
);
