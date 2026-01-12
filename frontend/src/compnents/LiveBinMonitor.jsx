import React, { useState, useEffect } from 'react';
import axios from 'axios';

const LiveBinMonitor = () => {
  const [bins, setBins] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBins();
    const interval = setInterval(fetchBins, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchBins = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/iot/bins/all-status');
      setBins(response.data.bins || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching bins:', error);
      setLoading(false);
    }
  };

  const getBinColor = (fillLevel) => {
    if (fillLevel >= 90) return 'bg-red-500';
    if (fillLevel >= 70) return 'bg-orange-500';
    if (fillLevel >= 50) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getStatusIcon = (status) => {
    switch(status) {
      case 'critical': return '🔴';
      case 'needs_collection': return '🟠';
      case 'moderate': return '🟡';
      default: return '🟢';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">🗑️ Live Bin Monitoring</h2>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-sm text-gray-600">Live</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {bins.map((bin) => (
          <div 
            key={bin.bin_id} 
            className={`rounded-lg shadow-md p-4 border-l-4 ${
              bin.fill_level >= 90 ? 'border-red-500 bg-red-50' :
              bin.fill_level >= 70 ? 'border-orange-500 bg-orange-50' :
              bin.fill_level >= 50 ? 'border-yellow-500 bg-yellow-50' :
              'border-green-500 bg-green-50'
            }`}
          >
            <div className="flex justify-between items-start mb-3">
              <div>
                <h3 className="font-bold text-lg">{bin.bin_id}</h3>
                <p className="text-sm text-gray-600">{bin.area}</p>
              </div>
              <span className="text-2xl">{getStatusIcon(bin.status)}</span>
            </div>

            <div className="mb-3">
              <div className="flex justify-between text-sm mb-1">
                <span>Fill Level</span>
                <span className="font-semibold">{bin.fill_level.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${getBinColor(bin.fill_level)}`}
                  style={{ width: `${bin.fill_level}%` }}
                ></div>
              </div>
            </div>

            <div className="flex justify-between items-center text-xs text-gray-500">
              <span>Status: {bin.status}</span>
              {bin.last_update && (
                <span>Updated: {new Date(bin.last_update).toLocaleTimeString()}</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {bins.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500">No bins found. Start your IoT devices!</p>
        </div>
      )}
    </div>
  );
};

export default LiveBinMonitor;