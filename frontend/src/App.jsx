import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import DataQualityPage from './pages/DataQualityPage';
import SchoolProfile from './pages/SchoolProfile';
import DistrictProfile from './pages/DistrictProfile';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-slate-50">
        <header className="bg-indigo-600 text-white shadow-md sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
            <div>
              <Link to="/">
                <h1 className="text-2xl font-bold tracking-tight">VidyaSetu AI</h1>
                <p className="text-indigo-200 text-sm">Student Retention & Welfare Efficacy Tracker</p>
              </Link>
            </div>
            <nav className="flex gap-4">
              <Link to="/" className="hover:text-indigo-200 transition-colors font-medium">Dashboard</Link>
              <Link to="/data-quality" className="hover:text-indigo-200 transition-colors font-medium">Data Quality</Link>
              <Link to="/schools" className="hover:text-indigo-200 transition-colors font-medium">Schools</Link>
              <Link to="/districts" className="hover:text-indigo-200 transition-colors font-medium">Districts</Link>
            </nav>
          </div>
        </header>
        
        <main className="max-w-7xl mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/data-quality" element={<DataQualityPage />} />
            <Route path="/schools" element={<SchoolProfile />} />
            <Route path="/schools/:id" element={<SchoolProfile />} />
            <Route path="/districts" element={<DistrictProfile />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
