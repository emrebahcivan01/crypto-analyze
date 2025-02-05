// API endpoint'i güncelle
const API_URL = '/.netlify/functions/analyze';

// AJAX çağrısını güncelle
$.ajax({
    url: API_URL,
    method: 'POST',
    data: JSON.stringify({
        symbol: $('#symbol').val(),
        timeframe: $('#timeframe').val()
    }),
    contentType: 'application/json',
    // ... geri kalan kod aynı
}); 