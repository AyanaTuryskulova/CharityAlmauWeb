import api from './api';

interface AiAnalysis {
  suggestedTitle: string;
  suggestedCategory: string;
  confidence: number;
}

export const aiService = {
  async analyzeImage(file: File): Promise<AiAnalysis> {
    const formData = new FormData();
    formData.append('image', file);
    const res = await api.post<AiAnalysis>('/ai/analyze-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return (res as unknown as { data?: AiAnalysis }).data ?? res as unknown as AiAnalysis;
  },
};
