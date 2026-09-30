export const ProvenanceFooter = ({ dataset, updated }: any) => (
  <div className="mt-4 pt-3 border-t border-slate-100 text-[10px] text-slate-400 flex flex-wrap gap-x-4 gap-y-1 justify-between">
    <div><span className="font-medium text-slate-500">Source:</span> APIx live scraper</div>
    <div><span className="font-medium text-slate-500">Dataset:</span> {dataset || 'N/A'}</div>
    <div><span className="font-medium text-slate-500">Method:</span> Jevons weighted index</div>
    <div><span className="font-medium text-slate-500">Updated:</span> {updated ? new Date(updated).toLocaleString() : 'N/A'}</div>
  </div>
);
