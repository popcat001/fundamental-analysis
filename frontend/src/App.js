import React, { useState } from 'react';
import './App.css';
import TickerSearch from './components/TickerSearch';
import DataTable from './components/DataTable';
import ValuationAnalysis from './components/ValuationAnalysis';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorMessage from './components/ErrorMessage';
import { fetchTickerData, refreshTickerData, calculateValuation } from './services/api';

function App() {
  const [tickerData, setTickerData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [valuationData, setValuationData] = useState(null);
  const [valuationLoading, setValuationLoading] = useState(false);
  const [valuationError, setValuationError] = useState(null);

  const handleTickerSearch = async (ticker) => {
    setLoading(true);
    setError(null);
    setValuationData(null);
    setValuationError(null);

    try {
      const data = await fetchTickerData(ticker);
      setTickerData(data);
    } catch (err) {
      setError(err.message);
      setTickerData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    if (!tickerData) return;

    setLoading(true);
    setError(null);
    setValuationData(null);
    setValuationError(null);

    try {
      const data = await refreshTickerData(tickerData.symbol);
      setTickerData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleValuationCalculate = async (peers) => {
    if (!tickerData) return;

    setValuationLoading(true);
    setValuationError(null);

    try {
      const data = await calculateValuation(tickerData.symbol, peers);
      setValuationData(data);
    } catch (err) {
      setValuationError(err.message);
      setValuationData(null);
    } finally {
      setValuationLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Fundamental Analysis Tool</h1>
        <p>View financial data for publicly traded companies</p>
      </header>

      <main className="App-main">
        <TickerSearch onSearch={handleTickerSearch} />

        {error && <ErrorMessage message={error} />}

        {loading && <LoadingSpinner />}

        {tickerData && !loading && (
          <>
            <div className="ticker-info">
              <h2>{tickerData.symbol} - {tickerData.company_name}</h2>
              <p className="last-updated">
                Last updated: {new Date(tickerData.last_updated).toLocaleString()}
              </p>
              <button onClick={handleRefresh} className="refresh-button">
                Refresh Data
              </button>
            </div>

            <DataTable data={tickerData.data} />

            {valuationError && <ErrorMessage message={valuationError} />}

            <ValuationAnalysis
              symbol={tickerData.symbol}
              valuation={valuationData}
              onCalculate={handleValuationCalculate}
              loading={valuationLoading}
            />
          </>
        )}
      </main>

      <footer className="App-footer">
        <p>Data sources: Alpha Vantage (financials), Yahoo Finance (prices)</p>
      </footer>
    </div>
  );
}

export default App;