import React from 'react';
import './DataTable.css';

function DataTable({ data }) {
  if (!data || data.length === 0) {
    return <div className="no-data">No financial data available</div>;
  }

  // Sort data by quarter (oldest to newest)
  const sortedData = [...data].sort((a, b) => a.quarter.localeCompare(b.quarter));

  // Format number with thousand separators
  const formatNumber = (num) => {
    if (num === null || num === undefined) return 'N/A';
    return new Intl.NumberFormat('en-US').format(num);
  };

  // Format currency in millions
  const formatMillion = (num) => {
    if (num === null || num === undefined) return 'N/A';
    return '$' + (num / 1000000).toFixed(1) + 'M';
  };

  // Format percentage
  const formatPercent = (num) => {
    if (num === null || num === undefined) return 'N/A';
    return (num * 100).toFixed(2) + '%';
  };

  return (
    <div className="data-table-container">
      <h3>Financial Data (Last 8 Quarters)</h3>
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Metric</th>
              {sortedData.map((item) => (
                <th key={item.quarter}>
                  <div style={{ fontWeight: 'bold' }}>
                    {item.fiscal_date || item.quarter}
                  </div>
                  {item.reported_date && (
                    <div style={{ fontSize: '0.8em', fontWeight: 'normal', color: '#666', marginTop: '4px' }}>
                      Reported: {item.reported_date}
                    </div>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="metric-label">EPS</td>
              {sortedData.map((item) => (
                <td key={item.quarter}>${item.eps?.toFixed(2) || 'N/A'}</td>
              ))}
            </tr>
            <tr className="alt-row">
              <td className="metric-label">Free Cash Flow</td>
              {sortedData.map((item) => (
                <td key={item.quarter}>{formatMillion(item.fcf)}</td>
              ))}
            </tr>
            <tr>
              <td className="metric-label">Gross Income</td>
              {sortedData.map((item) => (
                <td key={item.quarter}>{formatMillion(item.gross_income)}</td>
              ))}
            </tr>
            <tr className="alt-row">
              <td className="metric-label">Gross Margin</td>
              {sortedData.map((item) => (
                <td key={item.quarter}>{formatPercent(item.gross_margin)}</td>
              ))}
            </tr>
            <tr>
              <td className="metric-label">Net Income</td>
              {sortedData.map((item) => (
                <td key={item.quarter}>{formatMillion(item.net_income)}</td>
              ))}
            </tr>
            <tr className="alt-row">
              <td className="metric-label">Net Margin</td>
              {sortedData.map((item) => (
                <td key={item.quarter}>{formatPercent(item.net_margin)}</td>
              ))}
            </tr>
            <tr>
              <td className="metric-label">CapEx</td>
              {sortedData.map((item) => (
                <td key={item.quarter}>{formatMillion(item.capex)}</td>
              ))}
            </tr>
            <tr className="alt-row">
              <td className="metric-label">Cash Balance</td>
              {sortedData.map((item) => (
                <td key={item.quarter}>{formatMillion(item.cash)}</td>
              ))}
            </tr>
            <tr>
              <td className="metric-label">Total Debt</td>
              {sortedData.map((item) => (
                <td key={item.quarter}>{formatMillion(item.debt)}</td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default DataTable;