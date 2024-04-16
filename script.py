import mysql.connector
import requests
from bs4 import BeautifulSoup
import time
import schedule
from flask import Flask, jsonify, request, abort
import threading
from mysql.connector import pooling

app = Flask(__name__)
dbconfig = {
    "host": "localhost",
    "user": "root",
    "password": "123@abc",
    "database": "stocks"
}
tickers = [
        'ADANIENT', 'ADANIPORTS', 'APOLLOHOSP', 'ASIANPAINT', 'AXISBANK', 
        'BAJAJ-AUTO', 'BAJFINANCE', 'BAJAJFINSV', 'BPCL', 'BHARTIARTL', 
        'BRITANNIA', 'CIPLA', 'COALINDIA', 'DIVISLAB', 'DRREDDY', 
        'EICHERMOT', 'GRASIM', 'HCLTECH', 'HDFCBANK', 'HDFCLIFE', 
        'HEROMOTOCO', 'HINDALCO', 'HINDUNILVR', 'ICICIBANK', 'ITC', 
        'INDUSINDBK', 'INFY', 'JSWSTEEL', 'KOTAKBANK', 'LTIM', 
        'LT', 'M&M', 'MARUTI', 'NTPC', 'NESTLEIND', 
        'ONGC', 'POWERGRID', 'RELIANCE', 'SBILIFE', 'SBIN', 
        'SUNPHARMA', 'TCS', 'TATACONSUM', 'TATAMOTORS', 'TATASTEEL', 
        'TECHM', 'TITAN', 'UPL', 'ULTRACEMCO', 'WIPRO'
]

cnx_pool = pooling.MySQLConnectionPool(pool_name="mypool",
                                       pool_size=5,
                                       **dbconfig)

@app.route('/stock-data', methods=['GET'])
def get_data():
    page_no = request.args.get('page_no')
    stock_name = request.args.get('stock_name')
    cnx = cnx_pool.get_connection()
    cursor0 = cnx.cursor()
    cursor0.execute("USE stocks")
    try:
        if(page_no != None and int(page_no) < 6):
            cursor0.execute("SELECT * FROM StockPrices limit %s offset %s", ((int(10)), (int(page_no)-1) * 10))
            rows = cursor0.fetchall()
            cursor0.close()
            cnx.close()
            fetched_data = []   
            for name, price in rows:
                fetched_data.append({"stock" : name, "price" : price })

            if fetched_data is None:
                raise ValueError(f"Page No {page_no} does not exist")

            return jsonify({'data' : fetched_data})
        elif(stock_name != None):
            cursor0.execute(f'SELECT * FROM StockPrices WHERE ticker = "{stock_name}"')
            data = cursor0.fetchone()
            cursor0.close()
            cnx.close()

            if data is None:
                raise ValueError(f"Stock {stock_name} price not found")
            
            return jsonify({'data' : {"stock" : data[0], "price" : data[1]}})
    except ValueError as v:
        return jsonify({'error' : str(v)}), 400
    except Exception as e:
        return jsonify({'error' : str(e)}), 500

def fetch_stock_price():
    stock_prices = []

    for ticker in tickers:
        # print(ticker)
        url = f'https://www.google.com/finance/quote/{ticker}:NSE'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        class1 = 'YMlKec fxKbKc'
        stock_price = float(soup.find(class_=class1).text.strip()[1:].replace(",", ""))
        # print("stock price of %s is %s", (ticker, stock_price))
        stock_prices.append(stock_price)

    cnx = cnx_pool.get_connection()
    cursor1 = cnx.cursor()
    cursor1.execute("USE stocks")
    for i in range(len(tickers)):
        cursor1.execute("UPDATE StockPrices SET price = %.2f WHERE ticker = '%s'" % (stock_prices[i], tickers[i]))
    cnx.commit()
    cursor1.close()
    cnx.close()

def start_scheduler():
    print("fetching and updating")
    schedule.every(5).seconds.do(fetch_stock_price)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    scheduler_thread = threading.Thread(target=start_scheduler)
    scheduler_thread.start()
    app.run(debug=True)