export interface Evidence {
  id: string;
  requirement_id: string;
  source_id: string;
  segment_id: string;
  verbatim_quote: string;
  verified: number;
  verification_method: string | null;
  source_mismatch: number;
}

export interface Requirement {
  id: string;
  statement: string;
  category: string | null;
  type: string;
  grounding: 'grounded' | 'quarantined' | 'ungrounded_candidate';
  confidence: string;
  fabrication_attempts: number;
  ungrounded_reasoning: string | null;
  evidence: Evidence[];
}

export interface Segment {
  id: string;
  source_id: string;
  index: number;
  speaker: string | null;
  timestamp: string | null;
  text: string;
}

export interface Contradiction {
  id: string;
  requirement_id_1: string;
  requirement_id_2: string;
  conflict_description: string;
  status: string;
  resolution_notes: string | null;
}

export interface Gap {
  segment_id: string;
  segment_index: number;
  segment_text: string;
  speaker: string | null;
  is_filler: boolean;
}

export interface AuditEvent {
  id: string;
  requirement_id: string;
  action: string;
  before: string | null;
  after: string | null;
  actor: string;
  timestamp: string;
  notes: string | null;
}
