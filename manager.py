import pandas as pd
import numpy as np
from datetime import datetime
import os
import argparse
from colorama import init, Fore, Style
init(autoreset=True)  # Initialize colorama

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

def format_money(amount, include_plus=False):
    """Format money values with color based on positive/negative"""
    if amount > 0:
        return f"{Fore.GREEN}{'+' if include_plus else ''}{amount:.2f}{Style.RESET_ALL}"
    elif amount < 0:
        return f"{Fore.RED}{amount:.2f}{Style.RESET_ALL}"
    return f"{amount:.2f}"

class PortfolioManager:
    def __init__(self, csv_file='portfolio.csv', offline_mode=False):
        self.csv_file = csv_file
        self.offline_mode = offline_mode
        self.df = self._load_or_create_df()

    def _load_or_create_df(self):
        """Load existing CSV or create new DataFrame with proper structure"""
        if os.path.exists(self.csv_file):
            df = pd.read_csv(self.csv_file)
            # Replace NaN with empty string for string columns, 0 for numeric columns
            for col in df.columns:
                if 'type' in col or 'date' in col:
                    df[col] = df[col].fillna('')
                else:
                    df[col] = df[col].fillna(0)
            return df
        else:
            initial_columns = ['symbol']
            for i in range(1, 6):
                initial_columns.extend(self._get_transaction_columns(i))
            return pd.DataFrame(columns=initial_columns)

    def _get_transaction_columns(self, idx):
        """Get column names for a transaction set"""
        prefix = f't{idx}_'
        return [
            f'{prefix}type',
            f'{prefix}date',
            f'{prefix}qty',
            f'{prefix}price',
            f'{prefix}total'
        ]

    def _extend_columns_if_needed(self, needed_transactions):
        """Extend DataFrame columns if more transaction slots are needed"""
        current_transactions = (len(self.df.columns) - 1) // 5
        if needed_transactions > current_transactions:
            new_columns = []
            for i in range(current_transactions + 1, needed_transactions + 1):
                new_columns.extend(self._get_transaction_columns(i))
            for col in new_columns:
                if 'type' in col or 'date' in col:
                    self.df[col] = ''
                else:
                    self.df[col] = 0

    def add_transaction(self, symbol, trans_type, quantity, price, date=None):
        """Add a new stock transaction"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        total = round(quantity * price * (-1 if trans_type.lower() == 'buy' else 1), 2)
        
        stock_row = self.df[self.df['symbol'] == symbol]
        if len(stock_row) == 0:
            new_row = {'symbol': symbol}
            for i in range(1, 6):
                prefix = f't{i}_'
                new_row.update({
                    f'{prefix}type': '',
                    f'{prefix}date': '',
                    f'{prefix}qty': 0,
                    f'{prefix}price': 0,
                    f'{prefix}total': 0
                })
            new_row.update({
                't1_type': trans_type.upper(),
                't1_date': date,
                't1_qty': int(quantity),
                't1_price': price,
                't1_total': total
            })
            self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
        else:
            row_idx = stock_row.index[0]
            transaction_num = 1
            while True:
                col_type = f't{transaction_num}_type'
                if col_type not in self.df.columns:
                    self._extend_columns_if_needed(transaction_num)
                
                if pd.isna(self.df.at[row_idx, col_type]) or self.df.at[row_idx, col_type] == '':
                    self.df.at[row_idx, f't{transaction_num}_type'] = trans_type.upper()
                    self.df.at[row_idx, f't{transaction_num}_date'] = date
                    self.df.at[row_idx, f't{transaction_num}_qty'] = int(quantity)
                    self.df.at[row_idx, f't{transaction_num}_price'] = price
                    self.df.at[row_idx, f't{transaction_num}_total'] = total
                    break
                transaction_num += 1

        self._save_to_csv()
        print(f"\nTransaction added successfully: {symbol} - {trans_type} {int(quantity)} shares at ${price:.2f} (Total: ${format_money(total)})")

    def _save_to_csv(self):
        """Save the current DataFrame to CSV"""
        self.df.to_csv(self.csv_file, index=False)

    def _get_current_prices(self, symbols):
        """Get current market prices for a list of symbols"""
        if not YFINANCE_AVAILABLE or self.offline_mode:
            return {}
        
        prices = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                ticker_data = ticker.history(period='1d')
                if not ticker_data.empty:
                    current_price = ticker_data['Close'].iloc[-1]
                    prices[symbol] = current_price
            except Exception:
                pass
        return prices

    def get_portfolio_summary(self):
        """Generate a summary of current portfolio positions and closed positions"""
        print(f"\n{Fore.CYAN}=== PORTFOLIO SUMMARY ==={Style.RESET_ALL}")
        print("-" * 70)
        
        if not self.offline_mode and YFINANCE_AVAILABLE:
            print(f"{Fore.YELLOW}Fetching market data...{Style.RESET_ALL}")
            current_prices = self._get_current_prices(self.df['symbol'].tolist())
        else:
            current_prices = {}

        active_positions = []
        closed_positions = []
        
        for _, row in self.df.iterrows():
            symbol = row['symbol']
            total_shares = 0
            total_pnl = 0
            
            transaction_num = 1
            while f't{transaction_num}_type' in row:
                prefix = f't{transaction_num}_'
                if row[f'{prefix}type'] != '':
                    try:
                        qty = int(row[f'{prefix}qty'])
                        if row[f'{prefix}type'] == 'BUY':
                            total_shares += qty
                        else:
                            total_shares -= qty
                        total_pnl += float(row[f'{prefix}total'])
                    except (ValueError, TypeError):
                        continue
                transaction_num += 1

            position_info = {
                'symbol': symbol,
                'shares': total_shares,
                'pnl': total_pnl
            }

            if total_shares != 0:
                if symbol in current_prices:
                    current_price = current_prices[symbol]
                    market_value = total_shares * current_price
                    position_info['market_value'] = market_value
                    position_info['current_price'] = current_price
                    # Calculate gain (market value + pnl = gain)
                    position_info['gain'] = market_value + total_pnl
                active_positions.append(position_info)
            else:
                closed_positions.append(position_info)

        # Display active positions
        print(f"\n{Fore.CYAN}=== ACTIVE POSITIONS ==={Style.RESET_ALL}")
        print("-" * 70)
        total_pnl = 0
        total_market_value = 0
        
        for pos in active_positions:
            print(f"\n{Fore.YELLOW}Stock: {pos['symbol']}{Style.RESET_ALL}")
            print(f"Current Position: {pos['shares']} shares")
            print(f"Total P&L: ${format_money(pos['pnl'])}")
            if 'market_value' in pos:
                print(f"Current Price: ${pos['current_price']:.2f}")
                print(f"Current Market Value: ${pos['market_value']:.2f}")
                print(f"Gain: ${format_money(pos['gain'], include_plus=True)}")
            print("-" * 30)
            total_pnl += pos['pnl']
            if 'market_value' in pos:
                total_market_value += pos['market_value']

        # Display closed positions
        print(f"\n{Fore.CYAN}=== CLOSED POSITIONS ==={Style.RESET_ALL}")
        print("-" * 70)
        closed_total_pnl = 0
        
        for pos in closed_positions:
            print(f"\n{Fore.YELLOW}Stock: {pos['symbol']}{Style.RESET_ALL}")
            print(f"P&L: ${format_money(pos['pnl'])}")
            print("-" * 30)
            closed_total_pnl += pos['pnl']

        # Display summary totals
        print(f"\n{Fore.CYAN}=== PORTFOLIO TOTALS ==={Style.RESET_ALL}")
        print("-" * 70)
        print(f"Active Positions P&L: ${format_money(total_pnl)}")
        if total_market_value > 0:
            print(f"Active Positions Market Value: ${total_market_value:.2f}")
        print(f"Closed Positions P&L: ${format_money(closed_total_pnl)}")
        print("-" * 70)

    def view_all_transactions(self):
        """Display all transactions in a readable format"""
        print(f"\n{Fore.CYAN}=== ALL TRANSACTIONS ==={Style.RESET_ALL}")
        
        for _, row in self.df.iterrows():
            print(f"\n{Fore.YELLOW}Stock: {row['symbol']}{Style.RESET_ALL}")
            
            transaction_num = 1
            while f't{transaction_num}_type' in row:
                prefix = f't{transaction_num}_'
                if row[f'{prefix}type'] != '':
                    try:
                        qty = int(row[f'{prefix}qty'])
                        price = float(row[f'{prefix}price'])
                        total = float(row[f'{prefix}total'])
                        print(f"Transaction {transaction_num}: {row[f'{prefix}type']} "
                              f"{qty} shares @ ${price:.2f} on {row[f'{prefix}date']} "
                              f"(Total: ${format_money(total)})")
                    except (ValueError, TypeError):
                        continue
                transaction_num += 1
            print("-" * 50)

def main():
    parser = argparse.ArgumentParser(description='Portfolio Manager')
    parser.add_argument('--offline', action='store_true', help='Run in offline mode (skip market data)')
    args = parser.parse_args()

    portfolio = PortfolioManager(offline_mode=args.offline)
    
    while True:
        print(f"\n{Fore.CYAN}=== PORTFOLIO MANAGER ==={Style.RESET_ALL}")
        print("1. Add Transaction")
        print("2. View Portfolio Summary")
        print("3. View All Transactions")
        print("4. Exit")
        
        try:
            choice = input("\nEnter your choice (1-4): ")
            
            if choice == '1':
                symbol = input("Enter stock symbol: ").upper()
                trans_type = input("Enter transaction type (buy/sell): ").upper()
                while trans_type not in ['BUY', 'SELL']:
                    trans_type = input("Please enter 'BUY' or 'SELL': ").upper()
                
                try:
                    quantity = int(input("Enter quantity: "))
                    price = float(input("Enter price per share: "))
                    date = input("Enter date (YYYY-MM-DD, press Enter for today): ").strip()
                    if date:
                        portfolio.add_transaction(symbol, trans_type, quantity, price, date)
                    else:
                        portfolio.add_transaction(symbol, trans_type, quantity, price)
                except ValueError:
                    print(f"{Fore.RED}Invalid input. Please enter numeric values for quantity and price.{Style.RESET_ALL}")
                    
            elif choice == '2':
                portfolio.get_portfolio_summary()
                
            elif choice == '3':
                portfolio.view_all_transactions()
                
            elif choice == '4':
                print(f"\n{Fore.YELLOW}Exiting Portfolio Manager. Goodbye!{Style.RESET_ALL}")
                break
                
            else:
                print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")
                
        except EOFError:
            break
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Operation cancelled by user.{Style.RESET_ALL}")
            break

if __name__ == "__main__":
    main()
