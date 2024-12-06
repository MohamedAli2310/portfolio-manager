# Portfolio Manager

![Portfolio Manager Demo](demo/portfolio_manger_demo.gif)

A command-line tool to track and manage stock transactions with real-time market data integration.

## Features

- Track buy and sell transactions for multiple stocks
- Real-time market data integration via Yahoo Finance
- Color-coded profit/loss indicators
- Summarized view of active and closed positions
- Flexible offline mode for when market data isn't needed
- Automatic gain/loss calculations
- Transaction history view
- Support for unlimited transactions per stock

## Installation

1. Clone or download this repository
2. Install required dependencies:
   
`pip install pandas yfinance colorama`


## Usage

### Basic Usage

`python manager.py`

### Offline Mode (No Market Data)

`python manager.py --offline`

### Menu Options

1. Add Transaction
   - Enter stock symbol
   - Choose BUY or SELL
   - Input quantity and price
   - Optional: Specify date (YYYY-MM-DD)

2. View Portfolio Summary
   - Shows active positions with:
     - Current position size
     - Total P&L
     - Current market price (if online)
     - Current market value
     - Gain/Loss indicator
   - Shows closed positions with P&L
   - Displays portfolio totals

3. View All Transactions
   - Lists complete transaction history
   - Organized by stock
   - Shows all details of each trade

4. Exit
   - Saves and exits the program

### Data Storage

- All data is stored in 'portfolio.csv'
- Each stock gets one row with multiple transaction columns
- Data persists between sessions

### Color Coding

- Green: Positive values
- Red: Negative values
- Cyan: Headers
- Yellow: Stock symbols and status messages

## Notes

- Market data requires internet connection
- Use offline mode with '--offline' flag when internet isn't available
- Dates default to current date if not specified
- All money values are rounded to 2 decimal places
- Share quantities are always whole numbers

## Error Handling

- Gracefully handles network issues
- Validates all numeric inputs
- Protects against invalid date formats
- Handles program interruption (Ctrl+C)
