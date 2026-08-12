import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Requirement } from '../types';
import { acceptRequirement, rejectRequirement } from '../api';
import { CheckCircle, XCircle, Edit, ExternalLink } from 'lucide-react';

interface RequirementCardProps {
  requirement: Requirement;
  onUpdate: () => void;
}

const RequirementCard: React.FC<RequirementCardProps> = ({ requirement, onUpdate }) => {
  const [showActions, setShowActions] = useState(false);

  const getGroundingBadge = () => {
    switch (requirement.grounding) {
      case 'grounded':
        return <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">✓ Grounded</span>;
      case 'quarantined':
        return <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded">⚠ Quarantined</span>;
      case 'ungrounded_candidate':
        return <span className="bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded">? Ungrounded</span>;
    }
  };

  const handleAccept = async () => {
    try {
      await acceptRequirement(requirement.id);
      onUpdate();
    } catch (error) {
      console.error('Failed to accept:', error);
    }
  };

  const handleReject = async () => {
    const reason = prompt('Reason for rejection:');
    if (reason) {
      try {
        await rejectRequirement(requirement.id, reason);
        onUpdate();
      } catch (error) {
        console.error('Failed to reject:', error);
      }
    }
  };

  return (
    <div 
      className="border rounded p-3 hover:shadow-md transition-shadow bg-white"
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1">
          {getGroundingBadge()}
          {requirement.category && (
            <span className="ml-2 text-xs text-gray-500">
              {requirement.category}
            </span>
          )}
        </div>
        <Link to={`/requirement/${requirement.id}`} className="text-blue-600 hover:text-blue-800">
          <ExternalLink className="w-4 h-4" />
        </Link>
      </div>

      <p className="text-sm text-gray-900 mb-2">{requirement.statement}</p>

      <div className="text-xs text-gray-500 mb-2">
        {requirement.evidence.length} evidence • {requirement.fabrication_attempts} fabrications
      </div>

      {/* Quick Actions */}
      {showActions && requirement.grounding === 'grounded' && (
        <div className="flex space-x-2 mt-2 pt-2 border-t">
          <button
            onClick={handleAccept}
            className="flex items-center space-x-1 px-2 py-1 bg-green-100 text-green-700 rounded text-xs hover:bg-green-200"
          >
            <CheckCircle className="w-3 h-3" />
            <span>Accept</span>
          </button>
          <button
            onClick={handleReject}
            className="flex items-center space-x-1 px-2 py-1 bg-red-100 text-red-700 rounded text-xs hover:bg-red-200"
          >
            <XCircle className="w-3 h-3" />
            <span>Reject</span>
          </button>
          <Link
            to={`/requirement/${requirement.id}`}
            className="flex items-center space-x-1 px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs hover:bg-blue-200"
          >
            <Edit className="w-3 h-3" />
            <span>Edit</span>
          </Link>
        </div>
      )}
    </div>
  );
};

export default RequirementCard;
