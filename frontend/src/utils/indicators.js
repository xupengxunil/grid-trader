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

export function calculateMACD(closePrices) {
  let ema12 = closePrices[0];
  let ema26 = closePrices[0];
  let dea = 0;
  let macd = [];
  
  for (let i = 0; i < closePrices.length; i++) {
    const c = closePrices[i];
    if (i === 0) {
      macd.push({ dif: 0, dea: 0, hist: 0 });
    } else {
      ema12 = c * (2/13) + ema12 * (11/13);
      ema26 = c * (2/27) + ema26 * (25/27);
      const dif = ema12 - ema26;
      dea = dif * (2/10) + dea * (8/10);
      const hist = (dif - dea) * 2;
      macd.push({ dif, dea, hist });
    }
  }
  return macd;
}

export function calculateKDJ(kData) {
  let kdj = [];
  let k = 50, d = 50;
  const period = 9;

  for (let i = 0; i < kData.length; i++) {
    if (i < period - 1) {
      kdj.push({ k: 50, d: 50, j: 50 });
      continue;
    }
    const recent = kData.slice(i - period + 1, i + 1);
    const lowPx = Math.min(...recent.map(r => parseFloat(r.low)));
    const highPx = Math.max(...recent.map(r => parseFloat(r.high)));
    const c = parseFloat(kData[i].close);
    
    let rsv = 50;
    if (highPx !== lowPx) {
      rsv = ((c - lowPx) / (highPx - lowPx)) * 100;
    }
    
    k = (2/3) * k + (1/3) * rsv;
    d = (2/3) * d + (1/3) * k;
    const j = 3 * k - 2 * d;
    kdj.push({ k, d, j });
  }
  return kdj;
}

export function calculateBOLL(closePrices) {
  let boll = [];
  const period = 20;
  for (let i = 0; i < closePrices.length; i++) {
    if (i < period - 1) {
      boll.push({ mb: null, up: null, dn: null });
      continue;
    }
    const recent = closePrices.slice(i - period + 1, i + 1);
    const mb = recent.reduce((a, b) => a + b, 0) / period;
    const md = Math.sqrt(recent.reduce((a, b) => a + Math.pow(b - mb, 2), 0) / period);
    boll.push({
      mb: mb,
      up: mb + 2 * md,
      dn: mb - 2 * md
    });
  }
  return boll;
}

export function analyzeSignals(klineData) {
  const signals = {
      score: 0,
      tags: [],
      macdRaw: {},
      kdjRaw: {},
      bollRaw: {}
  };

  if (!klineData || klineData.length < 20) return signals;

  const closePrices = klineData.map(d => parseFloat(d.close));
  const macdData = calculateMACD(closePrices);
  const kdjData = calculateKDJ(klineData);
  const bollData = calculateBOLL(closePrices);

  const lastIdx = klineData.length - 1;
  const prevIdx = lastIdx - 1;
  const currentPrice = closePrices[lastIdx];

  const lastMacd = macdData[lastIdx];
  const prevMacd = macdData[prevIdx];
  signals.macdRaw = lastMacd;
  
  if (prevMacd.dif <= prevMacd.dea && lastMacd.dif > lastMacd.dea) {
      signals.tags.push({ text: 'MACD金叉', type: 'success' }); // 绿代表利好 
      signals.score += 2;
  } else if (lastMacd.hist < 0 && lastMacd.hist > prevMacd.hist) {
      signals.tags.push({ text: 'MACD绿缩短', type: 'warning' });
      signals.score += 1;
  } else if (prevMacd.dif >= prevMacd.dea && lastMacd.dif < lastMacd.dea) {
      signals.tags.push({ text: 'MACD死叉', type: 'danger' }); // 红代表风险
      signals.score -= 2;
  }

  const lastKdj = kdjData[lastIdx];
  signals.kdjRaw = lastKdj;
  if (lastKdj.j < 0 || (lastKdj.k < 20 && lastKdj.d < 20)) {
      signals.tags.push({ text: 'KDJ超卖', type: 'success' });
      signals.score += 2;
  } else if (lastKdj.j > 100 || (lastKdj.k > 80 && lastKdj.d > 80)) {
      signals.tags.push({ text: 'KDJ超买', type: 'danger' });
      signals.score -= 2;
  }

  const lastBoll = bollData[lastIdx];
  signals.bollRaw = lastBoll;
  if (lastBoll.dn && currentPrice <= lastBoll.dn * 1.01) {
      signals.tags.push({ text: '触及布林下轨', type: 'success' });
      signals.score += 2;
  } else if (lastBoll.up && currentPrice >= lastBoll.up * 0.99) {
      signals.tags.push({ text: '触及布林上轨', type: 'danger' });
      signals.score -= 1;
  }

  return signals;
}
