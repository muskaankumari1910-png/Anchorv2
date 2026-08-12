import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchRequirement, fetchSegment, editRequirement, fetchAuditTrail } from '../api';
import { Requirement, Segment, AuditEvent } from '../types';
import { ArrowLeft, ExternalLink } from 'lucide-react';

const RequirementDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [requirement, setRequirement] = useState<Requirement | null>(null);
  const [segments, setSegments] = useState<Record<string, Segment>>({});
  const [auditTrail, setAuditTrail] = useState<AuditEvent[]>([]);
  const [editing, setEditing] = useState(false);
  const [editedStatement, setEditedStatement] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      
      // Fetch requirement
      const req = await fetchRequirement(id);
      setRequirement(req);
      setEditedStatement(req.statement);
      
      // Fetch segments for evidence
      const segMap: Record<string, Segment> = {};
      for (const evd of req.evidence) {
        const seg = await fetchSegment(evd.source_id, evd.segment_id);
        if (seg) {
          segMap[evd.segment_id] = seg;
        }
      }
      setSegments(segMap);
      
      // Fetch audit trail
      const audit = await fetchAuditTrail(id);
      setAuditTrail(audit);
      
    } catch (error) {
      console.error('Failed to load requirement:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveEdit = async () => {
    if (!id) return;
    
    try {
      await editRequirement(id, editedStatement);
      setEditing(false);
      loadData();
    } catch (error) {
      console.error('Failed to edit:', error);
    }
  };

  const jumpToQuote = (segmentId: string) => {
    // Scroll to segment view
    const element = document.getElementById(`segment-${segmentId}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      element.classList.add('ring-2', 'ring-blue-500');
      setTimeout(() => {
        element.classList.remove('ring-2', 'ring-blue-500');
      }, 2000);
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading...</div>;
  }

  if (!requirement) {
    return <div className="text-center py-8">Requirement not found</div>;
  }

  return (
    <div className="space-y-6">
      <button
        onClick={() => navigate('/')}
        className="flex items-center space-x-2 text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Review Board</span>
      </button>

      {/* Requirement Details */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold">Requirement Details</h1>
          <span className={`px-3 py-1 rounded text-sm font-medium ${
            requirement.grounding === 'grounded' ? 'bg-green-100 text-green-800' :
            requirement.grounding === 'quarantined' ? 'bg-red-100 text-red-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {requirement.grounding}
          </span>
        </div>

        {!editing ? (
          <div>
            <p className="text-lg text-gray-900 mb-4">{requirement.statement}</p>
            <button
              onClick={() => setEditing(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Edit Statement
            </button>
          </div>
        ) : (
          <div>
            <textarea
              value={editedStatement}
              onChange={(e) => setEditedStatement(e.target.value)}
              className="w-full border rounded p-3 mb-2"
              rows={3}
            />
            <div className="flex space-x-2">
              <button
                onClick={handleSaveEdit}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                Save
              </button>
              <button
                onClick={() => {
                  setEditing(false);
                  setEditedStatement(requirement.statement);
                }}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Category:</span>
            <span className="ml-2 font-medium">{requirement.category || 'N/A'}</span>
          </div>
          <div>
            <span className="text-gray-500">Type:</span>
            <span className="ml-2 font-medium">{requirement.type}</span>
          </div>
          <div>
            <span className="text-gray-500">Confidence:</span>
            <span className="ml-2 font-medium">{requirement.confidence}</span>
          </div>
        </div>
      </div>

      {/* Evidence */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Evidence ({requirement.evidence.length})</h2>
        <div className="space-y-4">
          {requirement.evidence.map((evd) => {
            const segment = segments[evd.segment_id];
            return (
              <div key={evd.id} className="border rounded p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded text-xs ${
                      evd.verified === 1 ? 'bg-green-100 text-green-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {evd.verified === 1 ? '✓ Verified' : '✗ Failed'}
                    </span>
                    {evd.verification_method && (
                      <span className="text-xs text-gray-500">
                        ({evd.verification_method})
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() => jumpToQuote(evd.segment_id)}
                    className="flex items-center space-x-1 text-blue-600 hover:text-blue-800 text-sm"
                  >
                    <ExternalLink className="w-4 h-4" />
                    <span>Jump to quote</span>
                  </button>
                </div>

                <div className="bg-gray-50 p-3 rounded mb-2">
                  <p className="text-sm font-mono">{evd.verbatim_quote}</p>
                </div>

                {segment && (
                  <div id={`segment-${evd.segment_id}`} className="bg-blue-50 p-3 rounded transition-all">
                    <div className="text-xs text-gray-500 mb-1">
                      {segment.speaker && <span className="font-medium">{segment.speaker}</span>}
                      {segment.timestamp && <span className="ml-2">{segment.timestamp}</span>}
                    </div>
                    <p className="text-sm text-gray-700">{segment.text}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Audit Trail */}
      {auditTrail.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Audit Trail</h2>
          <div className="space-y-2">
            {auditTrail.map((event) => (
              <div key={event.id} className="border-l-4 border-blue-500 pl-4 py-2">
                <div className="flex items-center space-x-2 text-sm">
                  <span className="font-medium">{event.action}</span>
                  <span className="text-gray-500">by {event.actor}</span>
                  <span className="text-gray-400">{new Date(event.timestamp).toLocaleString()}</span>
                </div>
                {event.notes && <p className="text-xs text-gray-600 mt-1">{event.notes}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default RequirementDetail;
