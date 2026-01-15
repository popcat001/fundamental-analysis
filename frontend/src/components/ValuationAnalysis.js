import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import './ValuationAnalysis.css';
import ValuationCharts from './ValuationCharts';

// Parse peers.md content into defaultPeers object
function parsePeersMd(content) {
  const peers = {};
  const lines = content.split('\n').filter(line => line.trim());

  for (const line of lines) {
    // Format: "TICKER    PEER1, PEER2, PEER3"
    const match = line.match(/^(\w+)\s{2,}(.+)$/);
    if (match) {
      const ticker = match[1].trim().toUpperCase();
      const peerList = match[2].trim();

      // Validate peer list format (letters, commas, spaces only)
      if (peerList && /^[A-Z,\s]+$/i.test(peerList)) {
        peers[ticker] = peerList;
      } else {
        console.warn(`Invalid peer list format for ${ticker}: ${peerList}`);
      }
    }
  }

  return peers;
}

// Parse peer input string into array or null
function parsePeersInput(peerInput) {
  if (!peerInput) return null;

  const peers = peerInput
    .split(',')
    .map(p => p.trim().toUpperCase())
    .filter(p => p.length > 0);

  return peers.length > 0 ? peers : null;
}

function ValuationAnalysis({ symbol, valuation, onCalculate, loading }) {
  const [peerInput, setPeerInput] = useState('');
  const [defaultPeers, setDefaultPeers] = useState({});
  const [peersLoading, setPeersLoading] = useState(true);
  const [peersError, setPeersError] = useState(null);

  // Editable valuation parameters
  const [editableParams, setEditableParams] = useState({
    forwardEps: 0,
    historicalPE: 0,
    peerPE: 0,
    fundamentalsPE: 0,
    weightHistorical: 0,
    weightPeer: 0,
    weightFundamentals: 0
  });

  // Load peer mappings from peers.md on mount
  useEffect(() => {
    setPeersLoading(true);
    fetch('/peers.md')
      .then(res => {
        if (!res.ok) throw new Error(`Failed to load peers.md: ${res.status}`);
        return res.text();
      })
      .then(content => {
        const peers = parsePeersMd(content);
        setDefaultPeers(peers);
        setPeersError(null);
      })
      .catch(err => {
        console.warn('Failed to load peers.md:', err);
        setPeersError(err.message);
        setDefaultPeers({});
      })
      .finally(() => setPeersLoading(false));
  }, []);

  // Prepopulate peer input when symbol or defaultPeers changes
  useEffect(() => {
    if (symbol && defaultPeers[symbol.toUpperCase()]) {
      setPeerInput(defaultPeers[symbol.toUpperCase()]);
    } else {
      // Keep existing input if no default mapping
      // or clear it if you prefer: setPeerInput('');
    }
  }, [symbol, defaultPeers]);

  // Initialize editable parameters when valuation data changes
  useEffect(() => {
    if (valuation) {
      const hasPeers = valuation.peer_comparison?.peer_pe_ratios || valuation.peer_comparison?.peers;
      const weights = valuation.justified_pe?.weighting || {};

      setEditableParams({
        forwardEps: valuation.forward_eps?.recommended || 0,
        historicalPE: valuation.historical_pe?.median || 0,
        peerPE: valuation.peer_comparison?.average_pe || 0,
        fundamentalsPE: valuation.fundamentals_analysis?.fundamentals_pe || valuation.fundamentals_pe || 0,
        weightHistorical: weights.historical || 0,
        weightPeer: hasPeers ? (weights.peer || 0) : 0,
        weightFundamentals: weights.fundamentals || 0
      });
    }
  }, [valuation]);

  // Handle parameter change
  const handleParamChange = (param, value) => {
    setEditableParams(prev => ({
      ...prev,
      [param]: parseFloat(value) || 0
    }));
  };

  // Calculate fair value based on editable parameters
  const calculateEditableFairValue = () => {
    const { forwardEps, historicalPE, peerPE, fundamentalsPE, weightHistorical, weightPeer, weightFundamentals } = editableParams;
    const hasPeers = valuation?.peer_comparison?.peer_pe_ratios || valuation?.peer_comparison?.peers;

    // Weighted P/E calculation
    let weightedPE;
    if (hasPeers) {
      weightedPE = (weightHistorical * historicalPE) + (weightPeer * peerPE) + (weightFundamentals * fundamentalsPE);
    } else {
      weightedPE = (weightHistorical * historicalPE) + (weightFundamentals * fundamentalsPE);
    }

    // Fair value = EPS × Weighted P/E
    const fairValue = forwardEps * weightedPE;

    return {
      fairValue,
      weightedPE,
      currentPrice: valuation?.fair_value?.current_price || 0,
      upside: valuation?.fair_value?.current_price ? ((fairValue - valuation.fair_value.current_price) / valuation.fair_value.current_price * 100) : 0
    };
  };

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
            <small>
              {peersLoading && 'Loading default peers...'}
              {peersError && <span className="error">Could not load default peers</span>}
              {!peersLoading && !peersError && (
                peerInput && defaultPeers[symbol?.toUpperCase()] === peerInput
                  ? '✓ Auto-populated peers (editable)'
                  : 'Leave blank for valuation without peer comparison'
              )}
            </small>
          </div>
          <button
            onClick={() => onCalculate(parsePeersInput(peerInput))}
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
          onClick={() => onCalculate(parsePeersInput(peerInput))}
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

        {/* Step 1: Fair Value Calculation */}
        <div className="valuation-step final-step">
          <h4><span className="step-number">1.</span> Fair Value Calculation</h4>

          {/* Formula Display */}
          <div className="formula-section">
            <div className="formula-display">
              <strong>Formula:</strong>
              <div className="formula-expression">
                Fair Value = EPS × (w₁ × PE₁ + {valuation.peer_comparison?.peer_pe_ratios && 'w₂ × PE₂ + '}w₃ × PE₃)
              </div>
            </div>
          </div>

          {/* Editable Parameters */}
          <div className="editable-params">
            <div className="params-grid">
              {/* Column 1: Forward EPS */}
              <div className="param-column">
                <h5>Forward EPS:</h5>
                <div className="param-row">
                  <label>EPS:</label>
                  <input
                    type="number"
                    step="0.01"
                    value={editableParams.forwardEps}
                    onChange={(e) => handleParamChange('forwardEps', e.target.value)}
                    className="param-input"
                  />
                </div>
              </div>

              {/* Column 2: P/E Ratios */}
              <div className="param-column">
                <h5>P/E Ratios:</h5>
                <div className="param-row">
                  <label>PE₁ (Historical):</label>
                  <input
                    type="number"
                    step="0.01"
                    value={editableParams.historicalPE}
                    onChange={(e) => handleParamChange('historicalPE', e.target.value)}
                    className="param-input"
                  />
                </div>
                {valuation.peer_comparison?.peer_pe_ratios && (
                  <div className="param-row">
                    <label>PE₂ (Peer Avg):</label>
                    <input
                      type="number"
                      step="0.01"
                      value={editableParams.peerPE}
                      onChange={(e) => handleParamChange('peerPE', e.target.value)}
                      className="param-input"
                    />
                  </div>
                )}
                <div className="param-row">
                  <label>PE₃ (Fundamentals):</label>
                  <input
                    type="number"
                    step="0.01"
                    value={editableParams.fundamentalsPE}
                    onChange={(e) => handleParamChange('fundamentalsPE', e.target.value)}
                    className="param-input"
                  />
                </div>
              </div>

              {/* Column 3: Weights */}
              <div className="param-column">
                <h5>Weights (sum to 1.0):</h5>
                <div className="param-row">
                  <label>w₁ (Historical):</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    value={editableParams.weightHistorical.toFixed(2)}
                    onChange={(e) => handleParamChange('weightHistorical', e.target.value)}
                    className="param-input"
                  />
                </div>
                {valuation.peer_comparison?.peer_pe_ratios && (
                  <div className="param-row">
                    <label>w₂ (Peer):</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max="1"
                      value={editableParams.weightPeer.toFixed(2)}
                      onChange={(e) => handleParamChange('weightPeer', e.target.value)}
                      className="param-input"
                    />
                  </div>
                )}
                <div className="param-row">
                  <label>w₃ (Fundamentals):</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    value={editableParams.weightFundamentals.toFixed(2)}
                    onChange={(e) => handleParamChange('weightFundamentals', e.target.value)}
                    className="param-input"
                  />
                </div>
                <div className="weight-sum">
                  Sum: {(editableParams.weightHistorical + editableParams.weightPeer + editableParams.weightFundamentals).toFixed(2)}
                </div>
              </div>
            </div>
          </div>

          {/* Calculated Results */}
          <ul className="step-list">
            <li className="highlight-item">
              <strong>Weighted P/E:</strong> {calculateEditableFairValue().weightedPE.toFixed(2)}
            </li>
            <li className="highlight-item">
              <strong>Fair Value:</strong> {formatCurrency(calculateEditableFairValue().fairValue)}
            </li>
            <li><strong>Current Price:</strong> {formatCurrency(calculateEditableFairValue().currentPrice)}</li>
            <li>
              <strong>Upside:</strong>
              <span className={calculateEditableFairValue().upside >= 0 ? 'positive-upside' : 'negative-upside'}>
                {' '}{calculateEditableFairValue().upside.toFixed(2)}%
              </span>
            </li>
          </ul>
        </div>

        {/* Step 2: Forward EPS */}
        <div className="valuation-step">
          <h4><span className="step-number">2.</span> Forward EPS Calculation (Dual Methods)
            {valuation.forward_eps?.growth_method?.historical_eps?.length &&
              ` (${valuation.forward_eps.growth_method.historical_eps.length} quarters)`}
          </h4>
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

        {/* Step 3: Historical P/E */}
        <div className="valuation-step">
          <h4><span className="step-number">3.</span> Historical P/E Analysis ({valuation.historical_pe?.pe_ratios?.length || 5} quarters)</h4>
          <ul className="step-list">
            <li><strong>Average:</strong> {valuation.historical_pe?.average?.toFixed(2) || 'N/A'}</li>
            <li><strong>Median:</strong> {valuation.historical_pe?.median?.toFixed(2) || 'N/A'}</li>
            <li><strong>Range:</strong> {valuation.historical_pe?.min?.toFixed(2)} - {valuation.historical_pe?.max?.toFixed(2)}</li>
          </ul>
        </div>

        {/* Step 4: Peer Comparison */}
        {(valuation.peer_comparison?.peer_pe_ratios || valuation.peer_comparison?.peers) && (
          <div className="valuation-step">
            <h4>
              <span className="step-number">4.</span> Peer Comparison (
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

        {/* Step 5: Fundamentals */}
        <div className="valuation-step">
          <h4><span className="step-number">{valuation.peer_comparison?.peer_pe_ratios ? '5' : '4'}.</span> Fundamentals-Based P/E
            {valuation.fundamentals_analysis?.quarterly_metrics?.length &&
              ` (${valuation.fundamentals_analysis.quarterly_metrics.length} quarters)`}
          </h4>
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

        {/* Step 6: Justified P/E */}
        <div className="valuation-step">
          <h4><span className="step-number">{valuation.peer_comparison?.peer_pe_ratios ? '6' : '5'}.</span> Justified P/E Synthesis</h4>
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

      </div>

      {/* Detailed Data Visualization Charts */}
      <ValuationCharts valuation={valuation} />

      {/* Peer Input for Recalculation */}
      <div className="peer-recalc-section">
        <label htmlFor="peers-recalc">Update Peer Tickers:</label>
        <div className="peer-input-controls">
          <input
            id="peers-recalc"
            type="text"
            placeholder="e.g., MSFT, GOOGL, META"
            value={peerInput}
            onChange={(e) => setPeerInput(e.target.value)}
            className="peer-input"
          />
          {defaultPeers[symbol?.toUpperCase()] && (
            <button
              onClick={() => setPeerInput(defaultPeers[symbol.toUpperCase()])}
              className="reset-peers-button"
              title="Reset to default peers"
            >
              Reset
            </button>
          )}
        </div>
        <small>
          {peerInput && defaultPeers[symbol?.toUpperCase()] === peerInput
            ? '✓ Using default peers for ' + symbol
            : 'Modify and click Recalculate to update'}
        </small>
      </div>
    </div>
  );
}

ValuationAnalysis.propTypes = {
  symbol: PropTypes.string.isRequired,
  valuation: PropTypes.object,
  onCalculate: PropTypes.func.isRequired,
  loading: PropTypes.bool.isRequired
};

export default ValuationAnalysis;
