import React, { useState, useEffect, useCallback } from 'react';
import { 
  TrendingUp, TrendingDown, Bell, Search, Newspaper, 
  BarChart3, AlertCircle, Loader2, DollarSign, ArrowUpRight, 
  ArrowDownRight, Wallet, History, Activity, Briefcase
} from 'lucide-react';

// Configuration
const API_KEY = ""; // Gemini API Key
const STOCK_API_KEY = "demo"; 

const App = () => {
  const [ticker, setTicker] = useState('AAPL');
  const [stockData, setStockData] = useState(null);
  const [news, setNews] = useState([]);
  const [financials, setFinancials] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [portfolio, setPortfolio] = useState({ balance: 25000, shares: 0 });
  const [alerts, setAlerts] = useState([]);
  const [tradeStatus, setTradeStatus] = useState(null);

  // Exponential Backoff Fetch
  const fetchWithRetry = async (url, options, retries = 5, backoff = 1000) => {
    try {
      const response = await fetch(url, options);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (err) {
      if (retries > 0) {
        await new Promise(r => setTimeout(r, backoff));
        return fetchWithRetry(url, options, retries - 1, backoff * 2);
      }
      throw err;
    }
  };

  // AI Analysis for News & Earnings
  const performAIAnalysis = async (tickerSymbol, newsItems, financials) => {
    const prompt = `Analyze the data for ${tickerSymbol} as a Wall Street analyst.
    News: ${JSON.stringify(newsItems.slice(0, 3))}
    Financials: ${JSON.stringify(financials)}
    
    Return a JSON object with:
    "sentiment": "positive"/"negative"/"neutral",
    "score": 0-100,
    "summary": "Short Hebrew summary of news and earnings",
    "risk_level": "low"/"medium"/"high",
    "recommendation": "BUY"/"SELL"/"HOLD"`;

    try {
      const result = await fetchWithRetry(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${API_KEY}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contents: [{ parts: [{ text: prompt }] }],
            generationConfig: { responseMimeType: "application/json" }
          })
        }
      );
      return JSON.parse(result.candidates?.[0]?.content?.parts?.[0]?.text || "{}");
    } catch (err) {
      return { sentiment: 'neutral', score: 50, summary: "לא ניתן היה לבצע ניתוח AI כרגע.", recommendation: "HOLD", risk_level: "medium" };
    }
  };

  const fetchData = useCallback(async (symbol) => {
    setLoading(true);
    setTradeStatus(null);
    try {
      // 1. Price Data Simulation
      const price = {
        symbol,
        price: (Math.random() * 50 + 150).toFixed(2),
        change: (Math.random() * 8 - 4).toFixed(2),
        changePercent: (Math.random() * 3 - 1.5).toFixed(2)
      };
      setStockData(price);

      // 2. Mock Financials
      const mockFinancials = {
        revenue: "89.5B",
        revenueGrowth: "+5.2%",
        eps: "1.46",
        epsForecast: "1.39",
        netIncome: "22.9B"
      };
      setFinancials(mockFinancials);

      // 3. News Feed
      const mockNews = [
        { title: `${symbol} מכריזה על שת"פ AI חדש`, summary: "הסכם אסטרטגי עם ענקיות הענן צפוי להגדיל את הרווחיות." },
        { title: "דוח רבעוני חזק מהצפוי", summary: "החברה מדווחת על עלייה במכירות החומרה והשירותים." }
      ];
      setNews(mockNews);

      // 4. AI Analysis
      const aiResult = await performAIAnalysis(symbol, mockNews, mockFinancials);
      setAnalysis(aiResult);

      if (aiResult.score > 85) {
        addAlert(`הזדמנות חזקה ב-${symbol}! ציון AI: ${aiResult.score}`);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  const addAlert = (msg) => {
    setAlerts(prev => [{ id: Date.now(), msg, time: new Date().toLocaleTimeString() }, ...prev].slice(0, 5));
  };

  const handleTrade = (type) => {
    const cost = Number(stockData.price);
    if (type === 'BUY' && portfolio.balance >= cost) {
      setPortfolio(prev => ({ balance: prev.balance - cost, shares: prev.shares + 1 }));
      setTradeStatus({ type: 'success', msg: `בוצע: קניית מניית ${ticker}` });
    } else if (type === 'SELL' && portfolio.shares > 0) {
      setPortfolio(prev => ({ balance: prev.balance + cost, shares: prev.shares - 1 }));
      setTradeStatus({ type: 'success', msg: `בוצע: מכירת מניית ${ticker}` });
    } else {
      setTradeStatus({ type: 'error', msg: 'יתרה לא מספקת או אין מניות למכירה' });
    }
    setTimeout(() => setTradeStatus(null), 3000);
  };

  useEffect(() => { fetchData(ticker); }, [fetchData]);

  return (
    <div className="min-h-screen bg-black text-slate-100 p-4 font-sans selection:bg-blue-500/30" dir="rtl">
      {/* Portfolio Stats Bar */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-2xl flex items-center justify-between shadow-lg">
          <div className="flex items-center gap-3">
            <div className="bg-blue-500/10 p-2 rounded-lg"><Wallet className="text-blue-400" size={20} /></div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">יתרה פנויה</div>
              <div className="text-lg font-bold font-mono">${portfolio.balance.toLocaleString()}</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="bg-purple-500/10 p-2 rounded-lg"><Briefcase className="text-purple-400" size={20} /></div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">מניות</div>
              <div className="text-lg font-bold font-mono">{portfolio.shares}</div>
            </div>
          </div>
        </div>

        <div className="md:col-span-2 bg-slate-900/80 border border-slate-800 p-4 rounded-2xl flex items-center gap-4 overflow-x-auto no-scrollbar shadow-lg">
          <History className="text-yellow-500 shrink-0" size={20} />
          <div className="flex gap-4">
            {alerts.length > 0 ? alerts.map(a => (
              <div key={a.id} className="whitespace-nowrap bg-blue-500/10 border border-blue-500/20 px-3 py-1 rounded-full text-xs text-blue-300 flex items-center gap-2">
                <span className="opacity-40 text-[10px]">{a.time}</span> {a.msg}
              </div>
            )) : <span className="text-xs text-slate-500 italic">ממתין להתראות שוק...</span>}
          </div>
        </div>
      </div>

      <main className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Main Trading Area */}
        <div className="lg:col-span-8 space-y-6">
          
          {/* Header & Search */}
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between bg-slate-900/40 p-5 rounded-3xl border border-slate-800 shadow-inner">
            <div className="flex items-center gap-4">
              <h1 className="text-4xl font-black text-white tracking-tighter">{ticker}</h1>
              <div className="flex items-center gap-2 px-3 py-1 bg-green-500/10 rounded-full border border-green-500/20">
                <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                <span className="text-[10px] font-bold uppercase text-green-400">Live Trade</span>
              </div>
            </div>
            
            <form onSubmit={(e) => { e.preventDefault(); fetchData(e.target.symbol.value.toUpperCase()); }} className="relative">
              <input 
                name="symbol"
                className="bg-slate-800 border-none rounded-2xl py-2.5 px-12 w-full md:w-64 focus:ring-2 focus:ring-blue-500 transition-all text-sm"
                placeholder="הזן סימול מניה..."
              />
              <Search className="absolute right-4 top-3 text-slate-500" size={18} />
            </form>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Price Execution Card */}
            <div className="bg-gradient-to-br from-slate-900 via-slate-900 to-black border border-slate-800 p-8 rounded-[2rem] shadow-2xl relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1 bg-blue-500/30" />
              {loading && <div className="absolute inset-0 bg-black/60 backdrop-blur-md z-30 flex items-center justify-center"><Loader2 className="animate-spin text-blue-500" size={40} /></div>}
              
              <div className="flex justify-between items-start mb-10">
                <div>
                  <div className="text-xs text-slate-500 mb-1 font-bold uppercase tracking-widest">Market Price</div>
                  <div className="text-6xl font-mono font-bold tracking-tighter">${stockData?.price}</div>
                  <div className={`flex items-center gap-1 mt-3 font-bold text-lg ${Number(stockData?.change) > 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {Number(stockData?.change) > 0 ? <TrendingUp size={22} /> : <TrendingDown size={22} />}
                    {stockData?.changePercent}%
                  </div>
                </div>
                <div className="flex flex-col gap-3">
                  <button onClick={() => handleTrade('BUY')} className="bg-green-600 hover:bg-green-500 text-white font-black py-3 px-8 rounded-2xl transition-all active:scale-95 shadow-xl shadow-green-900/30 text-sm">BUY</button>
                  <button onClick={() => handleTrade('SELL')} className="bg-red-600 hover:bg-red-500 text-white font-black py-3 px-8 rounded-2xl transition-all active:scale-95 shadow-xl shadow-red-900/30 text-sm">SELL</button>
                </div>
              </div>
              
              {tradeStatus && (
                <div className={`mb-6 p-3 rounded-xl text-center text-xs font-bold animate-in fade-in slide-in-from-top-2 ${tradeStatus.type === 'success' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
                  {tradeStatus.msg}
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-white/5 rounded-2xl border border-white/5">
                  <span className="text-slate-500 block text-[10px] font-bold uppercase mb-1">Volume</span>
                  <span className="font-bold text-lg">142.5M</span>
                </div>
                <div className="p-4 bg-white/5 rounded-2xl border border-white/5">
                  <span className="text-slate-500 block text-[10px] font-bold uppercase mb-1">P/E</span>
                  <span className="font-bold text-lg">28.4</span>
                </div>
              </div>
            </div>

            {/* AI Insight Terminal */}
            <div className={`p-8 rounded-[2rem] border-2 transition-all duration-500 ${
              analysis?.sentiment === 'positive' ? 'border-green-500/30 bg-green-500/5' : 
              analysis?.sentiment === 'negative' ? 'border-red-500/30 bg-red-500/5' : 'border-slate-800 bg-slate-900/50'
            }`}>
              <div className="flex items-center justify-between mb-6">
                <h3 className="font-black text-xl flex items-center gap-2">
                  <BarChart3 size={24} className="text-blue-400" />
                  ניתוח AI
                </h3>
                <div className={`px-3 py-1 rounded-full text-[10px] font-black uppercase ${
                  analysis?.risk_level === 'low' ? 'bg-green-500/20 text-green-400' : 
                  analysis?.risk_level === 'high' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'
                }`}>
                  סיכון: {analysis?.risk_level === 'low' ? 'נמוך' : analysis?.risk_level === 'high' ? 'גבוה' : 'בינוני'}
                </div>
              </div>
              
              <div className="bg-black/40 p-5 rounded-2xl border border-white/5 mb-6">
                <p className="text-sm leading-relaxed text-slate-200 h-24 overflow-y-auto custom-scrollbar italic font-medium">
                  "{analysis?.summary || "סורק דוחות כספיים וחדשות אחרונות..."}"
                </p>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <div className="text-[10px] text-slate-500 uppercase font-bold mb-1 tracking-widest">Sentiment Score</div>
                  <div className="text-4xl font-black text-blue-400">{analysis?.score || 0}%</div>
                </div>
                <div className="text-left">
                  <div className="text-[10px] text-slate-500 uppercase font-bold mb-1 tracking-widest">Rec.</div>
                  <div className="text-2xl font-black tracking-tighter">{analysis?.recommendation || '---'}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Earnings & Fundamentals */}
          <div className="bg-slate-900/30 border border-slate-800 rounded-3xl p-8 shadow-inner">
            <h3 className="font-bold text-lg mb-8 flex items-center gap-3">
              <DollarSign size={20} className="text-green-500 bg-green-500/10 p-1 rounded" />
              ביצועים פיננסיים (SEC Filing Summary)
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
              <div className="space-y-2">
                <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">הכנסות</div>
                <div className="text-2xl font-bold">{financials?.revenue}</div>
                <div className="text-xs font-bold text-green-400 bg-green-400/10 w-fit px-2 py-0.5 rounded-full">{financials?.revenueGrowth} YoY</div>
              </div>
              <div className="space-y-2">
                <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">EPS (דווח)</div>
                <div className="text-2xl font-bold">${financials?.eps}</div>
                <div className="text-[10px] text-slate-400 font-medium">תחזית: ${financials?.epsForecast}</div>
              </div>
              <div className="space-y-2">
                <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">רווח נקי</div>
                <div className="text-2xl font-bold">{financials?.netIncome}</div>
                <div className="text-[10px] text-slate-500">Margin: 25.6%</div>
              </div>
              <div className="space-y-2">
                <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">דירוג קונצנזוס</div>
                <div className="text-2xl font-bold text-blue-400">Strong Buy</div>
                <div className="text-[10px] text-slate-500">32 אנליסטים</div>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar News */}
        <div className="lg:col-span-4 space-y-6">
          <div className="bg-slate-900/60 border border-slate-800 rounded-[2rem] p-6 shadow-xl">
            <h3 className="font-bold text-lg mb-6 flex items-center gap-2">
              <Newspaper size={20} className="text-blue-400" />
              חדשות בזמן אמת
            </h3>
            <div className="space-y-6">
              {news.map((item, i) => (
                <div key={i} className="group cursor-pointer">
                  <h4 className="text-sm font-bold group-hover:text-blue-400 transition-colors mb-2 leading-snug">{item.title}</h4>
                  <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed mb-3">{item.summary}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-slate-600 font-mono">לפני 12 דק'</span>
                    <span className="bg-slate-800 px-2 py-0.5 rounded text-[10px] text-blue-300 font-bold uppercase">{ticker}</span>
                  </div>
                  {i < news.length - 1 && <div className="h-px bg-gradient-to-r from-transparent via-slate-800 to-transparent mt-6" />}
                </div>
              ))}
            </div>
            <button className="w-full mt-8 py-3 bg-slate-800/50 hover:bg-slate-800 rounded-xl text-xs font-bold text-slate-400 hover:text-white transition-all">צפה בכל הפיד</button>
          </div>
          
          <div className="bg-gradient-to-br from-blue-600/10 to-transparent border border-blue-500/20 p-6 rounded-[2rem]">
            <div className="flex items-center gap-3 mb-4">
              <AlertCircle size={20} className="text-blue-400" />
              <h4 className="font-bold text-sm">ניטור דוחות פעיל</h4>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed italic">
              "המערכת מנתחת דוחות 10-K/Q באופן אוטומטי. שים לב לשינויים ב-Guidance של ההנהלה, ה-AI נותן לכך משקל גבוה בניתוח הסנטימנט."
            </p>
          </div>
        </div>
      </main>

      <style dangerouslySetInnerHTML={{ __html: `
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
      `}} />
    </div>
  );
};

export default App;
