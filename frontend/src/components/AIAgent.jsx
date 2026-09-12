import React, { useState } from 'react';
import { Bot, Send, Loader2 } from 'lucide-react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const AIAgent = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setLoading(true);
    setResponse(null);
    try {
      const res = await axios.post('/api/ai/query', { query });
      setResponse(res.data);
    } catch (err) {
      setResponse({ answer: 'Failed to fetch AI response. Ensure backend is running.' });
    }
    setLoading(false);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden flex flex-col h-[500px]">
      <div className="bg-indigo-600 text-white p-4 flex items-center space-x-2">
        <Bot size={20} />
        <h2 className="font-semibold text-lg">Ask VidyaSetu AI</h2>
      </div>
      
      <div className="flex-1 p-4 overflow-y-auto bg-slate-50">
        {!response && !loading && (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 text-center px-4">
            <Bot size={48} className="mb-4 opacity-50" />
            <p>Ask natural language questions about attendance, MDM, infrastructure, or learning outcomes.</p>
            <p className="mt-2 text-sm text-indigo-500 font-medium">Try: "Compare average test scores between schools with and without functional electricity."</p>
          </div>
        )}
        
        {loading && (
          <div className="flex items-center justify-center h-full text-indigo-600">
            <Loader2 className="animate-spin" size={32} />
          </div>
        )}
        
        {response && (
          <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-100 animate-in fade-in slide-in-from-bottom-2">
            <div className="prose prose-sm text-slate-700 whitespace-pre-wrap max-w-none">
              {response.answer}
            </div>
            
            {response.chart_type === 'bar' && response.chart_data && (
              <div className="h-64 mt-6">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={response.chart_data}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip cursor={{fill: 'transparent'}} />
                    <Bar dataKey="Score" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        )}
      </div>
      
      <div className="p-4 bg-white border-t border-slate-100">
        <form onSubmit={handleQuery} className="flex space-x-2">
          <input 
            type="text" 
            placeholder="Ask a question..." 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 border border-slate-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
          />
          <button 
            type="submit"
            disabled={loading}
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 flex items-center"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
};

export default AIAgent;
