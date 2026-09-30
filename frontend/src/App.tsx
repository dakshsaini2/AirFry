import { useEffect, useState } from 'react';
import { Download, Play, Plane, Activity, Calendar, ShieldCheck, Info, X } from 'lucide-react';
import ReactEcharts from 'echarts-for-react';
import * as api from './api';
import './index.css';

import { LandingPage } from './components/LandingPage';
import { StatCard } from './components/StatCard';
import { ProvenanceFooter } from './components/ProvenanceFooter';

const INR = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 });
const formatVal = (v: number | undefined) => v !== undefined ? (v > 0 ? `+${v}%` : `${v}%`) : '-';

export default function App() {
  const [showLanding, setShowLanding] = useState(true);
  const [filters, setFilters] = useState({ freq: 'D', lead: 'all', carrier: 'all', route: 'all' });
  const [options, setOptions] = useState({ leads: [], carriers: [], routes: [] });
  const [data, setData] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);
  const [showMethodology, setShowMethodology] = useState(false);

  const fetchOptions = async () => {
    try {
      const res = await api.getRoutes();
      setOptions(res);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const p1 = { lead: filters.lead, carrier: filters.carrier };
      const [sum, idx, el, hm, cr, bt, q, f, mos, vr] = await Promise.all([
        api.getSummary(p1),
        api.getIndex({ freq: filters.freq, ...p1 }),
        api.getElasticity({ route: filters.route }),
        api.getHeatmap(),
        api.getCarriers(),
        api.getBacktest(),
        api.getQuality(),
        api.getFares({ route: filters.route, ...p1, limit: 100 }),
        api.getMospi(),
        api.getValidationReport()
      ]);
      setData({ summary: sum, index: idx, elasticity: el, heatmap: hm, carriers: cr, backtest: bt, quality: q, fares: f, mospi: mos, validation: vr });
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOptions();
  }, []);

  useEffect(() => {
    if (options.routes.length) {
      fetchData();
    }
  }, [filters, options]);

  const handleScrape = async () => {
    setScraping(true);
    await api.runScrape();
    await fetchData();
    setScraping(false);
  };

  const exportCSV = () => {
    if (!data.index) return;
    const csv = "date,apix\n" + data.index.dates.map((d: string, i: number) => `${d},${data.index.values[i]}`).join("\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([csv]));
    a.download = "apix.csv";
    a.click();
  };

  if (showLanding) {
    return <LandingPage onLaunch={() => setShowLanding(false)} />;
  }

  if (loading && !data.summary) {
    return <div className="h-screen w-screen flex items-center justify-center bg-[#F3F5F9]"><div className="animate-spin text-[#1F3C88]"><Activity size={48}/></div></div>;
  }

  const isOfficial = data.backtest?.data_mode === 'official';
  const dataModeLabel = (data.backtest?.data_mode || 'UNKNOWN').toUpperCase();
  const datasetVersion = data.backtest?.airfare_dataset_version || 'N/A';
  const isVerified = data.backtest?.validation_eligible && isOfficial;
  
  return (
    <div className="min-h-screen pb-12 font-sans bg-[#F3F5F9] text-[#16223A] relative">
      
      {/* Methodology Drawer Overlay */}
      {showMethodology && (
        <div className="fixed inset-0 bg-slate-900/40 z-50 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-md bg-white h-full shadow-2xl p-6 overflow-y-auto animate-in slide-in-from-right duration-300">
            <div className="flex justify-between items-center mb-6 border-b border-slate-100 pb-4">
              <h2 className="text-xl font-[Poppins] font-bold text-[#0B1F3A]">APIx Methodology</h2>
              <button onClick={() => setShowMethodology(false)} className="p-2 hover:bg-slate-100 rounded-full"><X size={20}/></button>
            </div>
            
            <div className="space-y-6 text-sm text-slate-700">
              <section>
                <h3 className="font-bold text-slate-900 mb-2">Route Weights</h3>
                <p>Top 10 highest volume domestic routes weighted by DGCA trailing 12-month passenger traffic share. Base weights range from ~20% (DEL-BOM) to ~6% (BOM-GOI).</p>
              </section>
              <section>
                <h3 className="font-bold text-slate-900 mb-2">Carrier Weights</h3>
                <p>Implicitly weighted by scrape volume mapping to actual market share (IndiGo ~60%, Air India Group ~25%, etc.). A carrier multiplier is applied to align base prices structurally.</p>
              </section>
              <section>
                <h3 className="font-bold text-slate-900 mb-2">Lead-time Distribution</h3>
                <p>Equally weighted across T+1, T+7, T+15, T+30, T+45 days to capture both immediate dynamic pricing and long-term base pricing.</p>
              </section>
              <section>
                <h3 className="font-bold text-slate-900 mb-2">Jevons Formula</h3>
                <p>The index uses a Jevons (Geometric Mean of Price Relatives) formula. It aggregates logarithmic price changes to satisfy time-reversal and circularity tests, making it robust against dynamic pricing spikes.</p>
              </section>
              <section>
                <h3 className="font-bold text-slate-900 mb-2">Base Period</h3>
                <p>The base period is set as the first 7 days of observation (Index = 100). All subsequent index values are geometric relatives to this baseline.</p>
              </section>
              <section>
                <h3 className="font-bold text-slate-900 mb-2">Outlier Treatment</h3>
                <p>Median Absolute Deviation (MAD) is used to reject values where `(0.6745 * |log_fare - median_log|) / MAD &gt; 3.5`. This prevents single erroneous API spikes from distorting the index.</p>
              </section>
              <section>
                <h3 className="font-bold text-slate-900 mb-2">Missing/Sold-out</h3>
                <p>Missing taxes are imputed using the route+lead median. Sold-out flights are dropped prior to the geometric mean calculation.</p>
              </section>
            </div>
          </div>
        </div>
      )}

      {/* Tri-color Top Bar */}
      <div className="h-2 w-full bg-gradient-to-r from-[#FF9933] via-white to-[#138808]" />
      
      {/* Header */}
      <header className="bg-gradient-to-r from-[#0B1F3A] to-[#1F3C88] text-white px-8 py-6 shadow-md relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
          <Plane size={150} className="-rotate-45" />
        </div>
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative z-10">
          <div>
            <h1 className="text-2xl md:text-3xl font-[Poppins] font-bold tracking-tight mb-1 flex items-center gap-3">
              APIx <span className="opacity-50 text-xl font-light">|</span> <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-100 to-white">Real-time Airfare Price Index</span>
            </h1>
            <p className="text-blue-200 text-sm font-medium tracking-wide">NSO / MoSPI &middot; RBI consumption &middot; CPI Transport &amp; Communication</p>
          </div>
          
          <div className="flex flex-col items-end gap-2">
            <div className="flex items-center gap-3">
              <div className={`px-4 py-1.5 rounded-full border flex items-center gap-2 font-bold text-sm tracking-wider shadow-inner ${
                isOfficial 
                  ? 'bg-green-500/20 border-green-400 text-green-300' 
                  : 'bg-amber-500/20 border-amber-400 text-amber-300'
              }`}>
                <div className={`w-2 h-2 rounded-full ${isOfficial ? 'bg-green-400' : 'bg-amber-400 animate-pulse'}`} />
                {dataModeLabel} MODE
              </div>
              <button onClick={() => setShowMethodology(true)} className="flex items-center gap-2 text-sm bg-white/10 hover:bg-white/20 px-4 py-1.5 rounded-full border border-white/20 backdrop-blur-sm transition-colors">
                <Info size={16} /> Methodology
              </button>
            </div>
            <div className="text-xs text-blue-200/70 font-medium text-right flex gap-3">
              <span>Source: Playwright Scrapers</span>
              <span>Dataset: {datasetVersion}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Alert Banners */}
      {!isOfficial && (
        <div className="bg-amber-50 border-b border-amber-200 text-amber-800 px-6 py-3 text-sm font-medium text-center">
          <span className="font-bold uppercase mr-2 tracking-wide">Development / Synthetic Data:</span> 
          Not for empirical validation. The current data is programmatic fixture data used for pipeline testing.
        </div>
      )}

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8 space-y-8">
        
        {/* Controls */}
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 flex flex-wrap gap-4 items-center justify-between sticky top-4 z-40 backdrop-blur-xl bg-white/80">
          <div className="flex flex-wrap gap-3">
            <select className="border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-medium focus:ring-2 focus:ring-[#1F3C88] focus:border-transparent outline-none bg-white" 
              value={filters.freq} onChange={e => setFilters({...filters, freq: e.target.value})}>
              <option value="D">Daily Frequency</option>
              <option value="W">Weekly Frequency</option>
              <option value="M">Monthly Frequency</option>
            </select>
            <select className="border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-medium focus:ring-2 focus:ring-[#1F3C88] focus:border-transparent outline-none bg-white"
              value={filters.lead} onChange={e => setFilters({...filters, lead: e.target.value})}>
              <option value="all">All Lead Times</option>
              {options.leads.map((l: any) => <option key={l} value={l}>T+{l} Days</option>)}
            </select>
            <select className="border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-medium focus:ring-2 focus:ring-[#1F3C88] focus:border-transparent outline-none bg-white"
              value={filters.carrier} onChange={e => setFilters({...filters, carrier: e.target.value})}>
              <option value="all">All Carriers</option>
              {options.carriers.map((c: any) => <option key={c} value={c}>{c}</option>)}
            </select>
            <select className="border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-medium focus:ring-2 focus:ring-[#1F3C88] focus:border-transparent outline-none bg-white"
              value={filters.route} onChange={e => setFilters({...filters, route: e.target.value})}>
              <option value="all">All Routes</option>
              {options.routes.map((r: any) => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div className="flex gap-3">
            <button onClick={exportCSV} className="flex items-center gap-2 px-5 py-2.5 rounded-xl border-2 border-[#1F3C88] text-[#1F3C88] font-semibold hover:bg-slate-50 transition-colors text-sm">
              <Download size={16} /> Export
            </button>
            <button onClick={handleScrape} disabled={scraping} className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#FF9933] to-[#e8851f] text-white font-semibold hover:shadow-lg hover:shadow-orange-500/20 transition-all text-sm disabled:opacity-50">
              {scraping ? <Activity size={16} className="animate-spin" /> : <Play size={16} />} 
              {scraping ? 'Collecting...' : 'Run Collection'}
            </button>
          </div>
        </div>

        {/* PROTOTYPE METRICS SECTION */}
        <div>
          <h2 className="text-xl font-bold text-[#0B1F3A] mb-4 font-[Poppins]">Prototype Metrics</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            <StatCard title="APIx Latest" value={data.summary?.latest} subValue="Index Value" icon={Activity} colorClass="from-blue-400 to-blue-600" />
            <StatCard title="DoD Change" value={formatVal(data.summary?.dod)} trend={data.summary?.dod >= 0 ? 'up' : 'down'} icon={Calendar} colorClass="from-orange-400 to-orange-600" />
            <StatCard title="Avg Total Fare" value={INR.format(data.summary?.avg_fare || 0)} subValue="Aggregate" icon={Plane} colorClass="from-green-400 to-green-600" />
            <StatCard title="Clean Quotes" value={(data.summary?.quotes || 0).toLocaleString()} subValue={`Valid ${dataModeLabel} observations`} icon={ShieldCheck} colorClass="from-purple-400 to-purple-600" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 h-[430px] flex flex-col">
              <h3 className="font-[Poppins] font-semibold text-lg text-[#0B1F3A] flex items-center gap-2 mb-4">
                <span className="w-1.5 h-6 bg-[#FF9933] rounded-full inline-block" /> Airfare Price Index (Base=100)
              </h3>
              <div className="flex-1 min-h-0">
                {data.index && <ReactEcharts option={{
                  tooltip: { trigger: 'axis', backgroundColor: 'rgba(255,255,255,0.95)', padding: 12, borderRadius: 8, borderColor: '#eee' },
                  grid: { top: 10, right: 10, bottom: 20, left: 40, containLabel: true },
                  xAxis: { type: 'category', boundaryGap: false, data: data.index.dates, axisLine: { lineStyle: { color: '#cbd5e1' } }, axisLabel: { color: '#64748b' } },
                  yAxis: { type: 'value', min: 'dataMin', splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } }, axisLabel: { color: '#64748b' } },
                  series: [{ name: 'APIx', type: 'line', smooth: 0.3, symbol: 'none', data: data.index.values, itemStyle: { color: '#1F3C88' }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(31,60,136,0.3)' }, { offset: 1, color: 'rgba(31,60,136,0)' }] } }, lineStyle: { width: 3 } }]
                }} style={{height: '100%', width: '100%'}} />}
              </div>
              <ProvenanceFooter dataset={datasetVersion} updated={data.summary?.last_run} />
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 h-[430px] flex flex-col">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-[Poppins] font-semibold text-lg text-[#0B1F3A] flex items-center gap-2">
                  <span className="w-1.5 h-6 bg-[#138808] rounded-full inline-block" /> Lead-time Elasticity
                </h3>
                <div className="px-3 py-1 bg-green-50 text-green-700 text-xs font-bold rounded-full border border-green-200">
                  T+1 Premium: {data.elasticity?.premium_t1_vs_t45_pct}%
                </div>
              </div>
              <div className="flex-1 min-h-0">
                {data.elasticity && <ReactEcharts option={{
                  tooltip: { trigger: 'axis', backgroundColor: 'rgba(255,255,255,0.95)' },
                  legend: { top: 0, itemWidth: 12, itemHeight: 12, textStyle: { color: '#64748b' } },
                  grid: { top: 40, right: 10, bottom: 20, left: 50, containLabel: true },
                  xAxis: { type: 'category', data: data.elasticity.leads.map((l:any) => `T+${l}`), axisLine: { lineStyle: { color: '#cbd5e1' } }, axisLabel: { color: '#64748b' } },
                  yAxis: { type: 'value', axisLabel: { formatter: '₹{value}', color: '#64748b' }, splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } } },
                  series: Object.entries(data.elasticity.series).map(([k, v]:any) => ({
                    name: k, type: 'line', smooth: 0.2, data: v, symbol: 'circle', symbolSize: 6, lineStyle: { width: 2 }
                  }))
                }} style={{height: '100%', width: '100%'}} />}
              </div>
              <ProvenanceFooter dataset={datasetVersion} updated={data.summary?.last_run} />
            </div>
          </div>
        </div>

        {/* OFFICIAL VALIDATION SECTION */}
        <div className="mt-12 pt-10 border-t-2 border-slate-200 border-dashed">
          <h2 className="text-xl font-bold text-[#0B1F3A] mb-6 font-[Poppins]">Official Validation Audit</h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            {/* Validation Card */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col justify-between">
              <div>
                <h3 className="font-bold text-slate-500 uppercase tracking-wide text-sm mb-4">Validation Status</h3>
                {isVerified ? (
                  <div className="bg-green-50 text-green-700 border border-green-200 p-4 rounded-xl flex items-center gap-3 mb-4">
                    <ShieldCheck size={32} className="text-green-600 flex-shrink-0" />
                    <div>
                      <div className="font-bold text-lg leading-tight">OFFICIAL VALIDATION VERIFIED</div>
                      <div className="text-xs text-green-600 mt-1">Empirical backtest meets requirements.</div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-amber-50 text-amber-800 border border-amber-200 p-4 rounded-xl flex items-start gap-3 mb-4">
                    <Info size={24} className="text-amber-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <div className="font-bold leading-tight">OFFICIAL VALIDATION NOT VERIFIED</div>
                      <div className="text-xs text-amber-700 mt-1">
                        Reason: {data.backtest?.data_mode !== 'official' ? 'Data is synthetic/not authorized.' : 'Insufficient DGCA overlap (< 30 days)'}
                      </div>
                    </div>
                  </div>
                )}
                
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between border-b border-slate-50 pb-2">
                    <span className="text-slate-500">DGCA reference:</span>
                    <span className="font-medium text-[#0B1F3A]">{data.backtest?.dgca_dataset_version !== 'N/A' ? 'Verified' : 'Not Verified'}</span>
                  </div>
                  <div className="flex justify-between border-b border-slate-50 pb-2">
                    <span className="text-slate-500">Overlap:</span>
                    <span className="font-medium text-[#0B1F3A]">{data.backtest?.dgca_records || 0} days</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Required:</span>
                    <span className="font-medium text-[#0B1F3A]">≥ 30 days</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Backtest vs DGCA Chart */}
            <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col relative">
              {!isVerified && (
                 <div className="absolute inset-0 bg-white/70 backdrop-blur-[2px] z-10 flex items-center justify-center rounded-2xl">
                    <div className="bg-white shadow-xl px-6 py-4 rounded-xl border border-slate-200 text-center">
                      <ShieldCheck size={32} className="mx-auto text-slate-300 mb-2" />
                      <div className="font-bold text-slate-800">Results Hidden</div>
                      <div className="text-sm text-slate-500">Official validation required to view backtest results</div>
                    </div>
                 </div>
              )}
              
              <h3 className="font-[Poppins] font-semibold text-lg text-[#0B1F3A] flex items-center gap-2 mb-4">
                <span className="w-1.5 h-6 bg-[#0B1F3A] rounded-full inline-block" /> Backtest vs DGCA Historical
              </h3>
              <div className="flex-1 min-h-0 mb-4">
                {data.backtest && isVerified && <ReactEcharts option={{
                  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
                  legend: { top: 0 },
                  grid: { top: 30, right: 10, bottom: 20, left: 40, containLabel: true },
                  xAxis: { type: 'category', data: data.backtest.rows.map((r:any) => r.month) },
                  yAxis: { type: 'value', min: 'dataMin' },
                  series: [
                    { name: 'DGCA Avg', type: 'bar', itemStyle: { color: '#94a3b8', borderRadius: [4,4,0,0] }, data: data.backtest.rows.map((r:any) => r.avg_fare_inr) },
                    { name: 'APIx Avg', type: 'bar', itemStyle: { color: '#FF9933', borderRadius: [4,4,0,0] }, data: data.backtest.rows.map((r:any) => r.apix_avg_fare) }
                  ]
                }} style={{height: '100%', width: '100%'}} />}
              </div>
              {data.backtest && isVerified && (
                 <div className="text-xs flex gap-4 text-slate-500 overflow-x-auto pb-2">
                   {data.backtest.rows.map((r:any, i:number) => (
                     <div key={i} className="bg-slate-50 px-3 py-2 rounded-lg border border-slate-100 whitespace-nowrap">
                       <span className="block font-semibold text-[#0B1F3A]">{r.month}</span>
                       Error: <span className={Math.abs(r.error_pct) > 10 ? 'text-amber-500 font-medium' : 'text-green-600 font-medium'}>{r.error_pct}%</span>
                     </div>
                   ))}
                 </div>
              )}
              <ProvenanceFooter dataset={data.backtest?.dgca_dataset_version} updated={data.summary?.last_run} />
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
            <h3 className="font-[Poppins] font-semibold text-[#0B1F3A] mb-3">Data Limitations (Prototype Note)</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 text-sm text-slate-600">
              <div>
                <strong className="text-slate-800 block mb-1">Asking Fares vs Transaction Fares</strong>
                APIx measures real-time asking fares (posted prices), while DGCA historical data is based on realized transaction fares which factor in last-minute deals or bulk corporate discounts.
              </div>
              <div>
                <strong className="text-slate-800 block mb-1">Tax & Fee Differences</strong>
                Convenience fees vary wildly between Direct Airlines and OTAs. DGCA data may not include OTA convenience fees or seat selection add-ons that APIx captures.
              </div>
              <div>
                <strong className="text-slate-800 block mb-1">Dynamic Pricing Volatility</strong>
                Scraping availability is subject to strict WAF rate limits. Brief outages during scraping windows can slightly shift the Jevons geometric mean if major routes are temporarily dropped.
              </div>
            </div>
          </div>
        </div>

        {/* Pipeline Details */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
           <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
             <h3 className="font-[Poppins] font-semibold text-lg text-[#0B1F3A] mb-4">Pipeline Quality Checks</h3>
             <div className="space-y-4">
              {data.quality && Object.entries(data.quality).map(([k, v]:any) => (
                <div key={k} className="flex justify-between items-center p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-sm font-medium text-slate-600 capitalize">{k.replace(/_/g, ' ')}</span>
                  <span className="font-bold text-slate-900">{typeof v === 'number' ? v.toLocaleString() : v}</span>
                </div>
              ))}
              <div className="mt-4 text-xs text-slate-400 bg-slate-50 p-3 rounded-xl border border-slate-100">
                Quality checks run automatically via Great Expectations after every scraping cycle to enforce bounds and missing data rules.
              </div>
            </div>
           </div>
        </div>

      </main>
    </div>
  );
}
