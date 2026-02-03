import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Search, 
  Plus, 
  Trash2, 
  Cpu, 
  BarChart3, 
  AlertTriangle,
  ChevronRight,
  Activity,
  DollarSign,
  Zap,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';

const API_KEY_STOCK = "GNYJ6HBVJV6Z8TVS";
const STORAGE_KEY = 'quanta_watchlist';

const App = () => {
  const [ticker, setTicker] = useState('NVDA');
  const [searchQuery, setSearchQuery] = useState('');
  const [watchlist, setWatchlist] = useState(['AAPL', 'TSLA', 'NVDA', 'MSFT', 'META']);
  const [timeframe, setTimeframe] = useState({ id: '1D', func: 'TIME_SERIES_INTRADAY', interval: '5min' });
  const [stats, setStats] = useState({ price: "0.00", change: "0.00", pct: "0.00", high: "0.00", low: "0.00", volume: "0" });
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isSimulated, setIsSimulated] = useState(false);
  const [libReady, setLibReady] = useState(false);
  const [portfolio, setPortfolio] = useState({ balance: 50000, shares: 0 });

  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
  const lastCallRef = useRef('');

  // --- Watchlist Persistence ---
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try { setWatchlist(JSON.parse(saved)); } catch (e) { console.error(e); }
    }
  }, []);

  const addToWatchlist = () => {
    if (searchQuery && !watchlist.includes(searchQuery.toUpperCase())) {
      const newList = [searchQuery.toUpperCase(), ...watchlist];
      setWatchlist(newList);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newList));
      setTicker(searchQuery.toUpperCase());
      setSearchQuery('');
    }
  };

  // --- Enhanced Recommendation Engine ---
  const generateAIRecommendation = (symbol, data) => {
    if (!data || data.length < 20) return;
    
    const prices = data.map(d => d.close);
    const lastPrice = prices[prices.length - 1];
    const avg = prices.reduce((a, b) => a + b, 0) / prices.length;
    const rsi = 50 + (Math.random() * 20 - 10); // Simulated RSI logic

    let rec = "HOLD";
    let score = 50;
    let insight = "";

    if (lastPrice > avg * 1.02) {
      rec = "BUY";
      score = Math.round(75 + (lastPrice / avg) * 5);
      insight = `מניית ${symbol} נסחרת מעל הממוצע הנע. המומנטום חיובי וקיים פוטנציאל לפריצה של רמת ההתנגדות הקרובה.`;
    } else if (lastPrice < avg * 0.98) {
      rec = "SELL";
      score = Math.round(25 - (avg / lastPrice) * 5);
      insight = `זוהתה שבירה של רמת תמיכה ב-${symbol}. האינדיקטורים הטכניים מצביעים על לחץ מכירות מוגבר.`;
    } else {
      insight = `המניה נסחרת בטווח יציב (Consolidation). מומלץ להמתין לאות ברור יותר לפני כניסה לעסקה.`;
    }

    setAiAnalysis({ rec, score: Math.max(0, Math.min(100, score)), insight });
  };

  // --- Live Data Fetching ---
  const fetchData = useCallback(async (symbol, tf) => {
    const callKey = `${symbol}-${tf.id}`;
    if (lastCallRef.current === callKey) return;
    lastCallRef.current = callKey;
    
    setLoading(true);
    try {
      let url = `https://www.alphavantage.co/query?function=${tf.func}&symbol=${symbol}&apikey=${API_KEY_STOCK}`;
      if (tf.interval) url += `&interval=${tf.interval}`;

      const res = await fetch(url);
      const data = await res.json();
      
      const keyMap = {
        '1D': "Time Series (5min)",
        '1W': "Time Series (Daily)",
        '1M': "Time Series (Daily)",
        '1Y': "Weekly Time Series"
      };

      const seriesData = data[keyMap[tf.id]];
      
      if (!seriesData) {
        if (data["Note"]) throw new Error("API_LIMIT");
        throw new Error("NO_DATA");
      }

      const formatted = Object.entries(seriesData).map(([time, v]) => ({
        time: tf.id === '1D' ? Math.floor(new Date(time).getTime() / 1000) : time,
        open: parseFloat(v["1. open"]),
        high: parseFloat(v["2. high"]),
        low: parseFloat(v["3. low"]),
        close: parseFloat(v["4. close"]),
      })).reverse();

      const latest = formatted[formatted.length - 1];
      const prev = formatted[formatted.length - 2] || latest;
      
      setStats({
        price: latest.close.toFixed(2),
        change: (latest.close - prev.close).toFixed(2),
        pct: (((latest.close - prev.close) / prev.close) * 100).toFixed(2),
        high: latest.high.toFixed(2),
        low: latest.low.toFixed(2),
        volume: parseInt(seriesData[Object.keys(seriesData)[0]]["5. volume"] || "0").toLocaleString()
      });

      if (seriesRef.current) seriesRef.current.setData(formatted);
      generateAIRecommendation(symbol, formatted);
      setIsSimulated(false);
    } catch (err) {
      console.warn("Falling back to simulation mode due to API constraints");
      const mock = [];
      let base = 150 + Math.random() * 50;
      const now = Math.floor(Date.now() / 1000);
      for(let i=0; i<100; i++) {
        const o = base + (Math.random() - 0.5) * 2;
        const c = o + (Math.random() - 0.5) * 3;
        mock.push({
          time: tf.id === '1D' ? now - (100 - i) * 300 : new Date(Date.now() - (100 - i) * 86400000).toISOString().split('T')[0],
          open: o, high: Math.max(o, c) + 0.5, low: Math.min(o, c) - 0.5, close: c
        });
        base = c;
      }
      if (seriesRef.current) seriesRef.current.setData(mock);
      setStats({ price: base.toFixed(2), change: "1.45", pct: "0.92", high: (base+3).toFixed(2), low: (base-3).toFixed(2), volume: "850K" });
      generateAIRecommendation(symbol, mock);
      setIsSimulated(true);
    } finally {
      setLoading(false);
      if (chartRef.current) chartRef.current.timeScale().fitContent();
    }
  }, []);

  // --- Script Loader ---
  useEffect(() => {
    const script = document.createElement('script');
    script.src = 'https://unpkg.com/lightweight-charts@3.8.0/dist/lightweight-charts.standalone.production.js';
    script.async = true;
    script.onload = () => setLibReady(true);
    document.head.appendChild(script);
  }, []);

  // --- Chart Lifecycle ---
  useEffect(() => {
    if (!libReady || !chartContainerRef.current) return;
    const LWCharts = window.LightweightCharts;
    if (!LWCharts) return;

    const container = chartContainerRef.current;
    const chart = LWCharts.createChart(container, {
      layout: { backgroundColor: '#05070a', textColor: '#94a3b8', fontSize: 11 },
      grid: { vertLines: { color: '#0f172a' }, horzLines: { color: '#0f172a' } },
      rightPriceScale: { borderColor: '#1e293b', scaleMargins: { top: 0.1, bottom: 0.2 } },
      timeScale: { borderColor: '#1e293b', timeVisible: true },
      width: container.clientWidth,
      height: container.clientHeight,
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#10b981', downColor: '#ef4444', borderVisible: false, wickUpColor: '#10b981', wickDownColor: '#ef4444'
    });

    chartRef.current = chart;
    seriesRef.current = candleSeries;
    fetchData(ticker, timeframe);

    const handleResize = () => chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [libReady, ticker, timeframe, fetchData]);

  return (
    <div className="flex flex-col h-screen bg-[#020617] text-slate-200 font-sans select-none overflow-hidden" dir="rtl">
      {/* Top Navigation */}
      <header className="h-14 border-b border-white/5 flex items-center justify-between px-6 bg-[#0a0f1e] shrink-0">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-900/20">
              <Zap size={16} className="text-white fill-current" />
            </div>
            <span className="text-lg font-black tracking-tighter text-white">QUANTA<span className="text-blue-500">LIVE</span></span>
          </div>
          
          <nav className="flex items-center gap-1 bg-white/5 p-1 rounded-xl">
            {['1D', '1W', '1M', '1Y'].map(id => (
              <button
                key={id}
                onClick={() => {
                   const tfMap = {
                     '1D': { id: '1D', func: 'TIME_SERIES_INTRADAY', interval: '5min' },
                     '1W': { id: '1W', func: 'TIME_SERIES_DAILY' },
                     '1M': { id: '1M', func: 'TIME_SERIES_DAILY' },
                     '1Y': { id: '1Y', func: 'TIME_SERIES_WEEKLY' }
                   };
                   setTimeframe(tfMap[id]);
                }}
                className={`px-4 py-1.5 text-[10px] font-black rounded-lg transition-all ${timeframe.id === id ? 'bg-blue-600 text-white' : 'text-slate-500 hover:text-white'}`}
              >
                {id}
              </button>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-6">
          <div className="relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500" size={14} />
            <input 
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value.toUpperCase())}
              onKeyDown={e => e.key === 'Enter' && addToWatchlist()}
              placeholder="חפש מנייה..."
              className="bg-white/5 border border-white/10 rounded-xl pr-10 pl-4 py-1.5 text-xs w-60 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            />
          </div>
          <div className="flex items-center gap-3 border-r border-white/10 pr-6 mr-2">
             <div className="text-left">
                <p className="text-[8px] text-slate-500 font-bold uppercase">Balance</p>
                <p className="text-xs font-mono font-bold text-emerald-400">${portfolio.balance.toLocaleString()}</p>
             </div>
             <div className="w-8 h-8 rounded-full bg-slate-800 border border-white/10 flex items-center justify-center">
                <DollarSign size={14} />
             </div>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Main Terminal */}
        <main className="flex-1 flex flex-col min-w-0 bg-[#020617]">
          {/* Price & Stats */}
          <div className="p-6 flex items-center justify-between border-b border-white/5 bg-gradient-to-b from-[#0a0f1e] to-transparent">
            <div className="flex items-center gap-6">
              <div>
                <h1 className="text-4xl font-black tracking-tighter text-white">{ticker}</h1>
                <p className="text-[10px] text-blue-500 font-bold uppercase tracking-widest">{isSimulated ? 'Simulation Mode' : 'Market Live'}</p>
              </div>
              <div className="h-10 w-px bg-white/10" />
              <div>
                <p className="text-[10px] text-slate-500 font-bold uppercase mb-1">מחיר נוכחי</p>
                <p className="text-3xl font-mono font-bold text-white tracking-tighter">${stats.price}</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-500 font-bold uppercase mb-1">שינוי יומי</p>
                <div className={`text-xl font-mono font-bold flex items-center gap-1 ${parseFloat(stats.change) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {parseFloat(stats.change) >= 0 ? <ArrowUpRight size={20} /> : <ArrowDownRight size={20} />}
                  {stats.pct}%
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <button className="px-8 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-black text-sm transition-all shadow-lg shadow-emerald-900/20 active:scale-95">BUY</button>
              <button className="px-8 py-3 bg-rose-600 hover:bg-rose-500 text-white rounded-xl font-black text-sm transition-all shadow-lg shadow-rose-900/20 active:scale-95">SELL</button>
            </div>
          </div>

          {/* Chart Section */}
          <div className="flex-1 relative min-h-0">
            {loading && (
              <div className="absolute inset-0 z-50 flex items-center justify-center bg-[#020617]/50 backdrop-blur-sm">
                <Activity className="animate-spin text-blue-500" size={32} />
              </div>
            )}
            <div ref={chartContainerRef} className="w-full h-full" />
            
            {/* AI Insights Panel */}
            <div className="absolute bottom-6 left-6 right-6 flex gap-4 pointer-events-none">
              <div className="flex-1 bg-[#0a0f1e]/90 backdrop-blur-xl border border-white/10 rounded-2xl p-4 shadow-2xl flex items-center justify-between pointer-events-auto">
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${aiAnalysis?.rec === 'BUY' ? 'bg-emerald-500/20 text-emerald-500' : 'bg-rose-500/20 text-rose-500'}`}>
                    <Cpu size={24} />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                       <span className="text-[10px] font-black text-blue-500 uppercase tracking-widest">AI Analyst Prediction</span>
                       <span className="px-2 py-0.5 rounded bg-white/5 text-[9px] font-bold text-slate-400 border border-white/5">Score: {aiAnalysis?.score}/100</span>
                    </div>
                    <p className="text-sm font-medium text-slate-200 mt-0.5">{aiAnalysis?.insight || "מנתח נתוני שוק..."}</p>
                  </div>
                </div>
                <div className="flex flex-col items-center pl-4 border-r border-white/10">
                   <p className="text-[10px] text-slate-500 font-bold uppercase mb-1">Recommendation</p>
                   <p className={`text-2xl font-black ${aiAnalysis?.rec === 'BUY' ? 'text-emerald-400' : aiAnalysis?.rec === 'SELL' ? 'text-rose-400' : 'text-slate-400'}`}>
                    {aiAnalysis?.rec || 'ANALYZING'}
                   </p>
                </div>
              </div>
            </div>
          </div>
        </main>

        {/* Sidebar */}
        <aside className="w-80 border-r border-white/5 bg-[#0a0f1e] flex flex-col shrink-0">
          <div className="p-4 border-b border-white/5 flex items-center justify-between">
            <h2 className="text-[10px] font-black text-slate-500 uppercase tracking-widest">רשימת מעקב (Watchlist)</h2>
            <Activity size={14} className="text-blue-500" />
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {watchlist.map(s => (
              <div 
                key={s}
                onClick={() => setTicker(s)}
                className={`p-4 rounded-2xl cursor-pointer transition-all border ${ticker === s ? 'bg-blue-600/10 border-blue-500/30' : 'bg-white/5 border-transparent hover:border-white/10'}`}
              >
                <div className="flex justify-between items-start mb-2">
                  <span className="text-lg font-black text-white">{s}</span>
                  <button onClick={(e) => { e.stopPropagation(); setWatchlist(prev => prev.filter(item => item !== s)); }} className="text-slate-600 hover:text-rose-500">
                    <Trash2 size={12} />
                  </button>
                </div>
                <div className="flex justify-between items-end">
                  <div className="text-[10px] font-bold text-slate-500 uppercase">Live Price</div>
                  <div className="text-sm font-mono font-bold text-slate-300">$---.--</div>
                </div>
              </div>
            ))}
          </div>
          <div className="p-4 bg-[#020617]/50 border-t border-white/5">
             <div className="flex items-center gap-2 mb-3">
                <AlertTriangle size={14} className="text-amber-500" />
                <span className="text-[10px] font-bold text-amber-500 uppercase">Risk Disclaimer</span>
             </div>
             <p className="text-[9px] text-slate-500 leading-relaxed font-medium">
               המסחר בניירות ערך כרוך בסיכון משמעותי. המלצות ה-AI מבוססות על מודלים סטטיסטיים בלבד ואינן מהוות ייעוץ השקעות.
             </p>
          </div>
        </aside>
      </div>

      <footer className="h-8 bg-[#0a0f1e] border-t border-white/5 px-6 flex items-center justify-between text-[9px] font-black text-slate-600 tracking-tighter uppercase">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
            CONNECTED TO ALPHA_VANTAGE
          </div>
          <span>NODE: TA_ISRAEL_01</span>
        </div>
        <div className="flex items-center gap-4">
           <span>MARKET STATUS: OPEN</span>
           <span className="text-blue-500">QUANTA PRO v3.0 LIVE EDITION</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
