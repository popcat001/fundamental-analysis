import React, { useState } from 'react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ComposedChart, Cell
} from 'recharts';
import './ValuationCharts.css';

function ValuationCharts({ valuation }) {
  const [expandedSections, setExpandedSections] = useState({});

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Chart 1: Forward EPS - Historical & Projected
  const renderForwardEPSChart = () => {
    if (!valuation?.forward_eps?.growth_method?.historical_eps) return null;

    // Growth Method Chart Data
    const growthHistoricalData = valuation.forward_eps.growth_method.historical_eps.map(item => ({
      quarter: item.quarter,
      actualEPS: item.eps,
      type: 'Historical'
    }));

    const growthProjectedData = valuation.forward_eps.growth_method.quarterly_estimates.map((eps, idx) => ({
      quarter: `Proj Q${idx + 1}`,
      projectedEPS: eps,
      type: 'Projected'
    }));

    const growthChartData = [...growthHistoricalData, ...growthProjectedData];

    // Regression Method Chart Data
    let regressionChartData = null;
    if (valuation.forward_eps.regression_method?.historical_eps) {
      const regressionHistoricalData = valuation.forward_eps.regression_method.historical_eps.map(item => ({
        quarter: item.quarter,
        actualEPS: item.eps,
        regressionFit: item.regression_fit,
        type: 'Historical'
      }));

      const regressionProjectedData = valuation.forward_eps.regression_method.quarterly_estimates.map((eps, idx) => ({
        quarter: `Proj Q${idx + 1}`,
        projectedEPS: eps,
        type: 'Projected'
      }));

      regressionChartData = [...regressionHistoricalData, ...regressionProjectedData];
    }

    return (
      <div className="chart-section">
        <h5 onClick={() => toggleSection('forwardEPS')} className="chart-header">
          📊 Forward EPS: Historical & Projected (Dual Methods)
          <span className="toggle-icon">{expandedSections.forwardEPS ? '▼' : '▶'}</span>
        </h5>
        {expandedSections.forwardEPS && (
          <>
            <div className="chart-container">
              <h6>Growth Method</h6>
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={growthChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="quarter" angle={-45} textAnchor="end" height={80} />
                  <YAxis label={{ value: 'EPS ($)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="actualEPS"
                    stroke="#2563eb"
                    strokeWidth={2}
                    name="Historical EPS"
                    dot={{ r: 4 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="projectedEPS"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    name="Projected EPS (Growth)"
                    dot={{ r: 4 }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
              <div className="chart-info">
                <p><strong>Growth Rate:</strong> {(valuation.forward_eps.growth_method.growth_rate * 100).toFixed(2)}% QoQ</p>
                <p><strong>Forward EPS (Growth):</strong> ${valuation.forward_eps.growth_method.forward_eps}</p>
              </div>
            </div>

            {regressionChartData && (
              <div className="chart-container">
                <h6>Regression Method</h6>
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart data={regressionChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="quarter" angle={-45} textAnchor="end" height={80} />
                    <YAxis label={{ value: 'EPS ($)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="actualEPS"
                      stroke="#2563eb"
                      strokeWidth={2}
                      name="Historical EPS"
                      dot={{ r: 4 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="regressionFit"
                      stroke="#8b5cf6"
                      strokeWidth={2}
                      name="Regression Fit"
                      dot={{ r: 3 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="projectedEPS"
                      stroke="#10b981"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      name="Projected EPS (Regression)"
                      dot={{ r: 4 }}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
                <div className="chart-info">
                  {valuation.forward_eps.regression_method.slope !== undefined && valuation.forward_eps.regression_method.intercept !== undefined && (
                    <p><strong>Regression Formula:</strong> EPS = {valuation.forward_eps.regression_method.slope >= 0 ? '' : '-'}{Math.abs(valuation.forward_eps.regression_method.slope).toFixed(4)} × Quarter {valuation.forward_eps.regression_method.intercept >= 0 ? '+ ' : '- '}{Math.abs(valuation.forward_eps.regression_method.intercept).toFixed(4)}</p>
                  )}
                  <p><strong>R² (Goodness of Fit):</strong> {valuation.forward_eps.regression_method.r_squared.toFixed(3)}</p>
                  <p><strong>Forward EPS (Regression):</strong> ${valuation.forward_eps.regression_method.forward_eps}</p>
                </div>
              </div>
            )}

            <div className="chart-info">
              <p><strong>Recommended Forward EPS (Average):</strong> ${valuation.forward_eps.recommended}</p>
            </div>
          </>
        )}
      </div>
    );
  };

  // Chart 2: Historical P/E Ratios
  const renderHistoricalPEChart = () => {
    if (!valuation?.historical_pe?.pe_ratios) return null;

    const chartData = valuation.historical_pe.pe_ratios.map(item => ({
      quarter: item.quarter,
      peRatio: item.pe_ratio,
      price: item.price,
      ttmEPS: item.ttm_eps
    }));

    const avgPE = valuation.historical_pe.average;

    return (
      <div className="chart-section">
        <h5 onClick={() => toggleSection('historicalPE')} className="chart-header">
          📊 Historical P/E Ratios (Last {chartData.length} Quarters)
          <span className="toggle-icon">{expandedSections.historicalPE ? '▼' : '▶'}</span>
        </h5>
        {expandedSections.historicalPE && (
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="quarter" angle={-45} textAnchor="end" height={80} />
                <YAxis yAxisId="left" label={{ value: 'P/E Ratio', angle: -90, position: 'insideLeft' }} />
                <YAxis yAxisId="right" orientation="right" label={{ value: 'Price ($)', angle: 90, position: 'insideRight' }} />
                <Tooltip />
                <Legend />
                <Bar yAxisId="left" dataKey="peRatio" fill="#10b981" name="P/E Ratio" />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="price"
                  stroke="#ef4444"
                  strokeWidth={2}
                  name="Stock Price"
                  dot={{ r: 3 }}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey={avgPE}
                  stroke="#9333ea"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  name={`Avg P/E (${avgPE.toFixed(1)})`}
                />
              </ComposedChart>
            </ResponsiveContainer>
            <div className="chart-info">
              <p><strong>Average P/E:</strong> {avgPE.toFixed(2)}</p>
              <p><strong>Median P/E:</strong> {valuation.historical_pe.median.toFixed(2)}</p>
              <p><strong>Range:</strong> {valuation.historical_pe.min.toFixed(2)} - {valuation.historical_pe.max.toFixed(2)}</p>
              <p><strong>Std Dev:</strong> {valuation.historical_pe.std_dev.toFixed(2)}</p>
            </div>
          </div>
        )}
      </div>
    );
  };

  // Chart 3: Peer Comparison
  const renderPeerComparisonChart = () => {
    if (!valuation?.peer_comparison?.peer_pe_ratios) return null;

    const chartData = valuation.peer_comparison.peer_pe_ratios.map(peer => ({
      ticker: peer.ticker,
      peRatio: peer.pe,
      ttmEPS: peer.ttm_eps,
      price: peer.price
    }));

    // Add target company
    chartData.push({
      ticker: valuation.symbol + ' (Target)',
      peRatio: valuation.current_metrics.current_pe,
      ttmEPS: valuation.current_metrics.ttm_eps,
      price: valuation.current_metrics.current_price
    });

    return (
      <div className="chart-section">
        <h5 onClick={() => toggleSection('peerComparison')} className="chart-header">
          📊 Peer P/E Comparison
          <span className="toggle-icon">{expandedSections.peerComparison ? '▼' : '▶'}</span>
        </h5>
        {expandedSections.peerComparison && (
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="ticker" />
                <YAxis label={{ value: 'P/E Ratio', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="peRatio" name="P/E Ratio">
                  {chartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.ticker.includes('Target') ? '#f59e0b' : '#6366f1'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="chart-info">
              <p><strong>Peer Average P/E:</strong> {valuation.peer_comparison.average_pe.toFixed(2)}</p>
              <p><strong>Peer Median P/E:</strong> {valuation.peer_comparison.median_pe.toFixed(2)}</p>
              <p><strong>Peer Range:</strong> {valuation.peer_comparison.range[0].toFixed(2)} - {valuation.peer_comparison.range[1].toFixed(2)}</p>
            </div>
          </div>
        )}
      </div>
    );
  };

  // Chart 4: Fundamentals - Quarterly Metrics Trends
  const renderFundamentalsChart = () => {
    if (!valuation?.fundamentals_analysis?.quarterly_metrics) return null;

    const chartData = valuation.fundamentals_analysis.quarterly_metrics;

    return (
      <div className="chart-section">
        <h5 onClick={() => toggleSection('fundamentals')} className="chart-header">
          📊 Fundamentals: Quarterly Metrics Trends
          <span className="toggle-icon">{expandedSections.fundamentals ? '▼' : '▶'}</span>
        </h5>
        {expandedSections.fundamentals && (
          <>
            <div className="chart-container">
              <h6>EPS & Revenue Trend</h6>
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="quarter" angle={-45} textAnchor="end" height={80} />
                  <YAxis yAxisId="left" label={{ value: 'EPS ($)', angle: -90, position: 'insideLeft' }} />
                  <YAxis yAxisId="right" orientation="right" label={{ value: 'Revenue (M)', angle: 90, position: 'insideRight' }} />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="right" dataKey="revenue" fill="#3b82f6" name="Revenue ($M)" opacity={0.6} />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="eps"
                    stroke="#10b981"
                    strokeWidth={3}
                    name="EPS"
                    dot={{ r: 4 }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-container">
              <h6>Margin Trends</h6>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="quarter" angle={-45} textAnchor="end" height={80} />
                  <YAxis label={{ value: 'Margin (%)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="gross_margin"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    name="Gross Margin %"
                    dot={{ r: 4 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="net_margin"
                    stroke="#8b5cf6"
                    strokeWidth={2}
                    name="Net Margin %"
                    dot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-info">
              <p><strong>EPS Growth Rate (CAGR):</strong> {(valuation.fundamentals_analysis.metrics.eps_growth_rate * 100).toFixed(2)}%</p>
              <p><strong>Revenue Growth Rate (CAGR):</strong> {(valuation.fundamentals_analysis.metrics.revenue_growth_rate * 100).toFixed(2)}%</p>
              <p><strong>Avg Net Margin:</strong> {(valuation.fundamentals_analysis.metrics.avg_net_margin * 100).toFixed(2)}%</p>
              <p><strong>Margin Trend:</strong> {valuation.fundamentals_analysis.metrics.margin_trend}</p>
              <p><strong>Debt-to-Equity:</strong> {valuation.fundamentals_analysis.metrics.debt_to_equity.toFixed(2)}</p>
            </div>
          </>
        )}
      </div>
    );
  };

  return (
    <div className="valuation-charts">
      <h4 className="charts-title">📈 Detailed Data Visualization (Click to Expand)</h4>
      {renderForwardEPSChart()}
      {renderHistoricalPEChart()}
      {renderPeerComparisonChart()}
      {renderFundamentalsChart()}
    </div>
  );
}

export default ValuationCharts;
