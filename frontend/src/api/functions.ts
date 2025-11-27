import request from './request'
import type { 
  ApiResponse, 
  PublishNoteParams, 
  PublishNoteResponse, 
  HealthCheckResponse, 
  GenerateImageParams, 
  GenerateImageResponse, 
  UploadImageResponse, 
  GenerateCaptionParams, 
  GenerateCaptionResponse,
  ListImagesParams,
  ListImagesResponse,
  TranslationResult,
  EnhanceResult,
  CreateWorkflowParams,
  UpdateWorkflowParams,
  WorkflowResponse,
  UploadWorkflowResponse,
  ListWorkflowParams,
  ListWorkflowResponse,
  GetWorkflowVariablesResponse,
  User,
  ActiveUser,
  Agent,
  AgentForm,
  ListNotesParams,
  ListNotesResponse
} from './config'

export const publishNote = async (params: PublishNoteParams): Promise<ApiResponse<PublishNoteResponse>> => {
  return request.post<any, ApiResponse<PublishNoteResponse>>('/publish', params)
}

export const listNotes = async (params?: ListNotesParams): Promise<ApiResponse<ListNotesResponse>> => {
  return request.get<any, ApiResponse<ListNotesResponse>>('/notes/list', { params })
}

export const checkHealth = async (): Promise<ApiResponse> => {
  try {
    const response = await request.get<any, HealthCheckResponse>('/health')
    // 将后端响应转换为统一的 ApiResponse 格式
    return {
      success: response.data.status === 'healthy',
      message: response.data.message,
      data: {
        status: response.data.status,
        message: response.data.message,
        comfyui_status: response.data.comfyui_status
      }
    }
  } catch (error) {
    return {
      success: false,
      message: '服务连接失败',
      data: {
        status: 'error',
        message: '服务连接失败',
        comfyui_status: {
          running: false,
          message: '无法连接到服务'
        }
      }
    }
  }
}

export const generateImage = async (params: GenerateImageParams): Promise<ApiResponse<GenerateImageResponse>> => {
  return request.post<any, ApiResponse<GenerateImageResponse>>('/generate-image', params)
}

export const listImages = async (params?: ListImagesParams): Promise<ApiResponse<{
  items: Array<{
    id: number
    filename: string
    workflow_name: string
    workflow_id: number | null
    created_at: string
    file_path: string
    variables: any
    source: string
    image_type: string
    local_path: string | null
    participated: boolean
  }>
  pagination: {
    page: number
    per_page: number
    total: number
    pages: number
  }
}>> => {
  return request.get('/images', {
    params: {
      page: params?.page || 1,
      per_page: params?.page_size || 20,
      _: Date.now() // Cache buster to prevent stale data
    }
  })
}

export const translateText = async (text: string): Promise<ApiResponse<TranslationResult>> => {
  return request.post<any, ApiResponse<TranslationResult>>('/translate', {
    text
  })
}

export const enhancePrompt = async (prompt: string): Promise<ApiResponse<EnhanceResult>> => {
  return request.post<any, ApiResponse<EnhanceResult>>('/enhance-prompt', {
    prompt
  })
}

export const uploadImage = async (file: FormData): Promise<ApiResponse<UploadImageResponse>> => {
  return request.post<any, ApiResponse<UploadImageResponse>>('/images/upload', file, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const deleteImage = async (id: number): Promise<ApiResponse<null>> => {
  return request.delete<any, ApiResponse<null>>(`/images/delete/${id}`)
}

export const generateCaption = async (params: GenerateCaptionParams): Promise<ApiResponse<GenerateCaptionResponse>> => {
  return request.post<any, ApiResponse<GenerateCaptionResponse>>('/generate-caption', params)
}

export const createWorkflow = async (params: CreateWorkflowParams): Promise<ApiResponse<WorkflowResponse>> => {
  return request.post<any, ApiResponse<WorkflowResponse>>('/workflows', params)
}

export const updateWorkflow = async (id: string, params: UpdateWorkflowParams): Promise<ApiResponse<WorkflowResponse>> => {
  return request.put<any, ApiResponse<WorkflowResponse>>(`/workflows/${id}`, params)
}

export const deleteWorkflow = async (id: string): Promise<ApiResponse> => {
  return request.delete<any, ApiResponse>(`/workflows/${id}`)
}

export const uploadWorkflow = async (file: FormData): Promise<ApiResponse<UploadWorkflowResponse>> => {
  return request.post<any, ApiResponse<UploadWorkflowResponse>>('/workflow/upload', file, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const listWorkflow = async (params: ListWorkflowParams): Promise<ApiResponse<ListWorkflowResponse>> => {
  return request.get<any, ApiResponse<ListWorkflowResponse>>('/workflow/list', { params })
}

export const toggleWorkflowStatus = async (id: number): Promise<ApiResponse<null>> => {
  return request.post<any, ApiResponse<null>>(`/workflow/${id}/toggle-status`)
}

export const getWorkflowVariables = async (id: number): Promise<ApiResponse<GetWorkflowVariablesResponse>> => {
  return request.get<any, ApiResponse<GetWorkflowVariablesResponse>>(`/workflow/${id}/variables`)
}

export async function updateWorkflowVars(
  workflowId: number, 
  inputVars: string[], 
  outputVars: string[],
  previewImage?: string
) {
  return await request.post(`/workflow/${workflowId}/update-vars`, {
    input_vars: inputVars,
    output_vars: outputVars,
    preview_image: previewImage
  })
}

// User Management APIs
export async function listUsers() {
  return request.get('/user/list')
}

export async function listActiveUsers(): Promise<ApiResponse<ActiveUser[]>> {
  return request.get<any, ApiResponse<ActiveUser[]>>('/user/active')
}

export async function createUser(data: {
  username: string
  nickname?: string
  cookie: string
  session_id?: string
}) {
  return request.post('/user/create', data)
}

export async function updateUser(userId: number, data: {
  username?: string
  nickname?: string
  cookie?: string
  session_id?: string
  status?: boolean
}) {
  return request.put(`/user/update/${userId}`, data)
}

export async function deleteUser(userId: number) {
  return request.delete(`/user/delete/${userId}`)
}

// Agent APIs
export async function createAgent(data: AgentForm): Promise<ApiResponse<Agent>> {
  return request.post<any, ApiResponse<Agent>>('/agent/agents', data)
}

export async function listAgents(): Promise<ApiResponse<Agent[]>> {
  return request.get<any, ApiResponse<Agent[]>>('/agent/agents')
}

export async function toggleAgent(agentId: number): Promise<ApiResponse<Agent>> {
  return request.put<any, ApiResponse<Agent>>(`/agent/agents/${agentId}/toggle`)
}

export async function deleteAgent(agentId: number): Promise<ApiResponse<void>> {
  return request.delete<any, ApiResponse<void>>(`/agent/agents/${agentId}`)
}

export async function updateAgent(agentId: number, data: AgentForm): Promise<ApiResponse<Agent>> {
  return request.put<any, ApiResponse<Agent>>(`/agent/agents/${agentId}`, data)
}