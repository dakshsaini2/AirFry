import { useEffect, useState } from 'react';
import { Download, Play, Plane, Activity, Calendar, ShieldCheck, Zap } from 'lucide-react';
import ReactEcharts from 'echarts-for-react';
import * as api from './api';
import './index.css';

const INR = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 });
const formatVal = (v: number | undefined) => v !== undefined ? (v > 0 ? `+${v}%` : `${v}%`) : '-';

const StatCard = ({ title, value, subValue, trend, icon: Icon, colorClass }: any) => (
  <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
    <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${colorClass} opacity-10 rounded-bl-[100px] -z-10 group-hover:scale-110 transition-transform`} />
    <div className="flex justify-between items-start mb-4">
      <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">{title}</h3>
      <div className={`p-2 rounded-lg bg-slate-50 text-slate-600`}>
        <Icon size={20} />
      </div>
    </div>
    <div className="flex flex-col gap-1">
      <span className="text-3xl font-bold text-[#0B1F3A] font-[Poppins]">{value}</span>
      {subValue && (
        <span className={`text-sm font-medium ${trend === 'up' ? 'text-red-500' : trend === 'down' ? 'text-green-600' : 'text-slate-500'}`}>
          {subValue}
        </span>
      )}
    </div>
  </div>
);

export default function App() {
  const [filters, setFilters] = useState({ freq: 'D', lead: 'all', carrier: 'all', route: 'all' });
  const [options, setOptions] = useState({ leads: [], carriers: [], routes: [] });
  const [data, setData] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);

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

  if (loading && !data.summary) {
    return <div className="h-screen w-screen flex items-center justify-center bg-[#F3F5F9]"><div className="animate-spin text-[#1F3C88]"><Activity size={48}/></div></div>;
  }

  return (
    <div className="min-h-screen pb-12 font-sans bg-[#F3F5F9] text-[#16223A]">
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
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 bg-white/10 px-4 py-2 rounded-full border border-white/20 backdrop-blur-sm">
              <div className={`w-2.5 h-2.5 rounded-full ${loading ? 'bg-yellow-400 animate-pulse' : 'bg-green-400'}`} />
              <span className="text-sm font-medium">Live &middot; {new Date(data.summary?.last_run || Date.now()).toLocaleTimeString()}</span>
            </div>
            <a href="http://localhost:8000/docs" target="_blank" className="text-sm hover:bg-white/10 px-4 py-2 rounded-full transition-colors border border-transparent hover:border-white/30">API Docs</a>
          </div>
        </div>
      </header>

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

        {/* KPIs */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard title="APIx Latest" value={data.summary?.latest} subValue="Index Value" icon={Activity} colorClass="from-blue-400 to-blue-600" />
          <StatCard title="DoD Change" value={formatVal(data.summary?.dod)} trend={data.summary?.dod >= 0 ? 'up' : 'down'} icon={Calendar} colorClass="from-orange-400 to-orange-600" />
          <StatCard title="Avg Total Fare" value={INR.format(data.summary?.avg_fare || 0)} subValue="Aggregate" icon={Plane} colorClass="from-green-400 to-green-600" />
          <StatCard title="Clean Quotes" value={(data.summary?.quotes || 0).toLocaleString()} subValue="Used in index" icon={ShieldCheck} colorClass="from-purple-400 to-purple-600" />
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 h-[380px] flex flex-col">
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
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 h-[380px] flex flex-col">
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
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 h-[400px] flex flex-col">
            <h3 className="font-[Poppins] font-semibold text-lg text-[#0B1F3A] flex items-center gap-2 mb-4">
              <span className="w-1.5 h-6 bg-[#FF9933] rounded-full inline-block" /> Fare Composition by Carrier
            </h3>
            <div className="flex-1 min-h-0">
              {data.carriers && <ReactEcharts option={{
                tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, backgroundColor: 'rgba(255,255,255,0.95)' },
                legend: { top: 0, textStyle: { color: '#64748b' } },
                grid: { top: 40, right: 10, bottom: 20, left: 50, containLabel: true },
                xAxis: { type: 'category', data: data.carriers.carriers, axisLine: { lineStyle: { color: '#cbd5e1' } } },
                yAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } } },
                series: [
                  { name: 'Base Fare', type: 'bar', stack: 'total', itemStyle: { color: '#0B1F3A' }, data: data.carriers.base },
                  { name: 'Taxes', type: 'bar', stack: 'total', itemStyle: { color: '#1F3C88' }, data: data.carriers.taxes },
                  { name: 'UDF', type: 'bar', stack: 'total', itemStyle: { color: '#FF9933' }, data: data.carriers.udf },
                  { name: 'Convenience', type: 'bar', stack: 'total', data: data.carriers.convenience, barWidth: '40%', itemStyle: { borderRadius: [4,4,0,0], color: '#138808' } }
                ]
              }} style={{height: '100%', width: '100%'}} />}
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 h-[400px] flex flex-col">
            <h3 className="font-[Poppins] font-semibold text-lg text-[#0B1F3A] flex items-center gap-2 mb-4">
              <span className="w-1.5 h-6 bg-[#0B1F3A] rounded-full inline-block" /> Backtest vs DGCA
            </h3>
            <div className="flex-1 min-h-0 mb-4">
              {data.backtest && <ReactEcharts option={{
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
            {data.backtest && data.backtest.status !== 'insufficient_data' && data.backtest.status !== 'source_unavailable' ? (
               <div className="text-xs flex gap-4 text-slate-500 overflow-x-auto pb-2">
                 {data.backtest.rows.map((r:any, i:number) => (
                   <div key={i} className="bg-slate-50 px-3 py-2 rounded-lg border border-slate-100 whitespace-nowrap">
                     <span className="block font-semibold text-[#0B1F3A]">{r.month}</span>
                     Error: <span className={Math.abs(r.error_pct) > 10 ? 'text-red-500 font-medium' : 'text-green-600 font-medium'}>{r.error_pct}%</span>
                   </div>
                 ))}
               </div>
            ) : data.backtest?.status === 'source_unavailable' ? (
                <div className="text-xs text-amber-600 p-2 bg-amber-50 rounded">○ OFFICIAL DATA NOT CONFIGURED</div>
            ) : (
                <div className="text-xs text-red-500 p-2 bg-red-50 rounded">Insufficient Data for Backtest</div>
            )}
          </div>
          
          {/* Validation Metrics & Data Status */}
          {data.backtest && (
            <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col mt-6">
              <h3 className="font-[Poppins] font-semibold text-lg text-[#0B1F3A] flex items-center gap-2 mb-4">
                <span className="w-1.5 h-6 bg-pink-500 rounded-full inline-block" /> Data Status & Statistical Validation
              </h3>

              {data.backtest.status === 'source_unavailable' && (
                <div className="mb-4 p-3 bg-amber-50 border border-amber-200 text-amber-800 rounded-lg text-sm flex gap-2 items-start">
                  <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                  <div>
                    <strong>○ OFFICIAL DATA NOT CONFIGURED</strong><br/>
                    Permitted live data source or actual official DGCA data dump is required for empirical validation. Do not generate synthetic substitutes.
                  </div>
                </div>
              )}
              {data.backtest.data_mode === 'synthetic' && data.backtest.status !== 'source_unavailable' && (
                <div className="mb-4 p-3 bg-amber-50 border border-amber-200 text-amber-800 rounded-lg text-sm flex gap-2 items-start">
                  <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                  <div>
                    <strong>⚠ DEVELOPMENT DATA</strong><br/>
                    The current data is programmatically generated (synthetic). Statistics shown are for development testing of the pipeline only and are <strong>NOT valid as empirical validation</strong>.
                  </div>
                </div>
              )}
              {data.backtest.data_mode === 'official' && (
                <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-800 rounded-lg text-sm flex gap-2 items-start">
                  <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/></svg>
                  <div>
                    <strong>✓ OFFICIAL VALIDATION DATA</strong><br/>
                    This data is sourced from an authoritative official source and is eligible for empirical validation.
                  </div>
                </div>
              )}

              {data.validation && data.validation.status !== 'insufficient_data' && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 text-center">
                    <div className="text-sm font-semibold text-slate-500 mb-1">Pearson Correlation</div>
                    <div className="text-2xl font-bold text-slate-800">{data.validation.pearson?.toFixed(2) || 'N/A'}</div>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 text-center">
                    <div className="text-sm font-semibold text-slate-500 mb-1">Spearman Rank</div>
                    <div className="text-2xl font-bold text-slate-800">{data.validation.spearman?.toFixed(2) || 'N/A'}</div>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 text-center">
                    <div className="text-sm font-semibold text-slate-500 mb-1">MAPE</div>
                    <div className="text-2xl font-bold text-slate-800">{data.validation.mape ? data.validation.mape.toFixed(1) + '%' : 'N/A'}</div>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 text-center">
                    <div className="text-sm font-semibold text-slate-500 mb-1">Directional Accuracy</div>
                    <div className="text-2xl font-bold text-slate-800">{data.validation.direction_accuracy ? data.validation.direction_accuracy.toFixed(1) + '%' : 'N/A'}</div>
                  </div>
                </div>
              )}

              {data.validation && (
                <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                    <div className="font-bold text-[#0B1F3A] mb-2 uppercase tracking-wide">AIRFARE DATA</div>
                    <div className="flex flex-col gap-1 text-slate-600">
                      <div><span className="text-slate-400">Mode:</span> {data.validation.airfare_data_mode}</div>
                      <div><span className="text-slate-400">Dataset:</span> {data.validation.airfare_dataset_version}</div>
                      <div><span className="text-slate-400">Coverage:</span> {data.validation.days_available} days</div>
                    </div>
                  </div>
                  
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                    <div className="font-bold text-[#0B1F3A] mb-2 uppercase tracking-wide">DGCA DATA</div>
                    <div className="flex flex-col gap-1 text-slate-600">
                      <div><span className="text-slate-400">Mode:</span> {data.validation.dgca_data_mode}</div>
                      <div><span className="text-slate-400">Dataset:</span> {data.validation.dgca_dataset_version}</div>
                      <div><span className="text-slate-400">Coverage:</span> {data.validation.overlapping_days} overlap rows</div>
                    </div>
                  </div>
                  
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                    <div className="font-bold text-[#0B1F3A] mb-2 uppercase tracking-wide">WEIGHTS</div>
                    <div className="flex flex-col gap-1 text-slate-600">
                      <div><span className="text-slate-400">Version:</span> {data.validation.weight_version}</div>
                      <div><span className="text-slate-400">Mode:</span> synthetic</div>
                      <div><span className="text-slate-400">Methodology:</span> {data.validation.methodology_version}</div>
                    </div>
                  </div>

                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                    <div className="font-bold text-[#0B1F3A] mb-2 uppercase tracking-wide">VALIDATION</div>
                    <div className="flex flex-col gap-1 text-slate-600">
                      <div><span className="text-slate-400">Eligible:</span> <span className={data.validation.validation_eligible ? "text-green-600 font-bold" : "text-red-500 font-bold"}>{data.validation.validation_eligible ? "YES" : "NO"}</span></div>
                      <div><span className="text-slate-400">Eligible days:</span> {data.validation.eligible_days}</div>
                      <div><span className="text-slate-400">Status:</span> <span className="uppercase">{data.validation.status.replace(/_/g, ' ')}</span></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Heatmap & Data Quality */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-slate-100 overflow-hidden flex flex-col">
            <h3 className="font-[Poppins] font-semibold text-lg text-[#0B1F3A] flex items-center gap-2 mb-4">
              <span className="w-1.5 h-6 bg-purple-500 rounded-full inline-block" /> Sector Heatmap (Avg Fare)
            </h3>
            <div className="overflow-x-auto flex-1">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wide text-xs">
                    <th className="py-3 px-4">Route</th>
                    {data.heatmap?.leads.map((l:any) => <th key={l} className="py-3 px-4 text-right">T+{l}</th>)}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.heatmap?.routes.map((r:any, i:number) => {
                    const rowVals = data.heatmap.z[i];
                    const min = Math.min(...data.heatmap.z.flat());
                    const max = Math.max(...data.heatmap.z.flat());
                    return (
                      <tr key={r} className="hover:bg-slate-50">
                        <td className="py-2.5 px-4 font-medium text-slate-700">{r}</td>
                        {rowVals.map((v:number, j:number) => {
                          const t = (v - min) / (max - min);
                          // blue to orange to red scale
                          const bg = `hsla(${220 - t*200}, 80%, ${95 - t*40}%, 1)`;
                          const col = t > 0.5 ? '#fff' : '#0f172a';
                          return (
                            <td key={j} className="py-1 px-1">
                              <div className="px-2 py-1.5 rounded-lg text-right font-medium transition-colors cursor-default hover:opacity-80 text-xs sm:text-sm" style={{backgroundColor: bg, color: col}}>
                                {INR.format(v)}
                              </div>
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
            <h3 className="font-[Poppins] font-semibold text-lg text-[#0B1F3A] flex items-center gap-2 mb-4">
              <span className="w-1.5 h-6 bg-slate-800 rounded-full inline-block" /> Pipeline Quality
            </h3>
            <div className="space-y-4">
              {data.quality && Object.entries(data.quality).map(([k, v]:any) => (
                <div key={k} className="flex justify-between items-center p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-sm font-medium text-slate-600 capitalize">{k.replace(/_/g, ' ')}</span>
                  <span className="font-bold text-slate-900">{typeof v === 'number' ? v.toLocaleString() : v}</span>
                </div>
              ))}
              <div className="mt-6 pt-6 border-t border-slate-100">
                <div className="bg-blue-50 text-blue-800 text-xs font-medium p-3 rounded-lg border border-blue-100 flex items-start gap-2">
                  <Zap size={14} className="mt-0.5 shrink-0 text-blue-600" />
                  <p>Quality checks run automatically via Great Expectations after every scraping cycle to enforce bounds and missing data rules.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Fare Explorer */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col">
           <h3 className="font-[Poppins] font-semibold text-lg text-[#0B1F3A] flex items-center gap-2 mb-4">
              <span className="w-1.5 h-6 bg-cyan-500 rounded-full inline-block" /> Live Fare Explorer (Cleaned)
            </h3>
            <div className="overflow-x-auto max-h-[400px]">
              <table className="w-full text-sm text-left whitespace-nowrap">
                <thead className="bg-slate-50 sticky top-0 z-10 shadow-sm shadow-slate-100/50">
                  <tr className="text-slate-500 font-semibold text-xs uppercase tracking-wider">
                    <th className="py-3 px-4 rounded-tl-xl">Date</th>
                    <th className="py-3 px-4">Route</th>
                    <th className="py-3 px-4">Carrier</th>
                    <th className="py-3 px-4">Source</th>
                    <th className="py-3 px-4 text-center">Lead</th>
                    <th className="py-3 px-4 text-right">Base</th>
                    <th className="py-3 px-4 text-right">Taxes</th>
                    <th className="py-3 px-4 text-right">UDF</th>
                    <th className="py-3 px-4 text-right">Conv.</th>
                    <th className="py-3 px-4 text-right rounded-tr-xl">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.fares?.map((f:any, i:number) => (
                    <tr key={i} className="hover:bg-blue-50/50 transition-colors">
                      <td className="py-2.5 px-4 text-slate-500">{f.date}</td>
                      <td className="py-2.5 px-4 font-semibold text-slate-700">{f.route}</td>
                      <td className="py-2.5 px-4">
                        <span className="bg-slate-100 text-slate-700 px-2.5 py-1 rounded-md text-xs font-medium">{f.carrier}</span>
                      </td>
                      <td className="py-2.5 px-4 text-slate-600 text-xs">{f.source}</td>
                      <td className="py-2.5 px-4 text-center">
                        <span className="bg-blue-50 text-blue-700 font-semibold px-2 py-0.5 rounded text-xs">T+{f.lead}</span>
                      </td>
                      <td className="py-2.5 px-4 text-right text-slate-500">{INR.format(f.base)}</td>
                      <td className="py-2.5 px-4 text-right text-slate-500">{INR.format(f.taxes)}</td>
                      <td className="py-2.5 px-4 text-right text-slate-500">{INR.format(f.udf)}</td>
                      <td className="py-2.5 px-4 text-right text-slate-500">{INR.format(f.convenience)}</td>
                      <td className="py-2.5 px-4 text-right font-bold text-[#0B1F3A]">{INR.format(f.total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
        </div>

      </main>
    </div>
  );
}
