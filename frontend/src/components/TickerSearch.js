import React, { useState } from 'react';
import './TickerSearch.css';

function TickerSearch({ onSearch }) {
  const [ticker, setTicker] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmedTicker = ticker.trim().toUpperCase();

    if (trimmedTicker && /^[A-Z]{1,5}$/.test(trimmedTicker)) {
      onSearch(trimmedTicker);
    } else {
      alert('Please enter a valid ticker symbol (1-5 letters)');
    }
  };

  return (
    <div className="ticker-search">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          placeholder="Enter ticker symbol (e.g., AAPL)"
          maxLength="5"
          className="ticker-input"
        />
        <button type="submit" className="search-button">
          Search
        </button>
      </form>
    </div>
  );
}

export default TickerSearch;