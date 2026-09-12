import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useParams, Link } from 'react-router-dom';

const SchoolProfile = () => {
  const { id } = useParams();
  const [schools, setSchools] = useState([]);
  const [school, setSchool] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSchools = async () => {
      try {
        if (id) {
          const res = await axios.get(`/api/schools/${id}`);
          setSchool(res.data);
        } else {
          const res = await axios.get('/api/schools');
          setSchools(res.data);
        }
      } catch (e) {
        console.error(e);
      }
      setLoading(false);
    };
    fetchSchools();
  }, [id]);

  if (loading) return <div className="p-8">Loading...</div>;

  if (id && school) {
    return (
      <div className="space-y-6">
        <Link to="/schools" className="text-indigo-600 hover:underline">&larr; Back to Directory</Link>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-slate-800">{school.school_name}</h1>
              <p className="text-slate-500">{school.school_id_clean} • {school.district} District</p>
            </div>
            <div className={`px-4 py-2 rounded-full font-bold text-sm ${school.risk_category === 'HIGH' ? 'bg-red-100 text-red-700' : school.risk_category === 'MEDIUM' ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'}`}>
              {school.risk_category} RISK
            </div>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-8">
            <div>
              <p className="text-slate-400 text-sm">Avg Attendance</p>
              <p className="text-2xl font-bold text-slate-800">{(school.avg_attendance_rate * 100).toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-slate-400 text-sm">MDM Regularity</p>
              <p className="text-2xl font-bold text-slate-800">{(school.mdm_regularity_score * 100).toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-slate-400 text-sm">Infra Deficit</p>
              <p className="text-2xl font-bold text-slate-800">{(school.infrastructure_deficit_index * 100).toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-slate-400 text-sm">Avg Test Score</p>
              <p className="text-2xl font-bold text-slate-800">{school.avg_test_score.toFixed(1)}%</p>
            </div>
          </div>
          
          <div className="mt-8 pt-6 border-t border-slate-100">
            <h3 className="font-bold text-lg mb-2">Risk Factors & Recommendations</h3>
            {school.risk_reasons.length > 0 ? (
              <ul className="list-disc pl-5 text-slate-700 space-y-1">
                {school.risk_reasons.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            ) : (
              <p className="text-slate-500">No major risk factors detected.</p>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-slate-800">School Directory</h1>
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-100 text-slate-500">
            <tr>
              <th className="px-6 py-3">ID</th>
              <th className="px-6 py-3">Name</th>
              <th className="px-6 py-3">District</th>
              <th className="px-6 py-3">Risk</th>
              <th className="px-6 py-3">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-700">
            {schools.slice(0, 100).map(s => (
              <tr key={s.school_id_clean} className="hover:bg-slate-50">
                <td className="px-6 py-3 font-medium">{s.school_id_clean}</td>
                <td className="px-6 py-3">{s.school_name}</td>
                <td className="px-6 py-3">{s.district}</td>
                <td className="px-6 py-3">
                  <span className={`text-xs font-bold px-2 py-1 rounded-full ${s.risk_category==='HIGH'?'bg-red-100 text-red-700':s.risk_category==='MEDIUM'?'bg-amber-100 text-amber-700':'bg-green-100 text-green-700'}`}>
                    {s.risk_category}
                  </span>
                </td>
                <td className="px-6 py-3">
                  <Link to={`/schools/${s.school_id_clean}`} className="text-indigo-600 hover:underline text-sm font-medium">View Profile</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SchoolProfile;
