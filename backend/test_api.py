#!/usr/bin/env python3
"""
Simple test script to verify the API is working correctly.
Run this after starting the FastAPI server.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

def test_root():
    """Test the root endpoint"""
    print("Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

def test_ticker_data(symbol="AAPL"):
    """Test fetching ticker data"""
    print(f"Testing ticker data for {symbol}...")
    response = requests.get(f"{BASE_URL}/api/ticker/{symbol}")

    if response.status_code == 200:
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Company: {data['company_name']}")
        print(f"Last Updated: {data['last_updated']}")
        print(f"Number of quarters: {len(data['data'])}")
        if data['data']:
            latest = data['data'][0]
            print(f"Latest quarter: {latest['quarter']}")
            print(f"EPS: ${latest['eps']}")
    else:
        print(f"Error: {response.status_code}")
        print(f"Details: {response.json()}")
    print()

def test_cached_tickers():
    """Test getting cached tickers"""
    print("Testing cached tickers...")
    response = requests.get(f"{BASE_URL}/api/tickers")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Cached tickers: {len(data)}")
    for ticker in data[:3]:  # Show first 3
        print(f"  - {ticker['symbol']}: {ticker['company_name']}")
    print()

def main():
    """Run all tests"""
    print("=" * 50)
    print("Testing Fundamental Analysis API")
    print("=" * 50)
    print()

    try:
        test_health_check()
        test_root()
        test_ticker_data("AAPL")
        test_cached_tickers()
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the API server.")
        print("Make sure the server is running with: python app.py")
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    main()