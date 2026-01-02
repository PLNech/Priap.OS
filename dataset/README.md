# Leek Wars Dataset Builder

This tool builds a structured dataset from Leek Wars fight data using the official API.

## Features

- Authenticates with Leek Wars API using your credentials
- Extracts fight history directly from your account
- Saves data in both JSON and CSV formats
- Includes comprehensive metadata for each fight
- Handles rate limiting appropriately

## Data Included

Each fight entry contains:
- Fight ID
- Participating leeks (names and IDs)
- Winner/loser information
- Fight result (win/defeat)
- Date and timestamp
- Additional metadata (level-ups, trophies, rare loot)

## Usage

### Basic Usage
```bash
python final_leekwars_dataset_builder.py --login YOUR_LOGIN --password YOUR_PASSWORD
```

### Collect More Fights
```bash
python final_leekwars_dataset_builder.py --login YOUR_LOGIN --password YOUR_PASSWORD --max-fights 50
```

### Custom Output Name
```bash
python final_leekwars_dataset_builder.py --login YOUR_LOGIN --password YOUR_PASSWORD --output-prefix my_dataset
```

## Output Files

- `leekwars_fights.json` - Complete fight data in JSON format
- `leekwars_fights.csv` - Simplified fight data in CSV format

## Limitations

Due to API restrictions, this tool can only collect:
1. Your own fight history (which is what we've successfully demonstrated)
2. Public data that's accessible through the API

The tool works with the authentication method that's confirmed to function in the environment.

## Security Note

Never commit your credentials to version control. The tool uses command-line arguments for credentials.