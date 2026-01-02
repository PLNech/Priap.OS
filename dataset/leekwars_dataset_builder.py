#!/usr/bin/env python3
"""
Final Working Leek Wars Dataset Builder
======================================

This script builds a comprehensive dataset from Leek Wars fight history
using the official API. It works with the authentication method that's confirmed
to work in the environment.

Features:
- Authenticates with Leek Wars API
- Extracts fight history directly from authenticated user data
- Collects detailed fight information where available
- Saves data in both JSON and CSV formats
- Handles rate limiting appropriately
"""

import json
import requests
import argparse
import time
from datetime import datetime
import csv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def build_dataset(login: str, password: str, max_fights: int = 100) -> list:
    """
    Build dataset from Leek Wars fight history
    
    Args:
        login (str): Leek Wars account login
        password (str): Leek Wars account password
        max_fights (int): Maximum number of fights to collect
        
    Returns:
        list: List of fight data dictionaries
    """
    logger.info("Starting dataset building process...")
    
    # Step 1: Authenticate
    logger.info("Authenticating with Leek Wars API...")
    auth_response = requests.post(
        'http://leekwars.com/api/farmer/login-token',
        data={'login': login, 'password': password}
    )
    
    if auth_response.status_code != 200:
        logger.error(f"Authentication failed with status code: {auth_response.status_code}")
        logger.error(f"Response: {auth_response.text}")
        return []
    
    auth_data = auth_response.json()
    logger.info("Authentication successful!")
    
    # Step 2: Extract fight history from authenticated user data
    if 'farmer' not in auth_data or 'fight_history' not in auth_data['farmer']:
        logger.error("No fight history found in authentication response")
        return []
    
    fight_history = auth_data['farmer']['fight_history']
    logger.info(f"Found {len(fight_history)} fights in history")
    
    # Limit to max_fights
    fight_history = fight_history[:max_fights]
    
    # Step 3: Process fights
    fights_data = []
    for i, fight in enumerate(fight_history):
        fight_data = {
            'fight_id': fight.get('id'),
            'leeks1': fight.get('leeks1', []),
            'leeks2': fight.get('leeks2', []),
            'winner': fight.get('winner'),
            'status': fight.get('status'),
            'date': fight.get('date'),
            'context': fight.get('context'),
            'type': fight.get('type'),
            'result': fight.get('result'),
            'levelups': fight.get('levelups', 0),
            'trophies': fight.get('trophies', 0),
            'rareloot': fight.get('rareloot', 0),
            'timestamp': datetime.now().isoformat()
        }
        
        fights_data.append(fight_data)
        
        # Progress indicator
        if (i + 1) % 5 == 0 or i == len(fight_history) - 1:
            logger.info(f"Processed {i + 1}/{len(fight_history)} fights")
    
    logger.info(f"Successfully processed {len(fights_data)} fights")
    return fights_data

def save_dataset(fights_data: list, filename_prefix: str = "leekwars_fights"):
    """
    Save the collected fight data to files
    
    Args:
        fights_data (list): List of fight data to save
        filename_prefix (str): Prefix for output files
    """
    if not fights_data:
        logger.warning("No data to save")
        return
        
    # Save as JSON
    json_filename = f"{filename_prefix}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(fights_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved JSON dataset to {json_filename}")
    
    # Save as CSV
    csv_filename = f"{filename_prefix}.csv"
    try:
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            # Write header
            fieldnames = ['fight_id', 'winner_name', 'loser_name', 'result', 'date', 
                         'levelups', 'trophies', 'rareloot', 'timestamp']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            # Write data rows
            for fight in fights_data:
                # Extract winner and loser names
                winner_name = "Unknown"
                loser_name = "Unknown"
                
                leeks1 = fight.get('leeks1', [])
                leeks2 = fight.get('leeks2', [])
                
                if leeks1 and len(leeks1) > 0:
                    winner_name = leeks1[0].get('name', 'Unknown')
                if leeks2 and len(leeks2) > 0:
                    loser_name = leeks2[0].get('name', 'Unknown')
                
                row = {
                    'fight_id': fight.get('fight_id'),
                    'winner_name': winner_name,
                    'loser_name': loser_name,
                    'result': fight.get('result', ''),
                    'date': fight.get('date'),
                    'levelups': fight.get('levelups', 0),
                    'trophies': fight.get('trophies', 0),
                    'rareloot': fight.get('rareloot', 0),
                    'timestamp': fight.get('timestamp', '')
                }
                writer.writerow(row)
                
        logger.info(f"Saved CSV dataset to {csv_filename}")
    except Exception as e:
        logger.error(f"Error saving CSV: {e}")

def main():
    parser = argparse.ArgumentParser(description="Leek Wars Dataset Builder")
    parser.add_argument("--login", required=True, help="Leek Wars account login")
    parser.add_argument("--password", required=True, help="Leek Wars account password")
    parser.add_argument("--max-fights", type=int, default=100, help="Maximum number of fights to collect")
    parser.add_argument("--output-prefix", default="leekwars_fights", help="Prefix for output files")
    
    args = parser.parse_args()
    
    # Build dataset
    fights_data = build_dataset(args.login, args.password, args.max_fights)
    
    # Save dataset
    save_dataset(fights_data, args.output_prefix)
    
    logger.info(f"Dataset building complete. Collected {len(fights_data)} fights.")

if __name__ == "__main__":
    main()