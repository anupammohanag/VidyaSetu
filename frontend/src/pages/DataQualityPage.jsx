import React, { useEffect, useState } from 'react';
import axios from 'axios';
import KPICard from '../components/KPICard';
import { Database, AlertTriangle, ShieldCheck, CheckCircle2 } from 'lucide-react';

const DataQualityPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDQ = async () => {
      try {
        const res = await axios.get('/api/data-quality');
        setData(res.data);
      } catch (e) {
        console.error(e);
      }
      setLoading(false);
    };
    fetchDQ();
  }, []);

  if (loading) return <div className="text-indigo-600 p-8 font-semibold animate-pulse">Loading data quality report...</div>;
  if (!data) return <div className="text-red-500 p-8">Failed to load.</div>;

  return (
    <div className="space-y-6 animate-in fade-in">
      <div>
        <h1 className="text-3xl font-bold text-slate-800">Data Quality & Anomalies</h1>
        <p className="text-slate-500 mt-2">Overview of records processed, standardized, and flagged by the Data Rescue Engine.</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Total Attendance Records" value={data.total_attendance_records} icon={Database} color="blue" />
        <KPICard title="Proxy Attendance Anomalies" value={data.proxy_attendance_records} icon={AlertTriangle} color="amber" subtitle="100% on Sundays" />
        <KPICard title="Impossible Attendance" value={data.impossible_attendance_records} icon={ShieldCheck} color="red" subtitle="Present > Total" />
        <KPICard title="Standardized Keys" value={data.standardized_ids ? 'Yes' : 'No'} icon={CheckCircle2} color="green" subtitle="SCH0000 Format" />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6 mt-8">
        <h2 className="text-lg font-bold mb-4 text-slate-800">Cleaning Engine Actions</h2>
        <ul className="space-y-3 text-slate-600">
          <li className="flex gap-2 items-start"><CheckCircle2 className="text-green-500 w-5 h-5" /> <strong>School IDs:</strong> Normalized variations (e.g., SCH-1001, sch_1001) to canonical format SCH1001.</li>
          <li className="flex gap-2 items-start"><AlertTriangle className="text-amber-500 w-5 h-5" /> <strong>Attendance Anomalies:</strong> Flagged rather than deleted to preserve evidence of potential proxy marking.</li>
          <li className="flex gap-2 items-start"><CheckCircle2 className="text-green-500 w-5 h-5" /> <strong>MDM Normalization:</strong> Converted vendor names to Title Case, standardized Grains to (Rice, Wheat, Dal), unified quantities to KG.</li>
          <li className="flex gap-2 items-start"><CheckCircle2 className="text-green-500 w-5 h-5" /> <strong>Infrastructure Booleans:</strong> Mapped string variations ("Hai", "Haan", "Working", "1") into standard True/False logic.</li>
          <li className="flex gap-2 items-start"><CheckCircle2 className="text-green-500 w-5 h-5" /> <strong>Test Scores:</strong> Mapped CGPA, Letter Grades, and raw fractions to a unified percentage scale.</li>
        </ul>
      </div>
    </div>
  );
};

export default DataQualityPage;
