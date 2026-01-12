# Stock Valuation Module

A comprehensive P/E multiple-based stock valuation system that calculates fair value price ranges using forward earnings estimates, historical P/E ratios, peer comparison, and fundamentals analysis.

## Quick Start

### 1. Calculate Valuation (No Peers)

```bash
curl -X POST http://localhost:8000/api/valuation/AAPL \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 2. Calculate Valuation (With Peer Comparison)

```bash
curl -X POST http://localhost:8000/api/valuation/AAPL \
  -H "Content-Type: application/json" \
  -d '{"peers": ["MSFT", "GOOGL", "META"]}'
```

### 3. Get Cached Valuation

```bash
curl "http://localhost:8000/api/valuation/AAPL?peers=MSFT,GOOGL,META"
```

---

## API Endpoints

### POST /api/valuation/{symbol}

Calculate fresh stock valuation with comprehensive analysis.

**Request Body:**
```json
{
  "peers": ["MSFT", "GOOGL", "META"]  // Optional
}
```

**Response:** Complete valuation report (see example below)

**Cache:** Results cached for 24 hours

---

### GET /api/valuation/{symbol}

Retrieve cached valuation if available and fresh.

**Query Parameters:**
- `peers` (optional): Comma-separated peer tickers (e.g., `?peers=MSFT,GOOGL,META`)

**Response:** Simplified cached data or 404 if not found/expired

**Note:** Peer order doesn't matter for cache lookup (`MSFT,GOOGL,META` = `META,GOOGL,MSFT`)

---

## Valuation Methodology

The module performs a 5-step P/E multiple valuation:

### 1. Forward EPS Estimation (Dual Methods)

**Growth Rate Method:**
- Calculate quarter-over-quarter EPS growth rates for last 8 quarters
- Average the growth rates
- Project forward 4 quarters using compound growth
- Formula: `EPS(t+i) = Latest_EPS × (1 + avg_growth)^i`

**Linear Regression Method:**
- Fit linear trend to last 8 quarters: `EPS = slope × quarter + intercept`
- Predict next 4 quarters using trend line
- R² value indicates trend strength (0 = no trend, 1 = perfect trend)

**Recommended EPS:** Average of both methods

---

### 2. Historical P/E Analysis

For each quarter with sufficient data (need 4 quarters for TTM):
1. Calculate **TTM EPS** = Sum of last 4 quarterly EPS
2. Get **stock price** at the earnings report date (from yfinance)
3. Calculate **P/E ratio** = Price ÷ TTM EPS

Statistics: Average, Median, Min, Max, Standard Deviation

---

### 3. Peer Comparison (Optional)

If peers provided:
1. Fetch financial data for each peer ticker
2. Calculate TTM EPS for each peer
3. Get current price for each peer
4. Calculate P/E ratio for each peer
5. Compute peer group statistics: Average, Median, Range

---

### 4. Fundamentals-Based P/E

Start with market baseline P/E of **15.0**, then adjust:

**Growth Adjustment:** `+0.5 × EPS_growth_rate × 100`
- Rewards growth, penalizes decline
- Example: 10% growth → +5.0, -10% decline → -5.0

**Margin Adjustment:**
- +3 if net margin > 20%
- +2 if margins improving
- +0 otherwise

**Risk Adjustment:**
- -2 if debt-to-equity > 1.5
- -2 if margins declining
- +0 otherwise

**Formula:** `Fundamentals_PE = 15 + Growth_Adj + Margin_Adj + Risk_Adj`

---

### 5. Justified P/E Synthesis

Weighted average of available P/E estimates:

**Without Peers:**
- 57% Historical P/E
- 43% Fundamentals P/E

**With Peers:**
- 40% Historical P/E
- 30% Peer Average P/E
- 30% Fundamentals P/E

**Range Calculation:**
- Midpoint = Weighted average
- Range = Midpoint ± 10% or ± 1 standard deviation (whichever is larger)

---

### 6. Fair Value Calculation

**Fair Value = Forward EPS × Justified P/E**

- **Low estimate** = Forward EPS × Justified P/E Low
- **High estimate** = Forward EPS × Justified P/E High
- **Midpoint** = Average of low and high

**Upside/Downside:** `(Fair Value - Current Price) / Current Price × 100%`

**Assessment:**
- **Undervalued:** Current price < Fair Value Low (potential buy)
- **Fairly Valued:** Current price within Fair Value range
- **Overvalued:** Current price > Fair Value High (potential sell)

---

## Example Response

```json
{
  "symbol": "AAPL",
  "company_name": "Apple Inc",
  "valuation_date": "2026-01-10T01:19:28.693662",

  "current_metrics": {
    "current_price": 259.37,
    "ttm_eps": 7.47,
    "current_pe": 34.72
  },

  "forward_eps": {
    "growth_method": {
      "forward_eps": 9.13,
      "growth_rate": 0.0859,
      "quarterly_estimates": [2.01, 2.18, 2.37, 2.57]
    },
    "regression_method": {
      "forward_eps": 6.80,
      "slope": 0.0008,
      "r_squared": 0.0,
      "quarterly_estimates": [1.70, 1.70, 1.70, 1.70]
    },
    "recommended": 7.96
  },

  "historical_pe": {
    "pe_ratios": [
      {
        "quarter": "2024-Q3",
        "fiscal_date": "2024-09-30",
        "reported_date": "2024-10-31",
        "eps": 0.97,
        "ttm_eps": 6.08,
        "price": 224.65,
        "pe_ratio": 36.95
      }
      // ... more quarters
    ],
    "average": 35.07,
    "median": 36.30,
    "min": 31.43,
    "max": 37.54,
    "std_dev": 2.38
  },

  "peer_comparison": {
    "peer_pe_ratios": [
      {
        "ticker": "MSFT",
        "pe": 34.09,
        "ttm_eps": 14.06,
        "price": 479.28
      },
      {
        "ticker": "GOOGL",
        "pe": 32.40,
        "ttm_eps": 10.14,
        "price": 328.57
      },
      {
        "ticker": "META",
        "pe": 22.64,
        "ttm_eps": 28.84,
        "price": 653.06
      }
    ],
    "average_pe": 29.71,
    "median_pe": 32.40,
    "range": [22.64, 34.09]
  },

  "fundamentals_analysis": {
    "fundamentals_pe": 11.65,
    "components": {
      "base_pe": 15.0,
      "growth_adjustment": -4.35,
      "margin_adjustment": 3,
      "risk_adjustment": -2
    },
    "metrics": {
      "eps_growth_rate": -0.0895,
      "revenue_growth_rate": -0.0845,
      "avg_net_margin": 0.2673,
      "margin_trend": "declining",
      "debt_to_equity": 0.18
    }
  },

  "justified_pe": {
    "justified_pe_low": 16.42,
    "justified_pe_high": 36.45,
    "justified_pe_midpoint": 26.44,
    "weighting": {
      "historical": 0.4,
      "peer": 0.3,
      "fundamentals": 0.3
    }
  },

  "fair_value": {
    "fair_value_low": 130.79,
    "fair_value_high": 290.32,
    "fair_value_midpoint": 210.55,
    "current_price": 259.37,
    "upside_percent": -18.82,
    "assessment": "Fairly Valued"
  },

  "metadata": {
    "calculation_date": "2026-01-10T01:19:28.693683",
    "quarters_analyzed": 8
  }
}
```

---

## Interpreting Results

### Forward EPS

- **Growth Method** works well for companies with consistent growth trends
- **Regression Method** is more conservative, smooths out volatility
- **R² value**: Higher = stronger trend (>0.7 = good, <0.3 = weak)
- **Recommended EPS**: Average of both methods provides balanced estimate

### Historical P/E

- Shows how market has valued the stock historically
- **Average vs Median**: Large difference indicates outliers
- **Std Dev**: Higher = more volatile P/E over time
- Use as reality check against fundamentals-based P/E

### Peer Comparison

- Only meaningful if peers are truly comparable (same industry, business model)
- Wide range suggests peer group is too diverse
- Compare individual peer P/Es to understand positioning

### Fundamentals P/E

- **Low P/E** (<15): Declining earnings, high risk, low margins
- **Medium P/E** (15-25): Stable business, moderate growth
- **High P/E** (>25): High growth, excellent margins, low risk

### Assessment

- **Undervalued**: Potential buy opportunity, verify fundamentals haven't deteriorated
- **Fairly Valued**: Current price reflects intrinsic value
- **Overvalued**: Potential sell/avoid, verify if growth justifies premium

---

## Data Requirements

- **Minimum 8 quarters** of financial data required
- **EPS data** must be available for all quarters
- **Revenue, margins, debt** used for fundamentals analysis
- **Stock prices** fetched automatically from yfinance for report dates

---

## Caching Behavior

### Valuation Cache
- **Duration:** 24 hours
- **Key:** Ticker + sorted peer list
- **Refresh:** Use POST to recalculate

### Stock Price Cache
- **Historical prices** (>30 days old): Never expire
- **Recent prices** (<30 days): Expire after 1 day
- Ensures historical P/E ratios remain consistent

---

## Error Handling

**404 - Not Found:**
- Ticker has insufficient data (<8 quarters)
- Ticker not found in database
- No cached valuation available (use POST)

**400 - Bad Request:**
- Invalid ticker format (must be 1-5 uppercase letters)
- Invalid peer ticker format

**500 - Internal Error:**
- API failure (Alpha Vantage, yfinance)
- Calculation error (division by zero, negative EPS issues)

---

## Configuration

Edit `backend/config.py` to customize:

```python
# Valuation Cache
VALUATION_CACHE_HOURS = 24

