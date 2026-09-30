export const StatCard = ({ title, value, subValue, trend, icon: Icon, colorClass }: any) => (
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
