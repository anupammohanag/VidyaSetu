import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { 
  School, Users, CalendarCheck, AlertTriangle, Building, BookOpen, AlertCircle
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer 
} from 'recharts';
import KPICard from '../components/KPICard';
import AIAgent from '../components/AIAgent';

const DashboardPage = () => {
  const [summary, setSummary] = useState(null);
  const [trend, setTrend] = useState([]);
  const [riskSchools, setRiskSchools] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sumRes, trendRes, riskRes] = await Promise.all([
          axios.get('/api/dashboard/summary'),
          axios.get('/api/attendance/trend'),
          axios.get('/api/risk/schools')
        ]);
        setSummary(sumRes.data);
        setTrend(trendRes.data);
        setRiskSchools(riskRes.data);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
      setLoading(false);
    };
    fetchData();
  }, []);

  if (loading) {
    return <div className="flex h-64 items-center justify-center text-indigo-600 font-semibold text-xl animate-pulse">Loading dashboard...</div>;
  }

  if (!summary) {
    return <div className="text-red-500 font-medium">Failed to load data. Please ensure the backend is running.</div>;
  }

  return (
    <div className="space-y-6">
      {/* KPI Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Total Schools" value={summary.total_schools} icon={School} color="blue" />
        <KPICard title="Students Tracked" value={summary.students_tracked} icon={Users} color="indigo" />
        <KPICard title="Average Attendance" value={`${summary.avg_attendance}%`} icon={CalendarCheck} color="green" />
        <KPICard title="Proxy Attendance Rate" value={`${summary.proxy_rate}%`} icon={AlertTriangle} color="amber" subtitle="Requires verification" />
        <KPICard title="Avg Infra Deficit" value={`${summary.infra_deficit}%`} icon={Building} color="slate" />
        <KPICard title="Average FLN Score" value={`${summary.avg_fln}%`} icon={BookOpen} color="purple" />
        <KPICard title="High Risk Schools" value={summary.high_risk_schools} icon={AlertCircle} color="red" subtitle="Urgent intervention needed" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Charts & Tables */}
        <div className="lg:col-span-2 space-y-6">
          {/* Chart Card */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
            <h2 className="text-lg font-bold text-slate-800 mb-4">Monthly Attendance Trend</h2>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trend}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="month" tick={{fill: '#64748b'}} />
                  <YAxis domain={[0, 100]} tick={{fill: '#64748b'}} />
                  <Tooltip 
                    contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}} 
                  />
                  <Line type="monotone" dataKey="att_rate" name="Attendance Rate (%)" stroke="#4f46e5" strokeWidth={3} dot={{r: 4, strokeWidth: 2}} activeDot={{r: 6}} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Risk Table */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
            <div className="p-6 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
              <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                <AlertTriangle size={20} className="text-red-500" />
                Priority Schools for Intervention
              </h2>
            </div>
            <div className="overflow-x-auto max-h-80">
              <table className="w-full text-left text-sm">
                <thead className="bg-white sticky top-0 border-b border-slate-100 shadow-sm z-10 text-slate-500 font-medium">
                  <tr>
                    <th className="px-6 py-3">School</th>
                    <th className="px-6 py-3">District</th>
                    <th className="px-6 py-3">Risk Category</th>
                    <th className="px-6 py-3 w-1/3">Risk Factors</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {riskSchools.filter(s => s.risk_category === 'HIGH').slice(0, 10).map((school, i) => (
                    <tr key={i} className="hover:bg-slate-50 transition-colors">
                      <td className="px-6 py-4 font-medium text-slate-800">{school.school_name} <br/><span className="text-xs text-slate-400">{school.school_id_clean}</span></td>
                      <td className="px-6 py-4 text-slate-600">{school.district}</td>
                      <td className="px-6 py-4">
                        <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-700">HIGH</span>
                      </td>
                      <td className="px-6 py-4">
                        <ul className="list-disc pl-4 text-slate-600 text-xs space-y-1">
                          {school.risk_reasons.map((r, idx) => (
                            <li key={idx}>{r}</li>
                          ))}
                          {school.risk_reasons.length === 0 && <li>Unknown factors</li>}
                        </ul>
                      </td>
                    </tr>
                  ))}
                  {riskSchools.filter(s => s.risk_category === 'HIGH').length === 0 && (
                    <tr>
                      <td colSpan="4" className="px-6 py-8 text-center text-slate-500">No high-risk schools detected in the current dataset.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column - AI Agent */}
        <div className="lg:col-span-1">
          <AIAgent />
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
