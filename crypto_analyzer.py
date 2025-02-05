import pandas as pd
import numpy as np
import ccxt
import ta
import json
import plotly.graph_objects as go
from datetime import datetime, timedelta

class CryptoAnalyzer:
    def __init__(self, symbol, timeframe='1h'):
        self.exchange = ccxt.binance()
        self.symbol = symbol
        self.timeframe = timeframe
        self.df = None
        
    def fetch_data(self):
        # Son 100 mum verisi al
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=100)
        self.df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'], unit='ms')
        
    def calculate_indicators(self):
        # RSI hesapla
        self.df['rsi'] = ta.momentum.RSIIndicator(self.df['close']).rsi()
        
        # MACD hesapla
        macd = ta.trend.MACD(self.df['close'])
        self.df['macd'] = macd.macd()
        self.df['macd_signal'] = macd.macd_signal()
        
        # Fisher Transform hesapla
        self.calculate_fisher_transform()
        
        # EMA hesapla
        self.df['ema5'] = ta.trend.EMAIndicator(self.df['close'], window=5).ema_indicator()
        self.df['ema8'] = ta.trend.EMAIndicator(self.df['close'], window=8).ema_indicator()
        self.df['ema13'] = ta.trend.EMAIndicator(self.df['close'], window=13).ema_indicator()
        
        # Pivot noktaları hesapla
        self.calculate_pivot_points()
        
    def calculate_fisher_transform(self, period=10):
        high = self.df['high'].rolling(window=period).max()
        low = self.df['low'].rolling(window=period).min()
        mid = (self.df['high'] + self.df['low']) / 2
        value = 0.33 * 2 * ((mid - low) / (high - low) - 0.5) + 0.67
        self.df['fisher'] = 0.5 * np.log((1 + value) / (1 - value))
        
    def calculate_pivot_points(self):
        self.df['pivot'] = (self.df['high'] + self.df['low'] + self.df['close']) / 3
        self.df['r1'] = 2 * self.df['pivot'] - self.df['low']
        self.df['s1'] = 2 * self.df['pivot'] - self.df['high']
        
    def calculate_support_resistance(self):
        try:
            # Fiyat ve hacim verileri
            close = self.df['close'].iloc[-1]
            high = self.df['high']
            low = self.df['low']
            volume = self.df['volume']
            
            # Major seviyeleri hesapla (son 50 mum için)
            major_window = 50
            major_high = high.rolling(window=major_window).max().iloc[-1]
            major_low = low.rolling(window=major_window).min().iloc[-1]
            
            # Minör 1 seviyeleri (son 20 mum için)
            minor_window1 = 20
            minor_high1 = high.rolling(window=minor_window1).max().iloc[-1]
            minor_low1 = low.rolling(window=minor_window1).min().iloc[-1]
            
            # Minör 2 seviyeleri (son 10 mum için)
            minor_window2 = 10
            minor_high2 = high.rolling(window=minor_window2).max().iloc[-1]
            minor_low2 = low.rolling(window=minor_window2).min().iloc[-1]
            
            # Fiyat kümelenmeleri
            price_clusters = self.find_price_clusters(threshold=0.001)
            
            # Destek ve direnç bölgelerini oluştur
            resistance_zones = []
            support_zones = []
            
            # Major seviyeler için test sayısı ve hacim kontrolü
            for price in [major_high, minor_high1, minor_high2]:
                strength = self.calculate_zone_strength(price, 'resistance', volume)
                nearest_cluster = self.find_nearest_cluster(price, price_clusters)
                
                if nearest_cluster:
                    price = nearest_cluster  # Kümelenme varsa fiyatı güncelle
                    strength += 10  # Kümelenme bonusu
                
                zone_type = 'Major' if price == major_high else 'Minor 1' if price == minor_high1 else 'Minor 2'
                
                resistance_zones.append({
                    'price': price,
                    'strength': strength,
                    'type': zone_type,
                    'tests': self.count_price_tests(price, 'resistance')
                })
            
            # Benzer şekilde destek seviyeleri için
            for price in [major_low, minor_low1, minor_low2]:
                strength = self.calculate_zone_strength(price, 'support', volume)
                nearest_cluster = self.find_nearest_cluster(price, price_clusters)
                
                if nearest_cluster:
                    price = nearest_cluster
                    strength += 10
                
                zone_type = 'Major' if price == major_low else 'Minor 1' if price == minor_low1 else 'Minor 2'
                
                support_zones.append({
                    'price': price,
                    'strength': strength,
                    'type': zone_type,
                    'tests': self.count_price_tests(price, 'support')
                })
            
            # VWAP ve trend hesaplama
            vwap = (self.df['close'] * self.df['volume']).sum() / self.df['volume'].sum()
            ema5 = self.df['ema5'].iloc[-1]
            ema13 = self.df['ema13'].iloc[-1]
            trend = self.determine_trend(ema5, ema13)
            
            return {
                'current_price': close,
                'vwap': vwap,
                'resistance_zones': resistance_zones,
                'support_zones': support_zones,
                'trend': trend,
                'price_clusters': price_clusters
            }
            
        except Exception as e:
            print(f"Error in calculate_support_resistance: {str(e)}")
            return self.get_default_levels()

    def count_price_tests(self, price, zone_type, threshold=0.002):
        """Fiyat seviyesinin kaç kez test edildiğini say"""
        tests = 0
        if zone_type == 'resistance':
            for high in self.df['high']:
                if abs(high - price) / price < threshold:
                    tests += 1
        else:
            for low in self.df['low']:
                if abs(low - price) / price < threshold:
                    tests += 1
        return tests

    def determine_trend(self, ema5, ema13):
        """Trend yönünü belirle"""
        if ema5 > ema13 * 1.02:  # %2 fark için güçlü trend
            return 'Strong Bullish'
        elif ema5 > ema13:
            return 'Bullish'
        elif ema5 < ema13 * 0.98:  # %2 fark için güçlü trend
            return 'Strong Bearish'
        elif ema5 < ema13:
            return 'Bearish'
        else:
            return 'Neutral'

    def get_default_levels(self):
        """Varsayılan seviyeleri döndür"""
        close = self.df['close'].iloc[-1]
        return {
            'current_price': close,
            'vwap': close,
            'resistance_zones': [
                {
                    'price': close * 1.02,
                    'strength': 50,
                    'type': 'Default Resistance'
                }
            ],
            'support_zones': [
                {
                    'price': close * 0.98,
                    'strength': 50,
                    'type': 'Default Support'
                }
            ],
            'trend': 'Neutral'
        }

    def find_price_clusters(self, threshold=0.002):
        """Fiyat kümelenmelerini bul"""
        prices = np.concatenate([self.df['high'].values, self.df['low'].values])
        prices = np.sort(prices)
        
        clusters = []
        current_cluster = [prices[0]]
        
        for i in range(1, len(prices)):
            if (prices[i] - prices[i-1]) / prices[i-1] <= threshold:
                current_cluster.append(prices[i])
            else:
                if len(current_cluster) > 3:  # En az 3 fiyat noktası olan kümelenmeleri al
                    clusters.append(np.mean(current_cluster))
                current_cluster = [prices[i]]
        
        if len(current_cluster) > 3:
            clusters.append(np.mean(current_cluster))
        
        return clusters

    def find_nearest_cluster(self, price, clusters):
        """Verilen fiyata en yakın kümelenmeyi bul"""
        if not clusters:
            return None
        
        distances = [abs(cluster - price) for cluster in clusters]
        min_distance_idx = np.argmin(distances)
        
        # Eğer en yakın kümelenme çok uzaksa None döndür
        if distances[min_distance_idx] / price > 0.05:  # %5'ten fazla uzaksa
            return None
        
        return clusters[min_distance_idx]

    def calculate_zone_strength(self, price, zone_type, volume=None):
        """Bölgenin gücünü hesapla"""
        strength = 0
        
        # Fiyat testlerini say
        tests = 0
        if zone_type == 'resistance':
            tests = sum(1 for high in self.df['high'] if abs(high - price) / price < 0.005)
        else:
            tests = sum(1 for low in self.df['low'] if abs(low - price) / price < 0.005)
        
        # Test sayısına göre puan ver
        strength += min(tests * 10, 50)  # Maximum 50 puan
        
        # Hacim desteğini kontrol et
        if volume:
            volume_at_level = self.df.loc[
                (self.df['high'] >= price * 0.995) & 
                (self.df['low'] <= price * 1.005), 
                'volume'
            ].mean()
            
            avg_volume = self.df['volume'].mean()
            if volume_at_level > avg_volume * 1.5:
                strength += 30
            elif volume_at_level > avg_volume:
                strength += 15
        
        # RSI ve MACD durumunu kontrol et
        last_rsi = self.df['rsi'].iloc[-1]
        if zone_type == 'resistance' and last_rsi > 70:
            strength += 20
        elif zone_type == 'support' and last_rsi < 30:
            strength += 20
        
        return min(strength, 100)  # Maximum 100 puan

    def analyze_entry_points(self):
        levels = self.calculate_support_resistance()
        last_close = levels['current_price']
        
        # RSI ve MACD durumlarını al
        last_rsi = self.df['rsi'].iloc[-1]
        last_macd = self.df['macd'].iloc[-1]
        last_macd_signal = self.df['macd_signal'].iloc[-1]
        
        # Long giriş noktaları analizi
        long_entries = []
        
        # Destek bölgeleri için hata kontrolü
        support_zones = levels.get('support_zones', [])
        resistance_zones = levels.get('resistance_zones', [])
        
        # En az bir destek/direnç bölgesi olduğundan emin ol
        if len(support_zones) > 0:
            if last_close <= support_zones[0]['price'] and last_rsi < 40:
                long_entries.append({
                    'price': support_zones[0]['price'],
                    'strength': support_zones[0]['strength'],
                    'reason': f"Support Zone {support_zones[0]['type']}"
                })
        
        if len(support_zones) > 1:
            if last_close <= support_zones[1]['price'] and last_rsi < 30:
                long_entries.append({
                    'price': support_zones[1]['price'],
                    'strength': support_zones[1]['strength'],
                    'reason': f"Support Zone {support_zones[1]['type']}"
                })
        
        if len(support_zones) > 2:
            if last_close <= support_zones[2]['price'] and last_rsi < 30:
                long_entries.append({
                    'price': support_zones[2]['price'],
                    'strength': support_zones[2]['strength'],
                    'reason': f"Support Zone {support_zones[2]['type']}"
                })
        
        # Short giriş noktaları analizi
        short_entries = []
        
        if len(resistance_zones) > 0:
            if last_close >= resistance_zones[0]['price'] and last_rsi > 60:
                short_entries.append({
                    'price': resistance_zones[0]['price'],
                    'strength': resistance_zones[0]['strength'],
                    'reason': f"Resistance Zone {resistance_zones[0]['type']}"
                })
        
        if len(resistance_zones) > 1:
            if last_close >= resistance_zones[1]['price'] and last_rsi > 70:
                short_entries.append({
                    'price': resistance_zones[1]['price'],
                    'strength': resistance_zones[1]['strength'],
                    'reason': f"Resistance Zone {resistance_zones[1]['type']}"
                })
        
        if len(resistance_zones) > 2:
            if last_close >= resistance_zones[2]['price'] and last_rsi > 70:
                short_entries.append({
                    'price': resistance_zones[2]['price'],
                    'strength': resistance_zones[2]['strength'],
                    'reason': f"Resistance Zone {resistance_zones[2]['type']}"
                })
        
        # Eğer hiç bölge bulunamazsa varsayılan değerler ekle
        if not resistance_zones:
            resistance_zones = [{
                'price': last_close * 1.02,
                'strength': 50,
                'type': 'Default Resistance'
            }]
        
        if not support_zones:
            support_zones = [{
                'price': last_close * 0.98,
                'strength': 50,
                'type': 'Default Support'
            }]
        
        return {
            'support_resistance': {
                'current_price': last_close,
                'vwap': levels.get('vwap', last_close),
                'resistance_zones': resistance_zones,
                'support_zones': support_zones,
                'trend': levels.get('trend', 'Neutral')
            },
            'long_entries': long_entries,
            'short_entries': short_entries
        }

    def analyze_signals(self):
        # Mevcut analiz sonuçlarını al
        signals = {
            'rsi': self.analyze_rsi(),
            'macd': self.analyze_macd(),
            'ema': self.analyze_ema(),
            'fisher': self.analyze_fisher(),
            'pivot': self.analyze_pivot_points()
        }
        
        # Destek/direnç ve giriş noktaları analizini ekle
        entry_analysis = self.analyze_entry_points()
        
        positive_signals = sum(1 for signal in signals.values() if signal['signal'] == 'ALIŞ')
        negative_signals = sum(1 for signal in signals.values() if signal['signal'] == 'SATIŞ')
        
        overall_signal = 'ALIŞ' if positive_signals > negative_signals else 'SATIŞ'
        
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': self.symbol,
            'indicators': signals,
            'support_resistance': entry_analysis['support_resistance'],
            'entry_points': {
                'long': entry_analysis['long_entries'],
                'short': entry_analysis['short_entries']
            },
            'overall_signal': overall_signal,
            'confidence_score': abs(positive_signals - negative_signals) / len(signals) * 100
        }
    
    def analyze_rsi(self):
        last_rsi = self.df['rsi'].iloc[-1]
        signal = 'ALIŞ' if last_rsi < 30 else 'SATIŞ' if last_rsi > 70 else 'NÖTR'
        return {'value': last_rsi, 'signal': signal}
    
    def analyze_macd(self):
        last_macd = self.df['macd'].iloc[-1]
        last_signal = self.df['macd_signal'].iloc[-1]
        signal = 'ALIŞ' if last_macd > last_signal else 'SATIŞ'
        return {'value': last_macd, 'signal': signal}
    
    def analyze_ema(self):
        last_ema5 = self.df['ema5'].iloc[-1]
        last_ema8 = self.df['ema8'].iloc[-1]
        last_ema13 = self.df['ema13'].iloc[-1]
        
        signal = 'ALIŞ' if last_ema5 > last_ema8 > last_ema13 else 'SATIŞ'
        return {'values': {'ema5': last_ema5, 'ema8': last_ema8, 'ema13': last_ema13}, 'signal': signal}
    
    def analyze_fisher(self):
        last_fisher = self.df['fisher'].iloc[-1]
        signal = 'ALIŞ' if last_fisher > 0 else 'SATIŞ'
        return {'value': last_fisher, 'signal': signal}
    
    def analyze_pivot_points(self):
        last_close = self.df['close'].iloc[-1]
        last_r1 = self.df['r1'].iloc[-1]
        last_s1 = self.df['s1'].iloc[-1]
        
        signal = 'ALIŞ' if last_close < last_s1 else 'SATIŞ' if last_close > last_r1 else 'NÖTR'
        return {'values': {'r1': last_r1, 's1': last_s1}, 'signal': signal}
    
    def create_chart(self):
        fig = go.Figure()
        
        # Mum grafiği
        fig.add_trace(go.Candlestick(
            x=self.df['timestamp'],
            open=self.df['open'],
            high=self.df['high'],
            low=self.df['low'],
            close=self.df['close'],
            name='OHLC'
        ))
        
        # EMA çizgileri
        fig.add_trace(go.Scatter(x=self.df['timestamp'], y=self.df['ema5'], name='EMA5'))
        fig.add_trace(go.Scatter(x=self.df['timestamp'], y=self.df['ema8'], name='EMA8'))
        fig.add_trace(go.Scatter(x=self.df['timestamp'], y=self.df['ema13'], name='EMA13'))
        
        # Destek ve direnç çizgileri
        levels = self.calculate_support_resistance()
        
        # Direnç bölgeleri için çizgiler
        for zone in levels['resistance_zones']:
            fig.add_hline(
                y=zone['price'],
                line_dash="dash",
                annotation_text=f"Direnç ({zone['type']})",
                line_color="red",
                opacity=zone['strength']/100
            )
        
        # Destek bölgeleri için çizgiler
        for zone in levels['support_zones']:
            fig.add_hline(
                y=zone['price'],
                line_dash="dash",
                annotation_text=f"Destek ({zone['type']})",
                line_color="green",
                opacity=zone['strength']/100
            )
        
        # VWAP çizgisi
        if 'vwap' in levels:
            fig.add_hline(
                y=levels['vwap'],
                line_dash="solid",
                annotation_text="VWAP",
                line_color="purple"
            )
        
        fig.update_layout(
            title=f'{self.symbol} Teknik Analiz Grafiği ({levels["trend"]})',
            yaxis_title='Fiyat',
            xaxis_title='Tarih',
            height=800,
            template='plotly_dark'  # Koyu tema
        )
        
        return fig 