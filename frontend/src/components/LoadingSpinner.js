import React from 'react';

function LoadingSpinner() {
  return (
    <div className="loading-spinner">
      <div className="spinner"></div>
      <p>Loading financial data...</p>
    </div>
  );
}

export default LoadingSpinner;