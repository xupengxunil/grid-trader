export function analyzeStockSuitability(kData) {
  if (!kData || kData.length === 0) return false;
  const closePrices = kData.map(d => parseFloat(d.close));
  const highs = kData.map(d => parseFloat(d.high));
  const lows = kData.map(d => parseFloat(d.low));
  
  const currentPx = closePrices[closePrices.length - 1];

  const ma5 = closePrices.slice(-5).reduce((a,b)=>a+b,0) / Math.min(5, closePrices.length);
  const ma10 = closePrices.slice(-10).reduce((a,b)=>a+b,0) / Math.min(10, closePrices.length);
  const ma30 = closePrices.slice(-30).reduce((a,b)=>a+b,0) / Math.min(30, closePrices.length);

  const pastClose30 = closePrices.slice(-40, -10);
  const ma30_past = pastClose30.length > 0 ? (pastClose30.reduce((a,b)=>a+b,0) / Math.min(30, pastClose30.length)) : ma30;
  const ma30_slope = ma30_past > 0 ? ((ma30 - ma30_past) / ma30_past) * 100 : 0;
  
  const ma_max = Math.max(ma5, ma10, ma30);
  const ma_min = Math.min(ma5, ma10, ma30);
  const ma_dispersion = ma_min > 0 ? ((ma_max - ma_min) / ma_min) * 100 : 0;

  let trSum = 0;
  let validDays = 0;
  const atrRange = 14;
  
  for (let i = 0; i < kData.length; i++) {
    if (i > 0 && i >= kData.length - atrRange) {
      const todayHigh = parseFloat(kData[i].high);
      const todayLow = parseFloat(kData[i].low);
      const preClose = parseFloat(kData[i - 1].close);
      
      const tr1 = todayHigh - todayLow;
      const tr2 = Math.abs(todayHigh - preClose);
      const tr3 = Math.abs(todayLow - preClose);
      trSum += Math.max(tr1, tr2, tr3);
      validDays++;
    }
  }

  let atrRatio = 0;
  if (validDays > 0 && currentPx > 0) {
    const atr = trSum / validDays;
    atrRatio = (atr / currentPx) * 100;
  }

  // MACD calculation
  let ema12 = closePrices[0];
  let ema26 = closePrices[0];
  let dea = 0;
  
  let macdDif = [];
  let macdDea = [];
  let macdHist = [];
  
  for (let i = 0; i < closePrices.length; i++) {
    const c = closePrices[i];
    if (i === 0) {
      macdDif.push(0);
      macdDea.push(0);
      macdHist.push(0);
    } else {
      ema12 = c * (2/13) + ema12 * (11/13);
      ema26 = c * (2/27) + ema26 * (25/27);
      const dif = ema12 - ema26;
      dea = dif * (2/10) + dea * (8/10);
      const hist = (dif - dea) * 2;
      macdDif.push(dif);
      macdDea.push(dea);
      macdHist.push(hist);
    }
  }
  
  const lastDif = macdDif[macdDif.length - 1] || 0;
  const lastDea = macdDea[macdDea.length - 1] || 0;
  const lastHist = macdHist[macdHist.length - 1] || 0;
  const prevHist = macdHist[macdHist.length - 2] || 0;

  let macdPassed = true;
  if (lastDif < lastDea && lastHist < prevHist && lastHist < 0) {
    macdPassed = false;
  } else if (lastDif < 0 && lastDea > 0 && lastDif < lastDea) {
    macdPassed = false;
  }

  // BOLL calculation
  let bollPassed = true;
  if (closePrices.length >= 20) {
    const recent20 = closePrices.slice(-20);
    const bolMB = recent20.reduce((a, b) => a + b, 0) / 20;
    const bolMD = Math.sqrt(recent20.reduce((a, b) => a + Math.pow(b - bolMB, 2), 0) / 20);
    const bolUP = bolMB + 2 * bolMD;
    const bolDN = bolMB - 2 * bolMD;
    
    const bollPosition = (currentPx - bolDN) / (bolUP - bolDN);
    
    if (bollPosition > 0.9) {
      bollPassed = false;
    }
  }

  const conditions = [
    currentPx > ma30 * 0.95 && ma30_slope > -2.0, // 长期下跌风险
    atrRatio > 1.5,                               // 震荡幅度达标
    currentPx <= ma30 * 1.15,                     // 非主升浪/单边上涨
    ma_dispersion < 5.0,                          // 均线乖离度
    bollPassed,                                   // 布林带通道(BOLL)
    macdPassed                                    // MACD多空趋势
  ];

  return conditions.every(c => c);
}
