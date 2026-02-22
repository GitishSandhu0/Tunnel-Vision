export interface GraphNode {
  id: string;
  label: string;
  type: "user" | "master" | "bridge";
  category?: string;
  description?: string;
  weight?: number;
  x?: number;
  y?: number;
  z?: number;
  color?: string;
  size?: number;
}

export interface GraphLink {
  source: string;
  target: string;
  weight?: number;
  type?: "strong" | "weak" | "inferred";
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

export interface Entity {
  id: string;
  name: string;
  type: string;
  category?: string;
  description?: string;
  confidence: number;
  sourceFile?: string;
  createdAt: string;
}

export interface Category {
  id: string;
  name: string;
  description?: string;
  entityCount: number;
  color?: string;
}

export interface Recommendation {
  id: string;
  topic: string;
  description: string;
  relevanceScore: number;
  distanceFromUser: number;
  category?: string;
  tags?: string[];
  estimatedReadTime?: number;
  resources?: RecommendationResource[];
}

export interface RecommendationResource {
  title: string;
  url: string;
  type: "article" | "video" | "course" | "paper" | "book";
}

export interface UploadJob {
  jobId: string;
  status: "queued" | "processing" | "completed" | "failed";
  fileName: string;
  fileSize: number;
  uploadedAt: string;
  completedAt?: string;
  progress?: number;
  entitiesExtracted?: number;
  error?: string;
}

export interface User {
  id: string;
  email: string;
  createdAt: string;
  uploadedFiles: number;
  entitiesExtracted: number;
  graphNodes: number;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface UploadResponse {
  jobId: string;
  message: string;
  fileName: string;
  fileSize: number;
}

export interface DashboardStats {
  uploadedFiles: number;
  entitiesExtracted: number;
  graphNodes: number;
  recommendations: number;
}
