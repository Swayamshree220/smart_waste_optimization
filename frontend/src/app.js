import { Link, Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import './App.css';
import LiveBinMonitor from './components/LiveBinMonitor';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        {/* Navigation Bar */}
        <nav className="bg-white shadow-lg">
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <span className="text-2xl font-bold text-blue-600">🗑️ Smart Waste</span>
              </div>
              <div className="flex space-x-4">
                <Link 
                  to="/" 
                  className="px-4 py-2 rounded-lg hover:bg-blue-50 font-medium text-gray-700"
                >
                  Dashboard
                </Link>
                <Link 
                  to="/live-bins" 
                  className="px-4 py-2 rounded-lg hover:bg-blue-50 font-medium text-gray-700"
                >
                  Live Bins
                </Link>
                <Link 
                  to="/prediction" 
                  className="px-4 py-2 rounded-lg hover:bg-blue-50 font-medium text-gray-700"
                >
                  Prediction
                </Link>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-4 py-6">
          <Routes>
            <Route path="/" element={<DashboardHome />} />
            <Route path="/live-bins" element={<LiveBinMonitor />} />
            <Route path="/prediction" element={<div>Prediction Page (Your existing component)</div>} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

// Simple Dashboard Home Component
const DashboardHome = () => {
  return (
    <div className="text-center py-12">
      <h1 className="text-4xl font-bold mb-4">Smart Waste Collection System</h1>
      <p className="text-gray-600 mb-8">IoT-Powered Waste Management Solution</p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="text-4xl mb-2">🗑️</div>
          <h3 className="font-bold text-xl mb-2">Smart Bins</h3>
          <p className="text-gray-600">Real-time monitoring with IoT sensors</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="text-4xl mb-2">📊</div>
          <h3 className="font-bold text-xl mb-2">Analytics</h3>
          <p className="text-gray-600">ML-powered waste predictions</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="text-4xl mb-2">🚛</div>
          <h3 className="font-bold text-xl mb-2">Route Optimization</h3>
          <p className="text-gray-600">AI-optimized collection routes</p>
        </div>
      </div>
    </div>
  );
};

export default App;