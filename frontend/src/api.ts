import axios from 'axios';
import { Requirement, Segment, Contradiction, AuditEvent } from './types';

const api = axios.create({
  baseURL: '/api',
});

export const fetchRequirements = async (grounding?: string): Promise<Requirement[]> => {
  const params = grounding ? { grounding } : {};
  const response = await api.get<Requirement[]>('/requirements', { params });
  return response.data;
};

export const fetchRequirement = async (id: string): Promise<Requirement> => {
  const response = await api.get<Requirement>(`/requirements/${id}`);
  return response.data;
};

export const fetchSegment = async (sourceId: string, segmentId: string): Promise<Segment> => {
  // Fetch source and find segment
  const response = await api.get(`/sources/${sourceId}`);
  const segment = response.data.segments.find((s: Segment) => s.id === segmentId);
  return segment;
};

export const fetchContradictions = async (status?: string): Promise<Contradiction[]> => {
  const params = status ? { status } : {};
  const response = await api.get<Contradiction[]>('/contradictions', { params });
  return response.data;
};

export const fetchReviewLanes = async () => {
  const response = await api.get('/review/lanes');
  return response.data;
};

export const acceptRequirement = async (id: string, actor: string = 'user') => {
  const response = await api.post(`/requirements/${id}/accept`, { actor });
  return response.data;
};

export const rejectRequirement = async (id: string, reason: string, actor: string = 'user') => {
  const response = await api.post(`/requirements/${id}/reject`, { reason, actor });
  return response.data;
};

export const editRequirement = async (id: string, newStatement: string, actor: string = 'user') => {
  const response = await api.post(`/requirements/${id}/edit`, { new_statement: newStatement, actor });
  return response.data;
};

export const fetchAuditTrail = async (requirementId: string): Promise<AuditEvent[]> => {
  const response = await api.get<AuditEvent[]>(`/requirements/${requirementId}/audit`);
  return response.data;
};

export const resolveContradiction = async (id: string, resolution: string, notes: string) => {
  const response = await api.post(`/contradictions/${id}/resolve`, { resolution, notes });
  return response.data;
};

export const uploadFile = async (file: File): Promise<any> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/ingest', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

export const extractRequirements = async (sourceId: string): Promise<any> => {
  const response = await api.post(`/extract/${sourceId}`);
  return response.data;
};
