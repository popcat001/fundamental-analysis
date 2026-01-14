"""
Valuation Service for P/E-based stock valuation

This service implements comprehensive P/E multiple valuation including:
- Forward EPS estimation (growth rate & regression methods)
- Historical P/E ratio analysis
- Peer comparison
- Fundamentals-based P/E calculation
- Justified P/E synthesis
- Fair value price calculation
"""
from sqlalchemy.orm import Session
from models import FinancialData, ValuationCache, Company
from services.data_service import DataService
from services.price_service import PriceService
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import numpy as np
import logging
from config import settings

logger = logging.getLogger(__name__)


class ValuationService:
    """Service for P/E-based stock valuation calculations"""

    def __init__(self, db: Session):
        self.db = db
        self.data_service = DataService(db)
        self.price_service = PriceService(db)

    def perform_valuation(self, symbol: str, peers: Optional[List[str]] = None) -> Dict:
        """
        Master method orchestrating complete valuation analysis

        Args:
            symbol: Stock ticker to value
            peers: Optional list of peer tickers for comparison

        Returns:
            Complete valuation report
        """
        symbol = symbol.upper()
        logger.info(f"Starting valuation for {symbol}" + (f" with peers: {peers}" if peers else ""))

        try:
            # Step 1: Get financial data
            financial_data = self.data_service.get_financial_data(symbol)
            if len(financial_data) < settings.MIN_QUARTERS_FOR_VALUATION:
                raise ValueError(f"Insufficient data: Need at least {settings.MIN_QUARTERS_FOR_VALUATION} quarters, found {len(financial_data)}")

            # Step 2: Get company info
            company = self.db.query(Company).filter(Company.ticker == symbol).first()
            company_name = company.company_name if company else symbol

            # Step 3: Calculate forward EPS (both methods)
            forward_eps_growth = self.calculate_forward_eps_growth(financial_data)
            forward_eps_regression = self.calculate_forward_eps_regression(financial_data)

            # Use average of both methods as recommended
            forward_eps_recommended = (forward_eps_growth['forward_eps'] + forward_eps_regression['forward_eps']) / 2

            # Step 4: Calculate current metrics
            current_price = self.price_service.get_current_price(symbol)
            if not current_price:
                raise ValueError(f"Could not get current price for {symbol}")

            # Calculate TTM EPS from last 4 quarters
            recent_quarters = sorted(financial_data, key=lambda x: x['fiscal_date'], reverse=True)[:4]
            ttm_eps = sum(q['eps'] for q in recent_quarters)
            current_pe = current_price / ttm_eps if ttm_eps > 0 else None

            # Step 5: Calculate historical P/E ratios
            historical_pe = self.calculate_historical_pe_ratios(symbol, financial_data)

            # Step 6: Calculate peer P/E ratios (if peers provided)
            peer_comparison = None
            if peers:
                peer_comparison = self.calculate_peer_pe_ratios(peers)

            # Step 7: Calculate fundamentals-based P/E
            fundamentals_analysis = self.calculate_fundamentals_pe(symbol, financial_data)

            # Step 8: Synthesize justified P/E range
            justified_pe = self.calculate_justified_pe(
                historical_pe['average'] if historical_pe else None,
                peer_comparison['average_pe'] if peer_comparison else None,
                fundamentals_analysis['fundamentals_pe']
            )

            # Step 9: Calculate fair value price range
            fair_value = self.calculate_fair_value_price(
                forward_eps_recommended,
                justified_pe['justified_pe_low'],
                justified_pe['justified_pe_high'],
                current_price
            )

            # Step 10: Build comprehensive report
            report = {
                'symbol': symbol,
                'company_name': company_name,
                'valuation_date': datetime.now(timezone.utc).isoformat(),

                'current_metrics': {
                    'current_price': round(current_price, 2),
                    'ttm_eps': round(ttm_eps, 2),
                    'current_pe': round(current_pe, 2) if current_pe else None
                },

                'forward_eps': {
                    'growth_method': forward_eps_growth,
                    'regression_method': forward_eps_regression,
                    'recommended': round(forward_eps_recommended, 2)
                },

                'historical_pe': historical_pe,
                'peer_comparison': peer_comparison,
                'fundamentals_analysis': fundamentals_analysis,
                'justified_pe': justified_pe,
                'fair_value': fair_value,

                'metadata': {
                    'calculation_date': datetime.now(timezone.utc).isoformat(),
                    'quarters_analyzed': len(financial_data)
                }
            }

            # Step 11: Cache the results
            self._cache_valuation(symbol, peers, report)

            logger.info(f"Valuation complete for {symbol}: Fair value ${fair_value['fair_value_low']}-${fair_value['fair_value_high']}")
            return report

        except Exception as e:
            logger.error(f"Valuation failed for {symbol}: {str(e)}", exc_info=True)
            raise

    def calculate_forward_eps_growth(self, financial_data: List[Dict]) -> Dict:
        """
        Calculate forward EPS using historical average growth rate

        Args:
            financial_data: List of quarterly financial data

        Returns:
            Dict with forward_eps, growth_rate, quarterly_estimates
        """
        # Sort by fiscal date to ensure chronological order
        sorted_data = sorted(financial_data, key=lambda x: x['fiscal_date'])

        # Extract EPS values
        eps_values = [q['eps'] for q in sorted_data if q['eps'] and q['eps'] > 0]

        if len(eps_values) < 4:
            raise ValueError("Need at least 4 quarters of positive EPS for growth calculation")

        # Calculate quarter-over-quarter growth rates
        growth_rates = []
        for i in range(1, len(eps_values)):
            if eps_values[i-1] > 0:
                growth = (eps_values[i] / eps_values[i-1]) - 1
                growth_rates.append(growth)

        # Average growth rate
        avg_growth = np.mean(growth_rates) if growth_rates else 0

        # Project forward 4 quarters
        latest_eps = eps_values[-1]
        quarterly_estimates = []
        for i in range(1, 5):
            estimate = latest_eps * ((1 + avg_growth) ** i)
            quarterly_estimates.append(round(estimate, 2))

        forward_eps = sum(quarterly_estimates)

        # Include historical EPS for visualization
        historical_eps = []
        for i, q in enumerate(sorted_data):
            if q['eps'] and q['eps'] > 0:
                historical_eps.append({
                    'quarter': q['quarter'],
                    'fiscal_date': q['fiscal_date'],
                    'eps': round(q['eps'], 2)
                })

        return {
            'forward_eps': round(forward_eps, 2),
            'growth_rate': round(avg_growth, 4),
            'quarterly_estimates': quarterly_estimates,
            'historical_eps': historical_eps
        }

    def calculate_forward_eps_regression(self, financial_data: List[Dict]) -> Dict:
        """
        Calculate forward EPS using linear regression on historical EPS

        Args:
            financial_data: List of quarterly financial data

        Returns:
            Dict with:
                - forward_eps: Sum of next 4 quarterly estimates
                - slope: Regression line slope coefficient
                - intercept: Regression line y-intercept
                - r_squared: Goodness of fit metric (0-1)
                - quarterly_estimates: List of next 4 quarter estimates
                - historical_eps: Historical data with regression fit values
        """
        # Sort by fiscal date
        sorted_data = sorted(financial_data, key=lambda x: x['fiscal_date'])

        # Extract EPS values
        eps_values = [q['eps'] for q in sorted_data if q['eps'] and q['eps'] > 0]

        if len(eps_values) < 4:
            raise ValueError("Need at least 4 quarters of positive EPS for regression")

        # Create x values (quarter numbers: 0, 1, 2, ...)
        x = np.array(range(len(eps_values)))
        y = np.array(eps_values)

        # Fit linear regression: y = slope * x + intercept
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]
        intercept = coeffs[1]

        # Calculate R-squared
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # Predict next 4 quarters
        n = len(eps_values)
        quarterly_estimates = []
        for i in range(1, 5):
            estimate = slope * (n + i - 1) + intercept
            quarterly_estimates.append(round(max(estimate, 0), 2))  # Don't allow negative

        forward_eps = sum(quarterly_estimates)

        # Include historical EPS for visualization
        historical_eps = []
        for i, q in enumerate(sorted_data):
            if q['eps'] and q['eps'] > 0:
                historical_eps.append({
                    'quarter': q['quarter'],
                    'fiscal_date': q['fiscal_date'],
                    'eps': round(q['eps'], 2),
                    'regression_fit': round(slope * i + intercept, 2)
                })

        return {
            'forward_eps': round(forward_eps, 2),
            'slope': round(slope, 4),
            'intercept': round(intercept, 4),
            'r_squared': round(r_squared, 4),
            'quarterly_estimates': quarterly_estimates,
            'historical_eps': historical_eps
        }

    def calculate_historical_pe_ratios(self, symbol: str, financial_data: List[Dict]) -> Optional[Dict]:
        """
        Calculate P/E ratios at each earnings report date

        Args:
            symbol: Stock ticker
            financial_data: List of quarterly financial data

        Returns:
            Dict with pe_ratios list and statistics, or None if insufficient data
        """
        # Sort by fiscal date
        sorted_data = sorted(financial_data, key=lambda x: x['fiscal_date'])

        pe_ratios = []

        for i in range(settings.TTM_QUARTERS - 1, len(sorted_data)):  # Need at least TTM_QUARTERS for TTM
            quarter = sorted_data[i]
            reported_date = quarter.get('reported_date')

            if not reported_date:
                logger.warning(f"Missing reported_date for {symbol} {quarter['quarter']}")
                continue

            # Calculate TTM EPS (sum of last 4 quarters including current)
            ttm_eps = sum(sorted_data[j]['eps'] for j in range(i-3, i+1) if sorted_data[j]['eps'])

            if ttm_eps <= 0:
                continue  # Skip if TTM EPS is negative or zero

            # Get stock price at reported date
            price = self.price_service.get_price_at_date(symbol, reported_date)

            if not price:
                logger.warning(f"Could not get price for {symbol} on {reported_date}")
                continue

            # Calculate P/E ratio
            pe_ratio = price / ttm_eps

            pe_ratios.append({
                'quarter': quarter['quarter'],
                'fiscal_date': quarter['fiscal_date'],
                'reported_date': reported_date,
                'eps': round(quarter['eps'], 2),
                'ttm_eps': round(ttm_eps, 2),
                'price': round(price, 2),
                'pe_ratio': round(pe_ratio, 2)
            })

        if not pe_ratios:
            logger.warning(f"No historical P/E ratios calculated for {symbol}")
            return None

        # Calculate statistics
        pe_values = [p['pe_ratio'] for p in pe_ratios]

        return {
            'pe_ratios': pe_ratios,
            'average': round(np.mean(pe_values), 2),
            'median': round(np.median(pe_values), 2),
            'min': round(min(pe_values), 2),
            'max': round(max(pe_values), 2),
            'std_dev': round(np.std(pe_values), 2)
        }

    def calculate_peer_pe_ratios(self, peers: List[str]) -> Optional[Dict]:
        """
        Calculate current P/E ratios for peer companies

        Args:
            peers: List of ticker symbols

        Returns:
            Dict with peer_pe_ratios list and statistics
        """
        if not peers:
            return None

        peer_results = []

        for peer_ticker in peers:
            try:
                peer_ticker = peer_ticker.upper()
                logger.info(f"Calculating P/E for peer {peer_ticker}")

                # Get financial data for peer
                peer_data = self.data_service.get_financial_data(peer_ticker)

                if len(peer_data) < 4:
                    logger.warning(f"Insufficient data for peer {peer_ticker}")
                    continue

                # Calculate TTM EPS from last 4 quarters
                recent_quarters = sorted(peer_data, key=lambda x: x['fiscal_date'], reverse=True)[:4]
                ttm_eps = sum(q['eps'] for q in recent_quarters if q['eps'])

                if ttm_eps <= 0:
                    logger.warning(f"Negative or zero TTM EPS for peer {peer_ticker}")
                    continue

                # Get current price
                current_price = self.price_service.get_current_price(peer_ticker)

                if not current_price:
                    logger.warning(f"Could not get price for peer {peer_ticker}")
                    continue

                # Calculate P/E
                pe_ratio = current_price / ttm_eps

                peer_results.append({
                    'ticker': peer_ticker,
                    'pe': round(pe_ratio, 2),
                    'ttm_eps': round(ttm_eps, 2),
                    'price': round(current_price, 2)
                })

            except Exception as e:
                logger.warning(f"Error calculating P/E for peer {peer_ticker}: {str(e)}")
                continue

        if not peer_results:
            logger.warning("No valid peer P/E ratios calculated")
            return None

        # Calculate statistics
        pe_values = [p['pe'] for p in peer_results]

        return {
            'peer_pe_ratios': peer_results,
            'average_pe': round(np.mean(pe_values), 2),
            'median_pe': round(np.median(pe_values), 2),
            'range': [round(min(pe_values), 2), round(max(pe_values), 2)]
        }

    def calculate_fundamentals_pe(self, symbol: str, financial_data: List[Dict]) -> Dict:
        """
        Calculate justified P/E based on fundamental metrics

        Args:
            symbol: Stock ticker
            financial_data: Historical financial data

        Returns:
            Dict with fundamentals_pe, components, and metrics
        """
        # Sort by fiscal date
        sorted_data = sorted(financial_data, key=lambda x: x['fiscal_date'])

        # Calculate EPS growth rate (CAGR over available quarters)
        eps_values = [q['eps'] for q in sorted_data if q['eps'] and q['eps'] > 0]
        if len(eps_values) >= 4:
            quarters = len(eps_values) - 1
            years = quarters / 4
            eps_cagr = ((eps_values[-1] / eps_values[0]) ** (1 / years)) - 1 if years > 0 else 0
        else:
            eps_cagr = 0

        # Calculate revenue growth rate
        revenue_values = [(q.get('revenue') or 0) for q in sorted_data if (q.get('revenue') or 0) > 0]
        if len(revenue_values) >= 4:
            quarters = len(revenue_values) - 1
            years = quarters / 4
            revenue_cagr = ((revenue_values[-1] / revenue_values[0]) ** (1 / years)) - 1 if years > 0 else 0
        else:
            revenue_cagr = 0

        # Calculate average net margin from last 4 quarters
        recent_quarters = sorted_data[-4:]
        net_margins = [q['net_margin'] for q in recent_quarters if q.get('net_margin')]
        avg_net_margin = np.mean(net_margins) if net_margins else 0

        # Check if margins are improving
        if len(net_margins) >= 4:
            margin_trend = "improving" if net_margins[-1] > net_margins[0] else "declining"
        else:
            margin_trend = "stable"

        # Calculate debt to equity (approximation)
        # Using latest quarter's data
        latest = sorted_data[-1]
        total_debt = latest.get('debt', 0)
        cash = latest.get('cash', 0)
        # Rough equity estimate: net_income * 20 (simplified)
        equity_estimate = latest.get('net_income', 0) * 20 if latest.get('net_income', 0) > 0 else 1
        debt_to_equity = total_debt / equity_estimate if equity_estimate > 0 else 0

        # Build fundamentals P/E
        base_pe = settings.PE_BASE_MARKET  # Default 15

        # Growth adjustment: add 0.5 * growth_rate for each 1% growth
        avg_growth = (eps_cagr + revenue_cagr) / 2
        growth_adjustment = settings.PE_GROWTH_MULTIPLIER * avg_growth * 100

        # Margin adjustment
        margin_adjustment = 0
        if avg_net_margin > settings.EXCELLENT_NET_MARGIN_THRESHOLD:
            margin_adjustment += settings.MARGIN_EXCELLENT_ADJUSTMENT
        if margin_trend == "improving":
            margin_adjustment += settings.MARGIN_IMPROVING_ADJUSTMENT

        # Risk adjustment
        risk_adjustment = 0
        if debt_to_equity > settings.HIGH_DEBT_TO_EQUITY_THRESHOLD:
            risk_adjustment += settings.DEBT_RISK_ADJUSTMENT
        if margin_trend == "declining":
            risk_adjustment += settings.DECLINING_MARGIN_ADJUSTMENT

        fundamentals_pe = base_pe + growth_adjustment + margin_adjustment + risk_adjustment

        # Include quarterly metrics for visualization
        quarterly_metrics = []
        for q in sorted_data:
            quarterly_metrics.append({
                'quarter': q['quarter'],
                'fiscal_date': q['fiscal_date'],
                'eps': round(q['eps'], 2) if q['eps'] else None,
                'revenue': round(q.get('revenue', 0) / 1e6, 2) if q.get('revenue') else None,  # in millions
                'net_margin': round(q.get('net_margin', 0) * 100, 2) if q.get('net_margin') is not None else None,  # as percentage
                'gross_margin': round(q.get('gross_margin', 0) * 100, 2) if q.get('gross_margin') is not None else None  # as percentage
            })

        return {
            'fundamentals_pe': round(max(fundamentals_pe, 5), 2),  # Floor at 5
            'components': {
                'base_pe': base_pe,
                'growth_adjustment': round(growth_adjustment, 2),
                'margin_adjustment': margin_adjustment,
                'risk_adjustment': risk_adjustment
            },
            'metrics': {
                'eps_growth_rate': round(eps_cagr, 4),
                'revenue_growth_rate': round(revenue_cagr, 4),
                'avg_net_margin': round(avg_net_margin, 4),
                'margin_trend': margin_trend,
                'debt_to_equity': round(debt_to_equity, 2)
            },
            'quarterly_metrics': quarterly_metrics
        }

    def calculate_justified_pe(self, historical_pe_avg: Optional[float],
                                peer_pe_avg: Optional[float],
                                fundamentals_pe: float) -> Dict:
        """
        Synthesize all P/E calculation methods into justified P/E range

        Args:
            historical_pe_avg: Company's historical average P/E
            peer_pe_avg: Peer group average P/E
            fundamentals_pe: Fundamentals-based justified P/E

        Returns:
            Dict with justified_pe_low, high, midpoint, weighting
        """
        # Determine weights based on available data
        pe_values = []
        weights = []

        if historical_pe_avg and historical_pe_avg > 0:
            pe_values.append(historical_pe_avg)
            weights.append(settings.PE_WEIGHT_HISTORICAL)

        if peer_pe_avg and peer_pe_avg > 0:
            pe_values.append(peer_pe_avg)
            weights.append(settings.PE_WEIGHT_PEER)

        if fundamentals_pe and fundamentals_pe > 0:
            pe_values.append(fundamentals_pe)
            weights.append(settings.PE_WEIGHT_FUNDAMENTALS)

        # Normalize weights if some data is missing
        if sum(weights) > 0:
            weights = [w / sum(weights) for w in weights]

        # Calculate weighted average
        midpoint = sum(p * w for p, w in zip(pe_values, weights))

        # Calculate range (±10% of midpoint or use std dev if multiple values)
        if len(pe_values) > 1:
            std_dev = np.std(pe_values)
            range_width = max(midpoint * 0.1, std_dev)
        else:
            range_width = midpoint * 0.1

        justified_pe_low = max(midpoint - range_width, 5)  # Floor at 5
        justified_pe_high = midpoint + range_width

        weighting_info = {}
        if historical_pe_avg:
            weighting_info['historical'] = weights[0] if len(weights) > 0 else 0
        if peer_pe_avg:
            idx = 1 if historical_pe_avg else 0
            weighting_info['peer'] = weights[idx] if len(weights) > idx else 0
        if fundamentals_pe:
            idx = sum([historical_pe_avg is not None, peer_pe_avg is not None])
            weighting_info['fundamentals'] = weights[idx] if len(weights) > idx else 0

        return {
            'justified_pe_low': round(justified_pe_low, 2),
            'justified_pe_high': round(justified_pe_high, 2),
            'justified_pe_midpoint': round(midpoint, 2),
            'weighting': weighting_info
        }

    def calculate_fair_value_price(self, forward_eps: float,
                                     justified_pe_low: float,
                                     justified_pe_high: float,
                                     current_price: float) -> Dict:
        """
        Calculate implied fair value price range

        Args:
            forward_eps: Estimated forward 12-month EPS
            justified_pe_low: Lower bound of justified P/E
            justified_pe_high: Upper bound of justified P/E
            current_price: Current stock price

        Returns:
            Dict with fair value range and assessment
        """
        # Calculate fair value range
        fair_value_low = forward_eps * justified_pe_low
        fair_value_high = forward_eps * justified_pe_high
        fair_value_midpoint = (fair_value_low + fair_value_high) / 2

        # Determine valuation assessment
        if current_price < fair_value_low:
            assessment = "Undervalued"
            upside_percent = ((fair_value_low - current_price) / current_price) * 100
        elif current_price > fair_value_high:
            assessment = "Overvalued"
            upside_percent = ((fair_value_high - current_price) / current_price) * 100
        else:
            assessment = "Fairly Valued"
            upside_percent = ((fair_value_midpoint - current_price) / current_price) * 100

        return {
            'fair_value_low': round(fair_value_low, 2),
            'fair_value_high': round(fair_value_high, 2),
            'fair_value_midpoint': round(fair_value_midpoint, 2),
            'current_price': round(current_price, 2),
            'upside_percent': round(upside_percent, 2),
            'assessment': assessment
        }

    def _cache_valuation(self, symbol: str, peers: Optional[List[str]], report: Dict):
        """
        Cache valuation results in database

        Args:
            symbol: Stock ticker
            peers: List of peer tickers (or None)
            report: Complete valuation report
        """
        try:
            # Format peers as comma-separated string (sorted for consistent cache key)
            peer_str = ','.join(sorted(peers)) if peers else ''

            # Check if cache entry exists
            existing = self.db.query(ValuationCache).filter(
                ValuationCache.ticker == symbol,
                ValuationCache.peers == peer_str
            ).first()

            # Extract values from report
            forward_eps = report['forward_eps']
            justified_pe = report['justified_pe']
            fair_value = report['fair_value']
            historical_pe = report.get('historical_pe')
            peer_comparison = report.get('peer_comparison')
            fundamentals = report['fundamentals_analysis']

            # Set expiration (24 hours from now) - store as naive UTC in database
            now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
            expires_at = now_utc + timedelta(hours=settings.VALUATION_CACHE_HOURS)

            if existing:
                # Update existing cache
                existing.forward_eps_growth = forward_eps['growth_method']['forward_eps']
                existing.forward_eps_regression = forward_eps['regression_method']['forward_eps']
                existing.historical_pe_avg = historical_pe['average'] if historical_pe else None
                existing.historical_pe_median = historical_pe['median'] if historical_pe else None
                existing.peer_pe_avg = peer_comparison['average_pe'] if peer_comparison else None
                existing.fundamentals_pe = fundamentals['fundamentals_pe']
                existing.justified_pe_low = justified_pe['justified_pe_low']
                existing.justified_pe_high = justified_pe['justified_pe_high']
                existing.fair_value_low = fair_value['fair_value_low']
                existing.fair_value_high = fair_value['fair_value_high']
                existing.valuation_data = report  # Store full report for visualization
                existing.calculated_at = now_utc
                existing.expires_at = expires_at
            else:
                # Create new cache entry
                cache_entry = ValuationCache(
                    ticker=symbol,
                    peers=peer_str,
                    forward_eps_growth=forward_eps['growth_method']['forward_eps'],
                    forward_eps_regression=forward_eps['regression_method']['forward_eps'],
                    historical_pe_avg=historical_pe['average'] if historical_pe else None,
                    historical_pe_median=historical_pe['median'] if historical_pe else None,
                    peer_pe_avg=peer_comparison['average_pe'] if peer_comparison else None,
                    fundamentals_pe=fundamentals['fundamentals_pe'],
                    justified_pe_low=justified_pe['justified_pe_low'],
                    justified_pe_high=justified_pe['justified_pe_high'],
                    fair_value_low=fair_value['fair_value_low'],
                    fair_value_high=fair_value['fair_value_high'],
                    valuation_data=report,  # Store full report for visualization
                    calculated_at=now_utc,
                    expires_at=expires_at
                )
                self.db.add(cache_entry)

            self.db.commit()
            logger.info(f"Cached valuation for {symbol}")

        except Exception as e:
            logger.error(f"Error caching valuation for {symbol}: {str(e)}")
            self.db.rollback()
