import React, { useState } from 'react';
import './ValuationAnalysis.css';

function ValuationAnalysis({ symbol, valuation, onCalculate, loading }) {
  const [peerInput, setPeerInput] = useState('');

  if (!valuation) {
    return (
      <div className="valuation-container">
        <h3>Valuation Analysis</h3>
        <div className="valuation-prompt">
          <p>Calculate P/E multiple-based valuation for {symbol}</p>
          <div className="peer-input-section">
            <label htmlFor="peers">
              Peer Tickers (optional, comma-separated):
            </label>
            <input
              id="peers"
              type="text"
              placeholder="e.g., MSFT, GOOGL, META"
              value={peerInput}
              onChange={(e) => setPeerInput(e.target.value)}
              className="peer-input"
            />
            <small>Leave blank for valuation without peer comparison</small>
          </div>
          <button
            onClick={() => {
              const peers = peerInput
                .split(',')
                .map(p => p.trim().toUpperCase())
                .filter(p => p.length > 0);
              onCalculate(peers.length > 0 ? peers : null);
            }}
            disabled={loading}
            className="calculate-button"
          >
            {loading ? 'Calculating...' : 'Calculate Valuation'}
          </button>
        </div>
      </div>
    );
  }

  const formatCurrency = (num) => {
    if (num === null || num === undefined) return 'N/A';
    return '$' + num.toFixed(2);
  };

  const formatPercent = (num) => {
    if (num === null || num === undefined) return 'N/A';
    return (num * 100).toFixed(2) + '%';
  };

  const getAssessmentClass = (assessment) => {
    if (assessment === 'Undervalued') return 'assessment-undervalued';
    if (assessment === 'Overvalued') return 'assessment-overvalued';
    return 'assessment-fair';
  };

  return (
    <div className="valuation-container">
      <div className="valuation-header">
        <h3>Valuation Analysis</h3>
        <button
          onClick={() => {
            const peers = peerInput
              .split(',')
              .map(p => p.trim().toUpperCase())
              .filter(p => p.length > 0);
            onCalculate(peers.length > 0 ? peers : null);
          }}
          disabled={loading}
          className="recalculate-button"
        >
          Recalculate
        </button>
      </div>

      {valuation.cached && (
        <div className="cache-notice">
          Cached result from {new Date(valuation.calculated_at || valuation.valuation_date).toLocaleString()}
        </div>
      )}

      {/* Current Metrics Summary */}
      <div className="current-summary">
        <div className="summary-item">
          <span className="summary-label">Current Price:</span>
          <span className="summary-value">{formatCurrency(valuation.current_metrics?.current_price || valuation.fair_value?.current_price)}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">TTM EPS:</span>
          <span className="summary-value">{formatCurrency(valuation.current_metrics?.ttm_eps)}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Current P/E:</span>
          <span className="summary-value">{valuation.current_metrics?.current_pe?.toFixed(2) || 'N/A'}</span>
        </div>
      </div>

      {/* Step-by-Step Valuation Report */}
      <div className="valuation-steps">

        {/* Step 1: Forward EPS */}
        <div className="valuation-step">
          <h4><span className="step-number">1.</span> Forward EPS Calculation (Dual Methods)</h4>
          <ul className="step-list">
            <li>
              <strong>Growth method:</strong> {formatCurrency(valuation.forward_eps?.growth_method?.forward_eps || valuation.forward_eps?.growth_method)}
              {valuation.forward_eps?.growth_method?.growth_rate && (
                <span> ({formatPercent(valuation.forward_eps.growth_method.growth_rate)} QoQ growth)</span>
              )}
            </li>
            <li>
              <strong>Regression method:</strong> {formatCurrency(valuation.forward_eps?.regression_method?.forward_eps || valuation.forward_eps?.regression_method)}
              {valuation.forward_eps?.regression_method?.r_squared !== undefined && (
                <span> ({valuation.forward_eps.regression_method.r_squared === 0 ? 'flat trend' : 'trend'}, R²={valuation.forward_eps.regression_method.r_squared.toFixed(2)})</span>
              )}
            </li>
            <li className="highlight-item">
              <strong>Recommended:</strong> {formatCurrency(valuation.forward_eps?.recommended)} (average)
            </li>
          </ul>
        </div>

        {/* Step 2: Historical P/E */}
        <div className="valuation-step">
          <h4><span className="step-number">2.</span> Historical P/E Analysis ({valuation.historical_pe?.pe_ratios?.length || 5} quarters)</h4>
          <ul className="step-list">
            <li><strong>Average:</strong> {valuation.historical_pe?.average?.toFixed(2) || 'N/A'}</li>
            <li><strong>Median:</strong> {valuation.historical_pe?.median?.toFixed(2) || 'N/A'}</li>
            <li><strong>Range:</strong> {valuation.historical_pe?.min?.toFixed(2)} - {valuation.historical_pe?.max?.toFixed(2)}</li>
          </ul>
        </div>

        {/* Step 3: Peer Comparison */}
        {(valuation.peer_comparison?.peer_pe_ratios || valuation.peer_comparison?.peers) && (
          <div className="valuation-step">
            <h4>
              <span className="step-number">3.</span> Peer Comparison (
              {valuation.peer_comparison.peer_pe_ratios?.map(p => p.ticker).join(', ') ||
               valuation.peer_comparison.peers?.join(', ')}
              )
            </h4>
            <ul className="step-list">
              {valuation.peer_comparison.peer_pe_ratios?.map((peer) => (
                <li key={peer.ticker}>
                  <strong>{peer.ticker} P/E:</strong> {peer.pe.toFixed(2)}
                </li>
              ))}
              <li className="highlight-item">
                <strong>Average peer P/E:</strong> {valuation.peer_comparison?.average_pe?.toFixed(2) || 'N/A'}
              </li>
            </ul>
          </div>
        )}

        {/* Step 4: Fundamentals */}
        <div className="valuation-step">
          <h4><span className="step-number">{valuation.peer_comparison?.peer_pe_ratios ? '4' : '3'}.</span> Fundamentals-Based P/E</h4>
          <ul className="step-list">
            <li className="highlight-item">
              <strong>Fundamentals P/E:</strong> {valuation.fundamentals_analysis?.fundamentals_pe?.toFixed(2) || valuation.fundamentals_pe?.toFixed(2) || 'N/A'}
            </li>
            {valuation.fundamentals_analysis?.components && (
              <>
                <li><strong>Base:</strong> {valuation.fundamentals_analysis.components.base_pe?.toFixed(1)}</li>
                <li>
                  <strong>Growth adjustment:</strong> {valuation.fundamentals_analysis.components.growth_adjustment?.toFixed(2)}
                  {valuation.fundamentals_analysis.metrics?.eps_growth_rate &&
                   valuation.fundamentals_analysis.metrics.eps_growth_rate < 0 && ' (negative growth)'}
                </li>
                <li>
                  <strong>Margin adjustment:</strong> +{valuation.fundamentals_analysis.components.margin_adjustment}
                  {valuation.fundamentals_analysis.metrics?.avg_net_margin &&
                   ` (${(valuation.fundamentals_analysis.metrics.avg_net_margin * 100).toFixed(0)}% margins)`}
                </li>
                <li>
                  <strong>Risk adjustment:</strong> {valuation.fundamentals_analysis.components.risk_adjustment}
                  {valuation.fundamentals_analysis.metrics?.margin_trend === 'declining' && ' (declining margins)'}
                </li>
              </>
            )}
          </ul>
        </div>

        {/* Step 5: Justified P/E */}
        <div className="valuation-step">
          <h4><span className="step-number">{valuation.peer_comparison?.peer_pe_ratios ? '5' : '4'}.</span> Justified P/E Synthesis</h4>
          <ul className="step-list">
            <li><strong>Range:</strong> {valuation.justified_pe?.justified_pe_low?.toFixed(2) || valuation.justified_pe?.low?.toFixed(2)} - {valuation.justified_pe?.justified_pe_high?.toFixed(2) || valuation.justified_pe?.high?.toFixed(2)}</li>
            <li className="highlight-item">
              <strong>Midpoint:</strong> {valuation.justified_pe?.justified_pe_midpoint?.toFixed(2) || valuation.justified_pe?.midpoint?.toFixed(2)}
            </li>
            {valuation.justified_pe?.weighting && (
              <li>
                <strong>Weighting:</strong> {(valuation.justified_pe.weighting.historical * 100).toFixed(0)}% historical
                {valuation.justified_pe.weighting.peer && `, ${(valuation.justified_pe.weighting.peer * 100).toFixed(0)}% peer`}
                , {(valuation.justified_pe.weighting.fundamentals * 100).toFixed(0)}% fundamentals
              </li>
            )}
          </ul>
        </div>

        {/* Step 6: Fair Value */}
        <div className="valuation-step final-step">
          <h4><span className="step-number">{valuation.peer_comparison?.peer_pe_ratios ? '6' : '5'}.</span> Fair Value Calculation</h4>
          <ul className="step-list">
            <li><strong>Fair value range:</strong> {formatCurrency(valuation.fair_value?.fair_value_low || valuation.fair_value?.low)} - {formatCurrency(valuation.fair_value?.fair_value_high || valuation.fair_value?.high)}</li>
            <li className="highlight-item">
              <strong>Midpoint:</strong> {formatCurrency(valuation.fair_value?.fair_value_midpoint || valuation.fair_value?.midpoint)}
            </li>
            <li><strong>Current price:</strong> {formatCurrency(valuation.fair_value?.current_price)}</li>
            <li>
              <strong>Upside:</strong>
              <span className={valuation.fair_value?.upside_percent >= 0 ? 'positive-upside' : 'negative-upside'}>
                {' '}{valuation.fair_value?.upside_percent?.toFixed(2)}%
              </span>
            </li>
            <li className="assessment-item">
              <strong>Assessment:</strong>
              <span className={`assessment-badge ${getAssessmentClass(valuation.fair_value?.assessment)}`}>
                {valuation.fair_value?.assessment || 'N/A'}
              </span>
            </li>
          </ul>
        </div>

      </div>

      {/* Peer Input for Recalculation */}
      <div className="peer-recalc-section">
        <label htmlFor="peers-recalc">Update Peer Tickers:</label>
        <input
          id="peers-recalc"
          type="text"
          placeholder="e.g., MSFT, GOOGL, META"
          value={peerInput}
          onChange={(e) => setPeerInput(e.target.value)}
          className="peer-input"
        />
      </div>
    </div>
  );
}

export default ValuationAnalysis;