# Price Cache
PRICE_CACHE_DAYS_HISTORICAL = 999999  # Never expire
PRICE_CACHE_DAYS_RECENT = 1

# P/E Calculation
PE_BASE_MARKET = 15.0              # Market baseline P/E
PE_GROWTH_MULTIPLIER = 0.5         # Growth adjustment factor
MIN_QUARTERS_FOR_VALUATION = 8    # Minimum data required
```

---

## Use Cases

### 1. Quick Valuation Check
```bash
# Is AAPL trading at fair value?
curl -X POST http://localhost:8000/api/valuation/AAPL -d '{}'
```

### 2. Peer Group Analysis
```bash
# How does AAPL compare to tech peers?
curl -X POST http://localhost:8000/api/valuation/AAPL \
  -d '{"peers": ["MSFT", "GOOGL", "META", "NVDA"]}'
```

### 3. Sector Comparison
```bash
# Compare multiple stocks in same sector
for ticker in AAPL MSFT GOOGL; do
  curl -X POST http://localhost:8000/api/valuation/$ticker -d '{}'
done
```

### 4. Daily Price Monitoring
```bash
# Get cached valuation (fast, no API calls)
curl "http://localhost:8000/api/valuation/AAPL"
```

---

## Limitations

1. **P/E method only** - Not suitable for:
   - Unprofitable companies (negative EPS)
   - Cyclical industries (use P/B or P/S instead)
   - High-growth tech (may undervalue)

2. **Historical bias** - Past P/E ratios may not reflect future market conditions

3. **Peer selection** - Manual peer list requires domain knowledge

4. **Point-in-time** - Valuation reflects current data, not future changes

5. **No qualitative factors** - Doesn't consider management quality, competitive moats, etc.

---

## Tips for Best Results

1. **Choose comparable peers** - Same industry, similar size, business model
2. **Review fundamentals** - Check if metrics (growth, margins) make sense
3. **Consider context** - Low P/E might indicate problems, not opportunity
4. **Use ranges** - Don't rely on single point estimate
5. **Refresh regularly** - Recalculate after earnings reports
6. **Combine methods** - Use alongside DCF, asset-based valuation

---

## Technical Details

**Dependencies:**
- `yfinance>=0.2.50` - Stock price data
- `numpy>=2.0.0` - Statistical calculations

**Database Tables:**
- `stock_prices` - Historical OHLCV data
- `valuation_cache` - Cached valuation results

**API Rate Limits:**
- Alpha Vantage: 25 calls/day, 1.5s between requests
- yfinance: No official limit, uses public Yahoo Finance

---

## Support

For issues or questions:
- Check logs: `backend/logs/` (if logging enabled)
- Verify data: `GET /api/ticker/AAPL` to see available quarters
- Refresh data: `POST /api/ticker/AAPL/refresh` to update from API
- Review methodology: See `backend/services/valuation_service.py`
