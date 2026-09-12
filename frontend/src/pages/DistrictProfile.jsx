import React, { useEffect, useState } from 'react';
import axios from 'axios';

const DistrictProfile = () => {
  const [districts, setDistricts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDistricts = async () => {
      try {
        const res = await axios.get('/api/districts');
        setDistricts(res.data);
      } catch (e) {
        console.error(e);
      }
      setLoading(false);
    };
    fetchDistricts();
  }, []);

  if (loading) return <div className="p-8">Loading districts...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-slate-800">District Interventions</h1>
      <p className="text-slate-500">Aggregate metrics across all tracked districts.</p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {districts.map(d => (
          <div key={d.district} className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
            <h2 className="text-xl font-bold text-slate-800 mb-1">{d.district || 'Unknown District'}</h2>
            <p className="text-sm text-slate-400 mb-4">{d.total_schools} Schools Tracked</p>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center border-b border-slate-50 pb-2">
                <span className="text-slate-500 text-sm">Avg Attendance</span>
                <span className="font-semibold text-slate-800">{(d.avg_attendance || 0).toFixed(1)}%</span>
              </div>
              <div className="flex justify-between items-center border-b border-slate-50 pb-2">
                <span className="text-slate-500 text-sm">Avg Test Score</span>
                <span className="font-semibold text-slate-800">{(d.avg_score || 0).toFixed(1)}%</span>
              </div>
            </div>
            
            <div className="mt-4 pt-4 border-t border-slate-100 flex justify-between items-center">
              <span className="text-xs text-slate-400">Needs review</span>
              <button className="text-indigo-600 text-sm font-medium hover:underline">Drill Down</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DistrictProfile;
