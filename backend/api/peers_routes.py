"""
API routes for peer ticker mappings
"""
from fastapi import APIRouter, HTTPException
import os

router = APIRouter()

@router.get("/peers/mappings")
def get_peer_mappings():
    """
    Read and parse peers.md file to get ticker-to-peers mappings

    Returns:
        Dict mapping tickers to their peer lists

    Example response:
        {
            "AAPL": "AMZN, MSFT, GOOGL, META",
            "AMD": "NVDA, AVGO, INTC, QCOM",
            ...
        }
    """
    # Path to peers.md (one level up from backend/)
    peers_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'peers.md')

    try:
        if not os.path.exists(peers_file):
            # Return empty dict if file doesn't exist
            return {}

        mappings = {}

        with open(peers_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:  # Skip empty lines
                    continue

                # Parse format: "TICKER    PEER1, PEER2, PEER3"
                parts = line.split(None, 1)  # Split on whitespace, max 2 parts
                if len(parts) == 2:
                    ticker = parts[0].strip().upper()
                    peers = parts[1].strip()
                    mappings[ticker] = peers

        return mappings

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading peers file: {str(e)}"
        )
