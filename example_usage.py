from crypto_analyzer import CryptoAnalyzer
import json

analyzer = CryptoAnalyzer('BTC/USDT')
analyzer.fetch_data()
analyzer.calculate_indicators()
analysis_result = analyzer.analyze_signals()

# Sonuçları JSON formatında yazdır
print(json.dumps(analysis_result, indent=2, ensure_ascii=False))

# Grafik oluştur ve kaydet
fig = analyzer.create_chart()
fig.write_html('crypto_analysis.html') 