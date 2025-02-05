from flask import Flask, render_template, request, jsonify
from crypto_analyzer import CryptoAnalyzer
import ccxt

app = Flask(__name__)

def get_available_symbols():
    exchange = ccxt.binance()
    markets = exchange.load_markets()
    # Sadece USDT çiftlerini al
    symbols = [symbol for symbol in markets.keys() if symbol.endswith('/USDT')]
    return sorted(symbols)

@app.route('/')
def index():
    symbols = get_available_symbols()
    # TradingView için sembolleri Binance formatına çevir
    tv_symbols = [symbol.replace('/', '') for symbol in symbols]
    return render_template('index.html', symbols=symbols, tv_symbols=tv_symbols)

@app.route('/analyze', methods=['POST'])
def analyze():
    symbol = request.form.get('symbol')
    timeframe = request.form.get('timeframe', '1h')
    
    try:
        analyzer = CryptoAnalyzer(symbol, timeframe)
        analyzer.fetch_data()
        analyzer.calculate_indicators()
        analysis_result = analyzer.analyze_signals()
        
        # Grafiği oluştur
        fig = analyzer.create_chart()
        chart_html = fig.to_html(full_html=False)
        
        return jsonify({
            'success': True,
            'analysis': analysis_result,
            'chart': chart_html
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True) 