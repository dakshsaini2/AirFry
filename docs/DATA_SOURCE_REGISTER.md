# APIx Data Source Register

As per the MoSPI strict provenance rules, all data sources utilized in APIx are registered here.

## Active Primary Sources (Web Scraping Engine)

### 1. Airline Direct Portals
- **Target**: `https://www.goindigo.in/` (and other major domestic airlines)
- **Method**: Headless `Playwright` Chromium instances simulating user navigation.
- **Data Extracted**: Real-time forward-looking (T+1 to T+45) base fares, taxes, and zero-convenience-fee prices.
- **Status**: ACTIVE

### 2. Online Travel Agencies (OTAs)
- **Target**: `https://www.makemytrip.com/` (and other OTAs via deep links)
- **Method**: Headless `Playwright` Chromium instances accessing direct deep-linked itinerary routes.
- **Data Extracted**: Cross-carrier inventory, OTA convenience fees, and relative pricing variations.
- **Status**: ACTIVE

## Discontinued / Retired Sources

### Duffel API
- **Reason**: The MoSPI Problem Statement (26056) explicitly requested an "ethically-designed multi-source web-scraping engine using Python (Scrapy/Selenium/Playwright)". The use of commercial B2B aggregators (like Duffel/Amadeus) violates the core directive of building an internal web-scraping tool. 
- **Status**: RETIRED AND PURGED in Phase 14.

## Historical Baselines

### DGCA Monthly Average Fares
- **Format**: CSV Snapshot
- **Dataset Version**: `DGCA-2026-v1`
- **Purpose**: Used strictly for Phase 15 empirical backtesting alignment and structural Pearson/MAPE validation. Cannot be used directly to construct the live index.
- **Status**: ACTIVE (Reference Only)
