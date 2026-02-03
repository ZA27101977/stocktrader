<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QUANTA PRO | Real-Time AI Terminal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://unpkg.com/lightweight-charts@4.1.1/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Assistant:wght@300;400;600;700&display=swap');
        
        :root {
            --bg-main: #020408;
            --bg-card: #0d1117;
            --accent-blue: #3b82f6;
            --border: rgba(255, 255, 255, 0.08);
        }

        body {
            background-color: var(--bg-main);
            color: #e6edf3;
            font-family: 'Inter', sans-serif;
            margin: 0;
            overflow: hidden;
        }

        .hebrew { font-family: 'Assistant', sans-serif; direction: rtl; }
        
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 320px;
            grid-template-rows: 64px 80px 1fr 32px;
            height: 100vh;
        }

        .panel { border: 1px solid var(--border); background: var(--bg-main); overflow: hidden; }
        .header { grid-column: 1 / -1; display: flex; align-items: center; justify-content: space-between; padding: 0 24px; background: #0d1117; }
        .ticker-bar { grid-column: 1 / 2; display: flex; align-items: center; gap: 32px; padding: 0 24px; background: #06090f; }
        .watchlist { grid-row: 2 / 4; grid-column: 2; border-left: 2px solid var(--border); }
        .chart-area { grid-row: 3 / 4; grid-column: 1; position: relative; }
        
        .btn-tf {
            padding: 4px 12px; font-size: 11px; font-weight: 700; border-radius: 4px;
            color: #8b949e; transition: 0.2s;
        }
        .btn-tf.active { background: var(--accent-blue); color: white; }

        .ai-card {
            position: absolute; bottom: 24px; left: 24px; right: 24px;
            background: rgba(13, 17, 23, 0.85); backdrop-filter: blur(12px);
            border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 16px;
            padding: 20px; z-index: 50; display: flex; justify-content: space-between; align-items: center;
        }

        .status-badge {
            font-size: 10px; font-weight: bold; padding: 4px 10px; border-radius: 99px;
        }
    </style>
</head>
<body>
    <div id="root"></div>

    <script type="text/babel">
        const { useState, useEffect, useRef, useCallback } = React;

        const API_KEY_STOCK = "GNYJ6HBVJV6Z8TVS"; 
        const API_KEY_GEMINI = ""; 

        const TIMEFRAMES = [
            { id: '1D', func: 'TIME_SERIES_INTRADAY', interval: '5min', label: '1 יום' },
            { id: '1W', func: 'TIME_SERIES_DAILY', limit: 7, label: '1 שבוע' },
            { id: '1M', func: 'TIME_SERIES_DAILY', limit: 30, label: '1 חודש' },
            { id: '1Y', func: 'TIME_SERIES_WEEKLY', limit: 52, label: '1 שנה' }
        ];

        // Persistent cache to avoid repeated network requests
        const marketCache = new Map();

        const App = () => {
            const [ticker, setTicker] = useState('NVDA');
            const [tf, setTf] = useState(TIMEFRAMES[0]);
            const [stats, setStats] = useState({ price: '0.00', change: '0.00', pct: '0.00%' });
            const [aiResponse, setAiResponse] = useState(null);
            const [loading, setLoading] = useState(false);
            const [isSimulated, setIsSimulated] = useState(false);
            
            const chartRef = useRef(null);
            const seriesRef = useRef(null);
            const chartInstance = useRef(null);
            const lastFetchRef = useRef(""); // Track last ticker+tf combination

            const generateMockData = (timeframe, lastPrice = 200) => {
                const mock = [];
                let p = parseFloat(lastPrice) || 200;
                let now = new Date();
                const count = 100;
                for (let i = 0; i < count; i++) {
                    const open = p + (Math.random() - 0.5) * (p * 0.01);
                    const close = open + (Math.random() - 0.5) * (p * 0.008);
                    mock.push({
                        time: timeframe.id === '1D' ? Math.floor(now.getTime() / 1000) - (count - i) * 300 : new Date(now.getTime() - (count-i)*86400000).toISOString().split('T')[0],
                        open, high: Math.max(open, close) + (p * 0.003), low: Math.min(open, close) - (p * 0.003), close
                    });
                    p = close;
                }
                return mock;
            };

            const askGemini = async (symbol, price, pct) => {
                if (!API_KEY_GEMINI) {
                    setAiResponse({ rec: "HOLD", score: 55, insight: "מנתח נתונים טכניים עבור " + symbol });
                    return;
                }
                const prompt = `Analyze ${symbol} at $${price} (${pct}%). Return JSON: {"rec": "BUY/SELL/HOLD", "score": 0-100, "insight": "Hebrew text"}`;
                try {
                    const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${API_KEY_GEMINI}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            contents: [{ parts: [{ text: prompt }] }],
                            generationConfig: { responseMimeType: "application/json" }
                        })
                    });
                    const result = await res.json();
                    setAiResponse(JSON.parse(result.candidates[0].content.parts[0].text));
                } catch (e) {
                    setAiResponse({ rec: "HOLD", score: 50, insight: "ממתין לתובנות בינה מלאכותית..." });
                }
            };

            const updateChartData = useCallback(async (symbol, timeframe) => {
                const comboKey = `${symbol}-${timeframe.id}`;
                if (lastFetchRef.current === comboKey) return;
                lastFetchRef.current = comboKey;

                setLoading(true);
                
                // Check Cache
                if (marketCache.has(comboKey)) {
                    const cached = marketCache.get(comboKey);
                    seriesRef.current.setData(cached.points);
                    setStats(cached.stats);
                    setIsSimulated(cached.simulated);
                    setLoading(false);
                    askGemini(symbol, cached.stats.price, cached.stats.pct);
                    return;
                }

                try {
                    let url = `https://www.alphavantage.co/query?function=${timeframe.func}&symbol=${symbol}&apikey=${API_KEY_STOCK}`;
                    if (timeframe.id === '1D') url += `&interval=${timeframe.interval}`;

                    const res = await fetch(url);
                    const raw = await res.json();
                    
                    const keyMap = {
                        '1D': "Time Series (5min)",
                        '1W': "Time Series (Daily)",
                        '1M': "Time Series (Daily)",
                        '1Y': "Weekly Time Series"
                    };

                    const timeSeries = raw[keyMap[timeframe.id]];
                    
                    if (!timeSeries) {
                        // Silent fail - switch to simulation
                        const mock = generateMockData(timeframe, 150);
                        seriesRef.current.setData(mock);
                        const latest = mock[mock.length-1];
                        const diff = (latest.close - mock[mock.length-2].close).toFixed(2);
                        const newStats = { price: latest.close.toFixed(2), change: diff, pct: 'Simulated' };
                        setStats(newStats);
                        setIsSimulated(true);
                        marketCache.set(comboKey, { points: mock, stats: newStats, simulated: true });
                    } else {
                        const formatted = Object.entries(timeSeries).map(([time, v]) => ({
                            time: timeframe.id === '1D' ? Math.floor(new Date(time).getTime() / 1000) : time,
                            open: parseFloat(v["1. open"]),
                            high: parseFloat(v["2. high"]),
                            low: parseFloat(v["3. low"]),
                            close: parseFloat(v["4. close"]),
                        })).reverse();

                        const finalData = timeframe.limit ? formatted.slice(-timeframe.limit) : formatted;
                        seriesRef.current.setData(finalData);
                        
                        const latest = finalData[finalData.length - 1];
                        const prev = finalData[finalData.length - 2] || latest;
                        const diff = (latest.close - prev.close).toFixed(2);
                        const pct = ((diff / prev.close) * 100).toFixed(2);
                        const newStats = { price: latest.close.toFixed(2), change: diff, pct: (diff >= 0 ? '+' : '') + pct + '%' };
                        
                        setStats(newStats);
                        setIsSimulated(false);
                        marketCache.set(comboKey, { points: finalData, stats: newStats, simulated: false });
                        askGemini(symbol, newStats.price, newStats.pct);
                    }
                } catch (err) {
                    console.error("Fetch error, using fallback");
                    setIsSimulated(true);
                } finally {
                    setLoading(false);
                    chartInstance.current.timeScale().fitContent();
                }
            }, []);

            useEffect(() => {
                // Initial Chart Setup
                const chart = LightweightCharts.createChart(chartRef.current, {
                    layout: { background: { color: '#020408' }, textColor: '#8b949e' },
                    grid: { vertLines: { color: '#161b22' }, horzLines: { color: '#161b22' } },
                    rightPriceScale: { borderColor: '#30363d' },
                    timeScale: { borderColor: '#30363d', timeVisible: true },
                });
                const candleSeries = chart.addCandlestickSeries({
                    upColor: '#238636', downColor: '#da3633', borderVisible: false, wickUpColor: '#238636', wickDownColor: '#da3633'
                });
                
                chartInstance.current = chart;
                seriesRef.current = candleSeries;

                updateChartData(ticker, tf);

                const handleResize = () => {
                    if (chartRef.current) chart.applyOptions({ width: chartRef.current.clientWidth });
                };
                window.addEventListener('resize', handleResize);
                return () => {
                    window.removeEventListener('resize', handleResize);
                    chart.remove();
                };
            }, []);

            useEffect(() => {
                updateChartData(ticker, tf);
            }, [ticker, tf]);

            return (
                <div className="main-grid">
                    <header className="header border-b border-white/5">
                        <div className="flex items-center gap-3">
                            <div className="bg-blue-600 text-white p-1 rounded font-black text-sm">Q</div>
                            <span className="text-lg font-extrabold tracking-tighter uppercase">Quanta Pro <span className="text-blue-500">AI</span></span>
                        </div>
                        <div className="flex gap-4 items-center">
                            <input 
                                className="bg-[#161b22] border border-white/10 rounded-lg px-4 py-2 text-xs w-64 focus:ring-2 focus:ring-blue-500 outline-none font-bold"
                                placeholder="חפש סימול..."
                                onKeyDown={e => e.key === 'Enter' && setTicker(e.target.value.toUpperCase())}
                            />
                            <div className={`status-badge ${isSimulated ? 'bg-amber-500/10 text-amber-500' : 'bg-emerald-500/10 text-emerald-500'}`}>
                                {isSimulated ? 'מצב סימולציה' : 'נתוני שוק חיים'}
                            </div>
                        </div>
                    </header>

                    <div className="ticker-bar border-b border-white/5">
                        <div className="flex flex-col">
                            <span className="text-[10px] text-slate-500 font-bold uppercase">סימול</span>
                            <span className="text-2xl font-black text-blue-500 leading-none">{ticker}</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[10px] text-slate-500 font-bold uppercase">מחיר</span>
                            <span className="text-2xl font-mono font-bold leading-none">${stats.price}</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[10px] text-slate-500 font-bold uppercase">שינוי</span>
                            <span className={`text-2xl font-mono font-bold leading-none ${parseFloat(stats.change) >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                                {stats.change} ({stats.pct})
                            </span>
                        </div>
                        {loading && <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>}
                    </div>

                    <aside className="watchlist bg-[#0d1117] p-4">
                        <h4 className="hebrew text-xs font-bold text-slate-500 mb-4 uppercase tracking-widest">מועדפים</h4>
                        <div className="space-y-1">
                            {['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL'].map(s => (
                                <div 
                                    key={s} 
                                    onClick={() => setTicker(s)}
                                    className={`flex justify-between p-3 rounded-lg cursor-pointer transition-all ${ticker === s ? 'bg-blue-600/20 border border-blue-500/30' : 'hover:bg-white/5'}`}
                                >
                                    <span className="font-bold text-sm">{s}</span>
                                    <span className="text-[10px] text-slate-600 self-center">NASDAQ</span>
                                </div>
                            ))}
                        </div>
                    </aside>

                    <main className="chart-area panel border-none">
                        <div className="absolute top-4 left-4 z-20 flex gap-2">
                            {TIMEFRAMES.map(item => (
                                <button 
                                    key={item.id} 
                                    onClick={() => setTf(item)}
                                    className={`btn-tf hebrew ${tf.id === item.id ? 'active' : 'bg-[#161b22] hover:bg-[#30363d]'}`}
                                >
                                    {item.label}
                                </button>
                            ))}
                        </div>
                        <div className="w-full h-full" ref={chartRef}></div>

                        <div className="ai-card shadow-2xl">
                            <div className="hebrew flex-1">
                                <div className="text-[10px] font-bold text-blue-400 mb-1 uppercase tracking-widest">תובנת בינה מלאכותית</div>
                                <p className="text-sm font-semibold text-slate-200">
                                    {aiResponse ? aiResponse.insight : "סורק נתונים..."}
                                </p>
                            </div>
                            <div className="flex gap-4 items-center mr-6 border-r border-white/10 pr-6">
                                <div className="text-center">
                                    <div className="text-[9px] font-bold text-slate-500 mb-1 uppercase">Score</div>
                                    <div className="text-2xl font-black">{aiResponse?.score || '--'}</div>
                                </div>
                                <div className={`px-6 py-2 rounded-xl text-lg font-black ${
                                    aiResponse?.rec === 'BUY' ? 'bg-emerald-600' : 
                                    aiResponse?.rec === 'SELL' ? 'bg-rose-600' : 'bg-blue-600'
                                }`}>
                                    {aiResponse?.rec || 'WAIT'}
                                </div>
                            </div>
                        </div>
                    </main>

                    <footer className="col-span-2 bg-[#020408] border-t border-white/5 px-6 flex items-center justify-between text-[10px] text-slate-600 font-bold uppercase">
                        <div>TERMINAL STATUS: ONLINE</div>
                        <div className="hebrew">מבוסס מערכת QUANTA AI v2.5</div>
                    </footer>
                </div>
            );
        };

        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<App />);
    </script>
</body>
</html>
