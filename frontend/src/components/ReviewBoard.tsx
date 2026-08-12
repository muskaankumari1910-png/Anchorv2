import React, { useEffect, useState } from 'react';
import { Requirement, Contradiction } from '../types';
import RequirementCard from './RequirementCard';
import { CheckCircle, AlertTriangle, GitMerge, FileQuestion } from 'lucide-react';

const ReviewBoard: React.FC = () => {
  const [lanes, setLanes] = useState<{
    lane1_confirmed: string[];
    lane2_needs_review: string[];
    lane3_conflicts: string[];
    lane4_gaps: string[];
    counts: any;
  } | null>(null);
  
  const [requirements, setRequirements] = useState<Record<string, Requirement>>({});
  const [contradictions, setContradictions] = useState<Contradiction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      const headers = {
        'X-Workspace-ID': 'default'
      };
      
      // Fetch lanes
      const lanesResponse = await fetch('/api/review/lanes', { headers });
      const lanesData = await lanesResponse.json();
      setLanes(lanesData);
      
      // Fetch all requirements
      const reqsResponse = await fetch('/api/requirements', { headers });
      const allReqs = await reqsResponse.json();
      const reqMap: Record<string, Requirement> = {};
      allReqs.forEach((req: Requirement) => {
        reqMap[req.id] = req;
      });
      setRequirements(reqMap);
      
      // Fetch open contradictions
      const conflictsResponse = await fetch('/api/contradictions?status=open', { headers });
      const conflicts = await conflictsResponse.json();
      setContradictions(conflicts);
      
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500">Loading review board...</div>
      </div>
    );
  }

  if (!lanes) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500">No data available</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Requirements Review</h1>
        <button
          onClick={loadData}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Refresh
        </button>
      </div>

      {/* Four-Lane Layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        
        {/* Lane 1: Confirmed (Grounded) */}
        <div className="bg-white rounded-lg shadow">
          <div className="bg-green-50 border-b border-green-200 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <h2 className="font-semibold text-green-900">Confirmed</h2>
            </div>
            <span className="bg-green-200 text-green-800 px-2 py-1 rounded text-sm font-medium">
              {lanes.counts.confirmed}
            </span>
          </div>
          <div className="p-4 space-y-3 max-h-[600px] overflow-y-auto">
            {lanes.lane1_confirmed.map(reqId => {
              const req = requirements[reqId];
              return req ? <RequirementCard key={reqId} requirement={req} onUpdate={loadData} /> : null;
            })}
            {lanes.lane1_confirmed.length === 0 && (
              <p className="text-gray-400 text-sm">No confirmed requirements</p>
            )}
          </div>
        </div>

        {/* Lane 2: Needs Review (Quarantined + Ungrounded) */}
        <div className="bg-white rounded-lg shadow">
          <div className="bg-yellow-50 border-b border-yellow-200 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
              <h2 className="font-semibold text-yellow-900">Needs Review</h2>
            </div>
            <span className="bg-yellow-200 text-yellow-800 px-2 py-1 rounded text-sm font-medium">
              {lanes.counts.needs_review}
            </span>
          </div>
          <div className="p-4 space-y-3 max-h-[600px] overflow-y-auto">
            {lanes.lane2_needs_review.map(reqId => {
              const req = requirements[reqId];
              return req ? <RequirementCard key={reqId} requirement={req} onUpdate={loadData} /> : null;
            })}
            {lanes.lane2_needs_review.length === 0 && (
              <p className="text-gray-400 text-sm">No items need review</p>
            )}
          </div>
        </div>

        {/* Lane 3: Conflicts (Contradictions) */}
        <div className="bg-white rounded-lg shadow">
          <div className="bg-red-50 border-b border-red-200 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <GitMerge className="w-5 h-5 text-red-600" />
              <h2 className="font-semibold text-red-900">Conflicts</h2>
            </div>
            <span className="bg-red-200 text-red-800 px-2 py-1 rounded text-sm font-medium">
              {lanes.counts.conflicts}
            </span>
          </div>
          <div className="p-4 space-y-3 max-h-[600px] overflow-y-auto">
            {contradictions.map(conflict => (
              <div key={conflict.id} className="border rounded p-3 bg-red-50 border-red-200">
                <p className="text-sm text-red-900 font-medium mb-2">Contradiction</p>
                <p className="text-xs text-red-700 mb-2">{conflict.conflict_description}</p>
                <div className="flex space-x-2 text-xs">
                  <button className="text-blue-600 hover:underline">
                    View Req 1
                  </button>
                  <span className="text-gray-400">•</span>
                  <button className="text-blue-600 hover:underline">
                    View Req 2
                  </button>
                </div>
              </div>
            ))}
            {contradictions.length === 0 && (
              <p className="text-gray-400 text-sm">No conflicts detected</p>
            )}
          </div>
        </div>

        {/* Lane 4: Possible Gaps */}
        <div className="bg-white rounded-lg shadow">
          <div className="bg-gray-50 border-b border-gray-200 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <FileQuestion className="w-5 h-5 text-gray-600" />
              <h2 className="font-semibold text-gray-900">Possible Gaps</h2>
            </div>
            <span className="bg-gray-200 text-gray-800 px-2 py-1 rounded text-sm font-medium">
              {lanes.counts.gaps}
            </span>
          </div>
          <div className="p-4 space-y-3 max-h-[600px] overflow-y-auto">
            <p className="text-gray-400 text-sm">
              {lanes.counts.gaps} unconsumed segments
            </p>
            <p className="text-xs text-gray-500">
              (Implementation: show segment text with "Create requirement" button)
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReviewBoard;
