import React from 'react';

const KPICard = ({ title, value, subtitle, icon: Icon, color = 'indigo' }) => {
  return (
    <div className="bg-white rounded-xl shadow-sm p-6 border border-slate-100 flex items-start space-x-4 transition-all hover:shadow-md">
      <div className={`p-3 rounded-lg bg-${color}-50 text-${color}-600`}>
        {Icon && <Icon size={24} />}
      </div>
      <div>
        <h3 className="text-sm font-medium text-slate-500 mb-1">{title}</h3>
        <p className="text-2xl font-bold text-slate-800">{value}</p>
        {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
      </div>
    </div>
  );
};

export default KPICard;
