# APIx Methodology

This document outlines the methodological framework for calculating the APIx Real-time Airfare Price Index.

## 1. Route Weights
The index tracks the top 10 highest-volume domestic routes in India. Each route is weighted by its trailing 12-month passenger traffic share as reported by the Directorate General of Civil Aviation (DGCA). Base weights range from ~20% (DEL-BOM) to ~6% (BOM-GOI).

## 2. Carrier Weights
Carrier weights are implicitly managed by the scrape volume, which maps to actual market share (e.g., IndiGo ~60%, Air India Group ~25%). A carrier multiplier is structurally applied to align base prices across low-cost carriers (LCCs) and full-service carriers (FSCs).

## 3. Lead-time Distribution
Prices are scraped equally across T+1, T+7, T+15, T+30, and T+45 day forward-looking windows. This captures both immediate dynamic pricing volatility and long-term base pricing elasticity.

## 4. Jevons Index Formula
The core index calculation relies on the Jevons Geometric Mean of price relatives:
`Index = Product( P_t / P_0 ) ^ (1/n)`

It aggregates logarithmic price changes. The geometric mean satisfies the time-reversal and circularity tests, making it robust against dynamic pricing spikes typical in the airline industry.

## 5. Base Period
The base period is defined as the first 7 days of observation (Index = 100). All subsequent index values are geometric relatives to this baseline.

## 6. Outlier Treatment
Median Absolute Deviation (MAD) is used to reject values where:
`(0.6745 * |log_fare - median_log|) / MAD > 3.5`
This prevents single erroneous API spikes or scraping anomalies from distorting the macroeconomic index.

## 7. Missing and Sold-out Data Treatment
- **Missing Data (e.g., Taxes)**: Missing tax components are imputed using the route+lead median.
- **Sold-out Flights**: Sold-out flights are actively dropped prior to the geometric mean calculation to prevent infinity errors in logarithmic aggregation.

## 8. Data Limitations
- **Asking Fares vs Transaction Fares**: APIx measures real-time asking fares (posted prices), while DGCA historical data is based on realized transaction fares, which factor in last-minute deals or bulk corporate discounts.
- **Tax & Fee Differences**: Convenience fees vary wildly between Direct Airlines and OTAs.
- **Dynamic Pricing Volatility**: Brief scraping outages can slightly shift the Jevons geometric mean if major routes are temporarily dropped due to bot-mitigation limits.
