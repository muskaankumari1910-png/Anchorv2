import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import ReviewBoard from './components/ReviewBoard';
import RequirementDetail from './components/RequirementDetail';
import FileUpload from './components/FileUpload';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16 items-center">
              <div className="flex items-center space-x-8">
                <Link to="/" className="text-2xl font-bold text-blue-600">
                  Anchor
                </Link>
                <div className="flex space-x-4">
                  <Link 
                    to="/" 
                    className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Review Board
                  </Link>
                  <Link 
                    to="/upload" 
                    className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Upload & Extract
                  </Link>
                </div>
              </div>
              <span className="text-sm text-gray-500">
                Grounded Requirements Review
              </span>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<ReviewBoard />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/requirement/:id" element={<RequirementDetail />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

function UploadPage() {
  const [sources, setSources] = React.useState<any[]>([]);
  const [extracting, setExtracting] = React.useState<string | null>(null);

  const loadSources = async () => {
    try {
      const response = await fetch('/api/sources', {
        headers: {
          'X-Workspace-ID': 'default'
        }
      });
      const data = await response.json();
      setSources(data);
    } catch (error) {
      console.error('Failed to load sources:', error);
    }
  };

  React.useEffect(() => {
    loadSources();
  }, []);

  const handleExtract = async (sourceId: string) => {
    try {
      setExtracting(sourceId);
      const response = await fetch(`/api/extract/${sourceId}`, { 
        method: 'POST',
        headers: {
          'X-Workspace-ID': 'default'
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('Extraction error:', errorData);
        alert(`Extraction failed: ${errorData.detail || 'Please check browser console for details'}`);
        return;
      }
      
      const data = await response.json();
      alert(`Extracted ${data.stats.total_proposed} requirements! (${data.stats.grounded} grounded)`);
      loadSources();
    } catch (error: any) {
      console.error('Extraction failed:', error);
      alert(`Extraction failed: ${error.message || 'Network error. Please check if backend is running.'}`);
    } finally {
      setExtracting(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload & Extract</h1>
        <p className="text-gray-600">
          Upload documents or transcripts, then extract requirements
        </p>
      </div>

      <FileUpload onUploadComplete={loadSources} />

      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Uploaded Sources</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {sources.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-500">
              No sources uploaded yet. Upload a file above to get started.
            </div>
          ) : (
            sources.map((source) => (
              <div key={source.id} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50">
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{source.filename}</p>
                  <p className="text-sm text-gray-500">
                    {source.type.toUpperCase()} • {source.segments?.length || 0} segments • 
                    {' '}{new Date(source.uploaded_at).toLocaleString()}
                  </p>
                </div>
                <button
                  onClick={() => handleExtract(source.id)}
                  disabled={extracting === source.id}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  {extracting === source.id ? 'Extracting...' : 'Extract Requirements'}
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
