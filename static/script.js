$(document).ready(function() {
    $('#analyzeForm').on('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        
        // Loading durumunu göster
        $('#chartContainer').html('<div class="text-center"><div class="spinner-border" role="status"></div><p>Analiz yapılıyor...</p></div>');
        $('#analysisResult').hide();
        
        $.ajax({
            url: '/analyze',
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    // Grafiği göster
                    $('#chartContainer').html(response.chart);
                    
                    // Analiz sonuçlarını göster
                    let resultHtml = `
                        <div class="mb-3">
                            <h6>Piyasa Durumu:</h6>
                            <p>Trend: <strong class="trend-${response.analysis.support_resistance.trend.toLowerCase()}">${response.analysis.support_resistance.trend}</strong></p>
                            <p>VWAP: ${response.analysis.support_resistance.vwap.toFixed(2)}</p>
                        </div>
                        
                        <div class="mb-3">
                            <h6>Direnç Bölgeleri:</h6>
                            <ul class="list-unstyled">
                            ${response.analysis.support_resistance.resistance_zones.map(zone => `
                                <li class="zone-item resistance">
                                    <div class="zone-price">${zone.price.toFixed(2)}</div>
                                    <div class="zone-details">
                                        <span class="zone-type">${zone.type}</span>
                                        <div class="strength-bar" style="width: ${zone.strength}%"></div>
                                        <span class="strength-text">${zone.strength}% Güç</span>
                                    </div>
                                </li>
                            `).join('')}
                            </ul>
                        </div>
                        
                        <div class="current-price-indicator">
                            Güncel Fiyat: ${response.analysis.support_resistance.current_price.toFixed(2)}
                        </div>
                        
                        <div class="mb-3">
                            <h6>Destek Bölgeleri:</h6>
                            <ul class="list-unstyled">
                            ${response.analysis.support_resistance.support_zones.map(zone => `
                                <li class="zone-item support">
                                    <div class="zone-price">${zone.price.toFixed(2)}</div>
                                    <div class="zone-details">
                                        <span class="zone-type">${zone.type}</span>
                                        <div class="strength-bar" style="width: ${zone.strength}%"></div>
                                        <span class="strength-text">${zone.strength}% Güç</span>
                                    </div>
                                </li>
                            `).join('')}
                            </ul>
                        </div>
                        
                        <div class="mb-3">
                            <h6>Long Giriş Noktaları:</h6>
                            <ul class="list-unstyled">
                            ${response.analysis.entry_points.long.map(entry => `
                                <li class="entry-point">
                                    <strong>${entry.strength}</strong> - ${entry.price.toFixed(2)}
                                    <br><small>${entry.reason}</small>
                                </li>
                            `).join('')}
                            </ul>
                        </div>
                        
                        <div class="mb-3">
                            <h6>Short Giriş Noktaları:</h6>
                            <ul class="list-unstyled">
                            ${response.analysis.entry_points.short.map(entry => `
                                <li class="entry-point">
                                    <strong>${entry.strength}</strong> - ${entry.price.toFixed(2)}
                                    <br><small>${entry.reason}</small>
                                </li>
                            `).join('')}
                            </ul>
                        </div>
                        
                        <div class="mb-3">
                            <h6>İndikatör Detayları:</h6>
                            <ul class="list-unstyled">
                    `;
                    
                    for (const [indicator, data] of Object.entries(response.analysis.indicators)) {
                        resultHtml += `
                            <li class="mb-2">
                                <strong>${indicator.toUpperCase()}</strong>: 
                                <span class="signal-${data.signal === 'ALIŞ' ? 'buy' : data.signal === 'SATIŞ' ? 'sell' : 'neutral'}">${data.signal}</span>
                            </li>
                        `;
                    }
                    
                    resultHtml += `</ul></div>`;
                    
                    $('#resultContent').html(resultHtml);
                    $('#analysisResult').show();
                } else {
                    alert('Hata: ' + response.error);
                }
            },
            error: function() {
                alert('Analiz sırasında bir hata oluştu.');
            }
        });
    });
}); 