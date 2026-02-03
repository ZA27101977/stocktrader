import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Search, 
  Plus, 
  Trash2, 
  Cpu, 
  BarChart3, 
  Clock, 
  AlertTriangle,
  ChevronRight,
  Activity
} from 'lucide-react';

const API_KEY_STOCK = "GNYJ6HBVJV6Z8TVS";
const STORAGE_KEY = 'quanta_watchlist';

const App = () => {
  const [ticker, setTicker] = useState('NVDA');
  const [searchQuery, setSearchQuery] = useState('');
  const [watchlist, setWatchlist] = useState(['AAPL', 'TSLA', 'NVDA', 'MSFT', 'META']);
  const [timeframe, setTimeframe] = useState({ id: '1D', func: 'TIME_SERIES_INTRADAY', interval: '5min', label: '1D' });
  const [stats, setStats] = useState({ price: "0.00", change: "0.00", pct: "0.00", high: "0.00", low: "0.00", volume: "0" });
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isSimulated, setIsSimulated] = useState(false);
  const [libReady, setLibReady] = useState(false);

  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
  const lastCallRef = useRef('');

  // --- Watchlist Persistence ---
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        setWatchlist(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to parse watchlist", e);
      }
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

  const removeFromWatchlist = (symbol, e) => {
    e.stopPropagation();
    const newList = watchlist.filter(s => s !== symbol);
    setWatchlist(newList);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newList));
  };

  // --- AI Analysis Logic ---
  const generateAIRecommendation = (symbol, currentPrice, data) => {
    if (!data || data.length < 10) return;
    
    const last = data[data.length - 1].close;
    const prev = data[data.length - 10]?.close || data[0].close;
    const momentum = ((last - prev) / prev) * 100;
    
    let rec = "HOLD";
    let score = 50;
    let insight = "";

    if (momentum > 1.2) {
      rec = "BUY";
      score = Math.min(95, 70 + momentum * 2);
      insight = `מניית ${symbol} מציגה מומנטום חיובי חזק. הפריצה מעל רמות התמיכה מעידה על פוטנציאל המשך עליות.`;
    } else if (momentum < -1.2) {
      rec = "SELL";
      score = Math.max(5, 30 + momentum * 2);
      insight = `לחץ מכירות ב-${symbol}. האינדיקטורים מצביעים על חולשה, מומלץ להמתין להתייצבות.`;
    } else {
      insight = `המניה נסחרת בטווח דשדוש. אין כיוון ברור כרגע, מומלץ להמתין לפריצה.`;
    }

    setAiAnalysis({ rec, score: Math.round(score), insight });
  };

  // --- Data Fetching ---
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
      
      if (!seriesData) throw new Error("API Limit");

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
        volume: parseInt(seriesData[Object.keys(seriesData)[0]]["5. volume"]).toLocaleString()
      });

      if (seriesRef.current) {
        seriesRef.current.setData(formatted);
      }
      generateAIRecommendation(symbol, latest.close, formatted);
      setIsSimulated(false);
    } catch (err) {
      const mock = [];
      let base = 150 + Math.random() * 50;
      const now = Math.floor(Date.now() / 1000);
      for(let i=0; i<100; i++) {
        const o = base + (Math.random() - 0.5) * 2;
        const c = o + (Math.random() - 0.5) * 3;
        const timeValue = tf.id === '1D' 
          ? now - (100 - i) * 300 
          : new Date(Date.now() - (100 - i) * 86400000).toISOString().split('T')[0];
        
        mock.push({
          time: timeValue,
          open: o, high: Math.max(o, c) + 0.5, low: Math.min(o, c) - 0.5, close: c
        });
        base = c;
      }
      if (seriesRef.current) {
        seriesRef.current.setData(mock);
      }
      setStats({ price: base.toFixed(2), change: "1.20", pct: "0.85", high: (base+2).toFixed(2), low: (base-2).toFixed(2), volume: "1.2M" });
      generateAIRecommendation(symbol, base, mock);
      setIsSimulated(true);
    } finally {
      setLoading(false);
      if (chartRef.current) {
        chartRef.current.timeScale().fitContent();
      }
    }
  }, []);

  // --- Robust Library Initialization ---
  useEffect(() => {
    const scriptId = 'lw-charts-script';
    if (!document.getElementById(scriptId)) {
      const script = document.createElement('script');
      script.id = scriptId;
      script.src = 'https://unpkg.com/lightweight-charts@3.8.0/dist/lightweight-charts.standalone.production.js';
      script.async = true;
      script.onload = () => setLibReady(true);
      document.head.appendChild(script);
    } else if (window.LightweightCharts) {
      setLibReady(true);
    }
  }, []);

  // --- Chart Lifecycle ---
  useEffect(() => {
    if (!libReady || !chartContainerRef.current) return;

    const LWCharts = window.LightweightCharts;
    if (!LWCharts || typeof LWCharts.createChart !== 'function') {
      const timer = setTimeout(() => setLibReady(false), 500); // Retry logic
      return () => clearTimeout(timer);
    }

    const container = chartContainerRef.current;
    
    // Cleanup previous chart
    if (chartRef.current) {
      chartRef.current.remove();
    }

    try {
      const chart = LWCharts.createChart(container, {
        layout: { 
          backgroundColor: '#05070a', 
          textColor: '#d1d5db',
          fontSize: 12 
        },
        grid: { 
          vertLines: { color: '#111827' }, 
          horzLines: { color: '#111827' } 
        },
        rightPriceScale: { borderColor: '#1f2937' },
        timeScale: { borderColor: '#1f2937', timeVisible: true },
        width: container.clientWidth,
        height: container.clientHeight
      });

      const candleSeries = chart.addCandlestickSeries({
        upColor: '#10b981', 
        downColor: '#ef4444', 
        borderVisible: false, 
        wickUpColor: '#10b981', 
        wickDownColor: '#ef4444'
      });

      chartRef.current = chart;
      seriesRef.current = candleSeries;

      fetchData(ticker, timeframe);

      const handleResize = () => {
        if (container && chartRef.current) {
          chartRef.current.applyOptions({ 
            width: container.clientWidth,
            height: container.clientHeight
          });
        }
      };

      window.addEventListener('resize', handleResize);
      return () => {
        window.removeEventListener('resize', handleResize);
        if (chartRef.current) {
          chartRef.current.remove();
          chartRef.current = null;
        }
      };
    } catch (e) {
      console.error("Chart initialization failed:", e);
    }
  }, [libReady, ticker, timeframe, fetchData]);

  return (
    <div className="flex flex-col h-screen bg-[#05070a] text-slate-200 font-sans select-none overflow-hidden" dir="ltr">
      {/* Header */}
      <header className="h-16 border-b border-white/5 flex items-center justify-between px-6 bg-[#0a0d14] shrink-0">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center font-black text-white">Q</div>
            <span className="text-xl font-bold tracking-tight text-white">QUANTA<span className="text-blue-500">PRO</span></span>
          </div>
          
          <div className="flex bg-[#111827] rounded-lg border border-white/10 p-1">
            {['1D', '1W', '1M', '1Y'].map(id => (
              <button
                key={id}
                onClick={() => {
                  const configs = {
                    '1D': { id: '1D', func: 'TIME_SERIES_INTRADAY', interval: '5min' },
                    '1W': { id: '1W', func: 'TIME_SERIES_DAILY' },
                    '1M': { id: '1M', func: 'TIME_SERIES_DAILY' },
                    '1Y': { id: '1Y', func: 'TIME_SERIES_WEEKLY' }
                  };
                  setTimeframe(configs[id]);
                }}
                className={`px-4 py-1.5 text-xs font-bold rounded-md transition-all ${timeframe.id === id ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-500 hover:text-white'}`}
              >
                {id}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="relative">
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">
                <Search size={16} />
            </div>
            <input 
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === 'Enter' && addToWatchlist()}
              placeholder="Search ticker..."
              className="bg-[#111827] border border-white/10 rounded-xl pl-10 pr-10 py-2 text-sm w-64 focus:ring-2 focus:ring-blue-500 outline-none text-white text-left"
            />
          </div>
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-[10px] font-bold border ${isSimulated ? 'bg-amber-500/10 text-amber-500 border-amber-500/20' : 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'}`}>
            <Activity size={12} className="animate-pulse" />
            {isSimulated ? 'SIMULATED' : 'LIVE'}
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden" dir="rtl">
        <main className="flex-1 flex flex-col min-w-0" dir="ltr">
          {/* Stats Bar */}
          <div className="p-6 grid grid-cols-4 gap-4 border-b border-white/5 bg-[#0a0d14]/50" dir="rtl">
            <div className="text-right">
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">נכס</span>
              <div className="text-3xl font-black text-white">{ticker}</div>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">מחיר</span>
              <div className="text-3xl font-mono font-bold text-white">${stats.price}</div>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">שינוי</span>
              <div className={`text-3xl font-mono font-bold flex items-center justify-end gap-2 ${parseFloat(stats.change) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {parseFloat(stats.change) >= 0 ? <TrendingUp size={24} /> : <TrendingDown size={24} />}
                {stats.pct}%
              </div>
            </div>
            <div className="flex flex-col justify-center border-r border-white/10 pr-6 text-right">
              <span className="text-[10px] text-slate-500 font-bold uppercase block mb-1">מחזור (Volume)</span>
              <span className="text-sm font-bold text-slate-300">{stats.volume}</span>
            </div>
          </div>

          {/* Chart Area */}
          <div className="flex-1 relative bg-[#05070a] min-h-0">
            {loading && (
              <div className="absolute inset-0 z-50 flex items-center justify-center bg-[#05070a]/50">
                <div className="w-10 h-10 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              </div>
            )}
            <div ref={chartContainerRef} className="w-full h-full" />

            {/* AI Recommendation */}
            <div className="absolute bottom-6 left-6 right-6 bg-[#0a0d14]/90 backdrop-blur-md border border-white/10 rounded-2xl p-4 flex items-center justify-between shadow-2xl z-40" dir="rtl">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-blue-600/20 rounded-lg flex items-center justify-center text-blue-500">
                  <Cpu size={20} />
                </div>
                <div className="text-right">
                  <h4 className="text-[10px] font-bold text-blue-400 uppercase tracking-widest flex items-center gap-1">
                    <BarChart3 size={10} /> ניתוח מערכת AI
                  </h4>
                  <p className="text-xs text-slate-300 max-w-xl">{aiAnalysis?.insight || "מעבד נתונים..."}</p>
                </div>
              </div>
              <div className="flex items-center gap-4 pr-4 border-r border-white/10">
                <div className="text-center">
                  <div className="text-[10px] text-slate-500 uppercase font-bold">ציון</div>
                  <div className="text-xl font-black text-white">{aiAnalysis?.score || '--'}</div>
                </div>
                <div className={`px-6 py-2 rounded-lg text-sm font-black text-white ${
                  aiAnalysis?.rec === 'BUY' ? 'bg-emerald-600' : aiAnalysis?.rec === 'SELL' ? 'bg-rose-600' : 'bg-slate-700'
                }`}>
                  {aiAnalysis?.rec || 'HOLD'}
                </div>
              </div>
            </div>
          </div>
        </main>

        {/* Sidebar */}
        <aside className="w-72 border-r border-white/5 bg-[#0a0d14] flex flex-col shrink-0 text-right">
          <div className="p-4 border-b border-white/5 flex items-center justify-between flex-row-reverse">
            <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">רשימת מעקב</span>
            <button onClick={addToWatchlist} className="text-slate-500 hover:text-white transition-colors">
                <Plus size={14} />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {watchlist.map(s => (
              <div 
                key={s}
                onClick={() => setTicker(s)}
                className={`flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all flex-row-reverse ${ticker === s ? 'bg-blue-600/10 border border-blue-500/20' : 'hover:bg-white/5 border border-transparent'}`}
              >
                <span className={`font-bold text-sm ${ticker === s ? 'text-white' : 'text-slate-400'}`}>{s}</span>
                <div className="flex items-center gap-2">
                  <button onClick={(e) => removeFromWatchlist(s, e)} className="text-slate-700 hover:text-rose-500">
                    <Trash2 size={12} />
                  </button>
                  <ChevronRight size={14} className={`rotate-180 ${ticker === s ? 'text-blue-500' : 'text-slate-700'}`} />
                </div>
              </div>
            ))}
          </div>
          <div className="p-4 border-t border-white/5">
            <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 flex gap-2 flex-row-reverse">
              <AlertTriangle size={14} className="text-amber-500 shrink-0" />
              <p className="text-[9px] text-amber-200/50 leading-tight">אין לראות במידע זה ייעוץ פיננסי או המלצה להשקעה בניירות ערך.</p>
            </div>
          </div>
        </aside>
      </div>

      <footer className="h-6 bg-[#0a0d14] border-t border-white/5 px-6 flex items-center justify-between text-[9px] font-bold text-slate-600 tracking-widest uppercase">
        <div className="flex items-center gap-4">
            <div className="flex items-center gap-1">
                <div className="w-1 h-1 rounded-full bg-emerald-500 animate-pulse"></div>
                SYSTEM ACTIVE
            </div>
            <span>DATA: {isSimulated ? 'DELAYED_MOCK' : 'REALTIME_FEED'}</span>
        </div>
        <div>QUANTA PRO TERMINAL v2.4</div>
      </footer>
    </div>
  );
};

export default App;
