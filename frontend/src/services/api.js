import axios from 'axios';

const API_BASE_URL = '/api';

/**
 * Fetch financial data for a ticker symbol
 * @param {string} ticker - Stock ticker symbol
 * @returns {Promise<Object>} Financial data
 */
export async function fetchTickerData(ticker) {
  try {
    const response = await axios.get(`${API_BASE_URL}/ticker/${ticker}`);
    return response.data;
  } catch (error) {
    if (error.response) {
      // Server responded with error status
      if (error.response.status === 404) {
        throw new Error(`Ticker symbol '${ticker}' not found. Please verify the symbol and try again.`);
      } else if (error.response.status === 400) {
        throw new Error(error.response.data.detail || 'Invalid ticker format');
      } else if (error.response.status === 500) {
        throw new Error('Server error. Please try again later.');
      }
    } else if (error.request) {
      // Request was made but no response received
      throw new Error('Unable to reach the server. Please check your connection.');
    }
    throw new Error('An unexpected error occurred');
  }
}

/**
 * Force refresh financial data for a ticker
 * @param {string} ticker - Stock ticker symbol
 * @returns {Promise<Object>} Refreshed financial data
 */
export async function refreshTickerData(ticker) {
  try {
    const response = await axios.post(`${API_BASE_URL}/ticker/${ticker}/refresh`);
    return response.data;
  } catch (error) {
    if (error.response) {
      if (error.response.status === 429) {
        throw new Error('API rate limit reached. Please try again later.');
      } else if (error.response.status === 404) {
        throw new Error(`Unable to refresh data for '${ticker}'`);
      }
    }
    throw new Error('Failed to refresh data. Please try again later.');
  }
}

/**
 * Get list of cached tickers
 * @returns {Promise<Array>} List of cached tickers
 */
export async function getCachedTickers() {
  try {
    const response = await axios.get(`${API_BASE_URL}/tickers`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch cached tickers:', error);
    return [];
  }
}

/**
 * Search for tickers
 * @param {string} query - Search query
 * @returns {Promise<Array>} Search results
 */
export async function searchTickers(query) {
  try {
    const response = await axios.get(`${API_BASE_URL}/search`, {
      params: { q: query }
    });
    return response.data;
  } catch (error) {
    console.error('Search failed:', error);
    return [];
  }
}

/**
 * Calculate stock valuation
 * @param {string} ticker - Stock ticker symbol
 * @param {Array<string>} peers - Optional list of peer tickers
 * @returns {Promise<Object>} Valuation analysis
 */
export async function calculateValuation(ticker, peers = null) {
  try {
    const response = await axios.post(`${API_BASE_URL}/valuation/${ticker}`, {
      peers: peers
    });
    return response.data;
  } catch (error) {
    if (error.response) {
      if (error.response.status === 404) {
        throw new Error(error.response.data.detail || `Insufficient data for valuation of '${ticker}'`);
      } else if (error.response.status === 400) {
        throw new Error(error.response.data.detail || 'Invalid request');
      }
    }
    throw new Error('Failed to calculate valuation. Please try again later.');
  }
}

/**
 * Get cached valuation
 * @param {string} ticker - Stock ticker symbol
 * @param {Array<string>} peers - Optional list of peer tickers
 * @returns {Promise<Object>} Cached valuation data
 */
export async function getCachedValuation(ticker, peers = null) {
  try {
    const params = peers && peers.length > 0 ? { peers: peers.join(',') } : {};
    const response = await axios.get(`${API_BASE_URL}/valuation/${ticker}`, { params });
    return response.data;
  } catch (error) {
    if (error.response && error.response.status === 404) {
      return null; // No cached data available
    }
    throw error;
  }
}