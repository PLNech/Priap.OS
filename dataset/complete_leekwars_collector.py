#!/usr/bin/env python3
"""
Comprehensive Leek Wars Data Collection Tool
=========================================

This tool demonstrates two approaches:
1. Your own fight history (working with your credentials)
2. Framework for collecting public data from KRR Analyser (conceptual)

Features:
- Works with your authenticated fight history (fully functional)
- Template for future public data collection
- Proper data structure for analysis
- Extensible architecture
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

class LeekWarsDataCollector:
    def __init__(self, login: str, password: str):
        self.login = login
        self.password = password
        self.token = None
        self.base_url = "http://leekwars.com/api"
        
    def authenticate(self) -> bool:
        """Authenticate with the Leek Wars API"""
        try:
            logger.info("Authenticating with Leek Wars API...")
            response = requests.post(
                f"{self.base_url}/farmer/login-token",
                data={'login': self.login, 'password': self.password}
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'token' in data:
                    self.token = data['token']
                    logger.info("Authentication successful")
                    return True
                else:
                    logger.error("Authentication failed: No token in response")
                    return False
            else:
                logger.error(f"Authentication failed with status code: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            return False
    
    def collect_own_fights(self, max_fights: int = 100) -> list:
        """Collect fights from your own history (fully working)"""
        if not self.authenticate():
            logger.error("Failed to authenticate")
            return []
            
        # Get user data which contains fight history
        try:
            logger.info("Fetching user data with fight history...")
            response = requests.post(
                f"{self.base_url}/farmer/get",
                data={'token': self.token}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                fight_history = user_data.get('fight_history', [])
                logger.info(f"Found {len(fight_history)} fights in history")
                
                # Process fights
                fights_data = []
                for i, fight in enumerate(fight_history[:max_fights]):
                    fight_data = {
                        'source': 'own_history',
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
                    logger.info(f"Processed fight {fight.get('id')} ({i+1}/{min(len(fight_history), max_fights)})")
                
                return fights_data
            else:
                logger.error(f"Failed to fetch user data: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error collecting own fights: {e}")
            return []

def save_dataset(fights_data: list, filename_prefix: str = "leekwars_fights"):
    """Save the collected fight data to files"""
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
            fieldnames = ['source', 'fight_id', 'winner_name', 'loser_name', 'result', 'date', 
                         'levelups', 'trophies', 'rareloot', 'timestamp']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
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
                    'source': fight.get('source', 'unknown'),
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
    parser = argparse.ArgumentParser(description="Leek Wars Data Collection Tool")
    parser.add_argument("--login", required=True, help="Leek Wars account login")
    parser.add_argument("--password", required=True, help="Leek Wars account password")
    parser.add_argument("--max-fights", type=int, default=100, help="Maximum number of fights to collect")
    parser.add_argument("--output-prefix", default="leekwars_fights", help="Prefix for output files")
    
    args = parser.parse_args()
    
    # Create collector and collect data
    collector = LeekWarsDataCollector(args.login, args.password)
    fights_data = collector.collect_own_fights(args.max_fights)
    
    # Save dataset
    save_dataset(fights_data, args.output_prefix)
    
    logger.info(f"Dataset building complete. Collected {len(fights_data)} fights.")

if __name__ == "__main__":
    main()