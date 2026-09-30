import { Play, Activity, ShieldCheck, Zap, Plane } from 'lucide-react';

export const LandingPage = ({ onLaunch }: { onLaunch: () => void }) => {
  return (
    <div className="min-h-screen bg-[#0B1F3A] flex flex-col items-center justify-center relative overflow-hidden text-white font-sans">
      {/* Decorative Background Elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-[#1F3C88] blur-[120px] opacity-40 mix-blend-screen" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-[#FF9933] blur-[150px] opacity-20 mix-blend-screen" />
      
      {/* Tri-color Top Bar */}
      <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-[#FF9933] via-white to-[#138808]" />

      <div className="relative z-10 flex flex-col items-center text-center max-w-4xl px-6">
        
        {/* Emblem / Icon */}
        <div className="mb-8 relative group">
          <div className="absolute inset-0 bg-blue-500 rounded-full blur-xl opacity-30 group-hover:opacity-60 transition-opacity duration-700" />
          <div className="relative bg-white/5 p-6 rounded-3xl border border-white/10 backdrop-blur-md">
            <Plane size={64} className="text-white -rotate-45" strokeWidth={1.5} />
          </div>
        </div>

        {/* Title */}
        <h1 className="text-5xl md:text-7xl font-bold font-[Poppins] tracking-tight mb-6 text-transparent bg-clip-text bg-gradient-to-br from-white to-blue-200 leading-tight drop-shadow-sm">
          APIx
        </h1>
        <h2 className="text-2xl md:text-3xl font-light text-blue-100 mb-8 tracking-wide">
          Real-time Airfare Price Index
        </h2>

        {/* Subtitle / Mission */}
        <p className="text-lg text-blue-200/80 mb-12 max-w-2xl leading-relaxed font-light">
          A high-frequency macroeconomic data engine built for the Ministry of Statistics and Programme Implementation (MoSPI). 
          Empowering economists to track inflation and dynamic pricing in India's aviation sector.
        </p>

        {/* Action Button */}
        <button 
          onClick={onLaunch}
          className="group relative inline-flex items-center gap-3 px-8 py-4 bg-white text-[#0B1F3A] rounded-full font-bold text-lg overflow-hidden hover:scale-105 transition-transform duration-300 shadow-[0_0_40px_rgba(255,255,255,0.2)]"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-blue-50 to-white opacity-0 group-hover:opacity-100 transition-opacity" />
          <span className="relative z-10">Access Dashboard</span>
          <Play size={20} className="relative z-10 group-hover:translate-x-1 transition-transform" />
        </button>

        {/* Footer badges */}
        <div className="mt-20 flex flex-wrap justify-center gap-6 opacity-60 text-sm">
          <div className="flex items-center gap-2"><Activity size={16}/> Jevons Index</div>
          <div className="flex items-center gap-2"><ShieldCheck size={16}/> DGCA Validated</div>
          <div className="flex items-center gap-2"><Zap size={16}/> Real-time Extraction</div>
        </div>
      </div>
    </div>
  );
};
