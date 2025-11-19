<template>
  <div class="page">
    <div class="page-header">
      <h2>LLM 模型管理</h2>
      <n-button type="primary" @click="syncActiveConfigToBackend">
        <template #icon>
          <n-icon>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="currentColor" d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6s-2.69 6-6 6s-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8s-3.58-8-8-8z"/></svg>
          </n-icon>
        </template>
        同步配置到后端
      </n-button>
    </div>
    <div class="content">
      <!-- Configuration Form -->
      <n-card title="添加模型配置" style="margin-bottom: 20px;">
        <n-alert type="info" style="margin-bottom: 16px;" :show-icon="true">
          <template #header>Ollama 配置说明</template>
          对于 Ollama 模型，API Base 通常为 <n-text code>http://localhost:11434/v1</n-text> 或 <n-text code>http://127.0.0.1:11434/v1</n-text>
          <br/>
          确保 Ollama 服务正在运行，并且已经拉取了所需的模型（例如：<n-text code>ollama pull llama3.2</n-text>）
        </n-alert>
        <n-form label-width="120">
          <n-form-item label="配置名称">
            <n-input v-model:value="configName" placeholder="例如：本地 GPT-4" />
          </n-form-item>
          <n-form-item label="LLM 模型">
            <n-input 
              v-model:value="llmModel" 
              placeholder="输入模型名称，例如：llama3.2, gpt-4o, qwen2.5"
            />
          </n-form-item>
          <n-form-item label="API Base">
            <n-input v-model:value="apiBase" placeholder="例如：http://localhost:8000 或 http://192.168.1.100:8000" />
            <template #feedback>
              <span style="color: #999; font-size: 12px;">填写完整 URL，或者使用下方 IP + 端口</span>
            </template>
          </n-form-item>
          <n-form-item label="API 主机 IP">
            <n-input v-model:value="apiHost" placeholder="例如：localhost 或 192.168.1.100" />
          </n-form-item>
          <n-form-item label="API 端口">
            <n-input v-model:value="apiPort" placeholder="例如：8000" />
            <template #feedback>
              <span style="color: #999; font-size: 12px;">IP 和 端口需同时填写</span>
            </template>
          </n-form-item>
          <div class="actions">
            <n-button v-if="!isEditing" type="primary" @click="addConfig">添加配置</n-button>
            <n-space v-else>
              <n-button @click="cancelEdit">取消</n-button>
              <n-button type="primary" @click="saveEdit">保存修改</n-button>
            </n-space>
          </div>
        </n-form>
      </n-card>

      <!-- Saved Models List -->
      <n-card title="已保存的模型配置">
        <n-empty v-if="savedConfigs.length === 0" description="暂无保存的模型配置" />
        <n-list v-else hoverable clickable>
          <n-list-item v-for="(config, index) in savedConfigs" :key="index">
            <template #prefix>
              <n-icon size="24" color="#18a058">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10s10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5l1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
              </n-icon>
            </template>
            <n-thing :title="config.name || config.model">
              <template #description>
                <n-space vertical size="small">
                  <div><n-tag size="small" type="info">{{ config.model }}</n-tag></div>
                  <div v-if="config.apiBase"><n-text depth="3" style="font-size: 12px;">API: {{ config.apiBase }}</n-text></div>
                  <div v-if="config.apiHost && config.apiPort"><n-text depth="3" style="font-size: 12px;">连接: {{ config.apiHost }}:{{ config.apiPort }}</n-text></div>
                </n-space>
              </template>
              <template #action>
                <n-space>
                  <n-button 
                    size="small" 
                    type="primary" 
                    @click="setAsActive(index)"
                    :disabled="index === activeConfigIndex"
                  >
                    {{ index === activeConfigIndex ? '当前使用' : '设为默认' }}
                  </n-button>
                  <n-button size="small" @click="editConfig(index)">编辑</n-button>
                  <n-button size="small" type="error" @click="deleteConfig(index)">删除</n-button>
                </n-space>
              </template>
            </n-thing>
          </n-list-item>
        </n-list>
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NForm, NFormItem, NInput, NButton, NCard, NList, NListItem, NThing, NSpace, NEmpty, NTag, NText, NIcon, NAlert, useMessage, useDialog } from 'naive-ui'
import api from '@/api'

const message = useMessage()
const dialog = useDialog()

// Form fields
const configName = ref('')
const llmModel = ref('')
const apiBase = ref('')
const apiHost = ref('127.0.0.1')
const apiPort = ref('')
const isEditing = ref(false)
const editingIndex = ref(-1)

// Saved configurations
const savedConfigs = ref<Array<{
  name: string
  model: string
  apiBase: string
  apiHost: string
  apiPort: string
}>>([])

const activeConfigIndex = ref(0)

// Load configs from localStorage
const loadConfigs = () => {
  const stored = localStorage.getItem('llm_model_configs')
  if (stored) {
    try {
      savedConfigs.value = JSON.parse(stored)
    } catch (e) {
      console.error('Failed to parse saved configs:', e)
    }
  }
  
  const activeIndex = localStorage.getItem('llm_active_config_index')
  if (activeIndex !== null) {
    activeConfigIndex.value = parseInt(activeIndex)
  }
}

// Save configs to localStorage
const saveConfigs = () => {
  localStorage.setItem('llm_model_configs', JSON.stringify(savedConfigs.value))
  localStorage.setItem('llm_active_config_index', activeConfigIndex.value.toString())
}

// Edit configuration
const editConfig = (index: number) => {
  const config = savedConfigs.value[index]
  configName.value = config.name
  llmModel.value = config.model
  apiBase.value = config.apiBase
  apiHost.value = config.apiHost
  apiPort.value = config.apiPort
  isEditing.value = true
  editingIndex.value = index
  message.info('正在编辑配置，修改后点击"保存修改"')
}

// Cancel edit
const cancelEdit = () => {
  configName.value = ''
  llmModel.value = ''
  apiBase.value = ''
  apiHost.value = '127.0.0.1'
  apiPort.value = ''
  isEditing.value = false
  editingIndex.value = -1
}

// Save edit
const saveEdit = () => {
  // Validation
  const hasApiBase = !!apiBase.value.trim()
  const hasIpAndPort = !!apiHost.value.trim() && !!apiPort.value.trim()
  
  if (!hasApiBase && !hasIpAndPort) {
    message.error('请填写 API Base 或者同时填写 API 主机 IP 和 端口')
    return
  }
  
  if (!llmModel.value.trim()) {
    message.error('请选择 LLM 模型')
    return
  }
  
  if (!configName.value.trim()) {
    message.error('请输入配置名称')
    return
  }
  
  // Update configuration
  savedConfigs.value[editingIndex.value] = {
    name: configName.value,
    model: llmModel.value,
    apiBase: apiBase.value,
    apiHost: apiHost.value,
    apiPort: apiPort.value
  }
  
  saveConfigs()
  cancelEdit()
  message.success('配置已更新')
  
  // Sync to backend if this is the active config
  if (editingIndex.value === activeConfigIndex.value) {
    syncActiveConfigToBackend()
  }
}

// Add new configuration
const addConfig = () => {
  // Validation
  const hasApiBase = !!apiBase.value.trim()
  const hasIpAndPort = !!apiHost.value.trim() && !!apiPort.value.trim()
  
  if (!hasApiBase && !hasIpAndPort) {
    message.error('请填写 API Base 或者同时填写 API 主机 IP 和 端口')
    return
  }
  
  if (!llmModel.value.trim()) {
    message.error('请选择 LLM 模型')
    return
  }
  
  if (!configName.value.trim()) {
    message.error('请输入配置名称')
    return
  }
  
  // Add to list
  savedConfigs.value.push({
    name: configName.value,
    model: llmModel.value,
    apiBase: apiBase.value,
    apiHost: apiHost.value,
    apiPort: apiPort.value
  })
  
  saveConfigs()
  
  // Clear form
  configName.value = ''
  llmModel.value = ''
  apiBase.value = ''
  apiHost.value = ''
  apiPort.value = ''
  
  message.success('已添加模型配置')
  
  // Sync active config to backend
  syncActiveConfigToBackend()
}

// Delete configuration
const deleteConfig = (index: number) => {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除配置 "${savedConfigs.value[index].name}" 吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: () => {
      savedConfigs.value.splice(index, 1)
      
      // Adjust active index if necessary
      if (activeConfigIndex.value >= savedConfigs.value.length) {
        activeConfigIndex.value = Math.max(0, savedConfigs.value.length - 1)
      }
      
      saveConfigs()
      message.success('已删除配置')
      
      // Sync to backend
      syncActiveConfigToBackend()
    }
  })
}

// Set as active configuration
const setAsActive = (index: number) => {
  activeConfigIndex.value = index
  saveConfigs()
  message.success('已设为默认配置')
  
  // Sync to backend
  syncActiveConfigToBackend()
}

// Sync active config to backend
const syncActiveConfigToBackend = async () => {
  if (savedConfigs.value.length === 0) {
    console.warn('[LLM Sync] No configs to sync')
    message.warning('请先添加至少一个模型配置')
    return
  }
  
  const config = savedConfigs.value[activeConfigIndex.value]
  if (!config) {
    console.warn('[LLM Sync] No active config found')
    message.error('未找到活动配置')
    return
  }
  
  // Build payload - use apiBase if provided, otherwise use host+port
  const payload: any = {
    enhance_model: config.model,
    caption_model: config.model,
  }
  
  if (config.apiBase && config.apiBase.trim()) {
    payload.api_base = config.apiBase.trim()
    console.log('[LLM Sync] Using apiBase directly:', payload.api_base)
  } else if (config.apiHost && config.apiPort) {
    payload.api_host = config.apiHost.trim()
    payload.api_port = config.apiPort.trim()
    console.log('[LLM Sync] Using host+port:', payload.api_host, payload.api_port)
  } else {
    message.error('配置无效：请填写 API Base 或者 API 主机+端口')
    return
  }
  
  console.log('[LLM Sync] ========================================')
  console.log('[LLM Sync] Syncing config to backend:')
  console.log('[LLM Sync] Payload:', JSON.stringify(payload, null, 2))
  console.log('[LLM Sync] ========================================')
  
  try {
    const response = await api.post('/prompt/models', payload)
    console.log('[LLM Sync] ========================================')
    console.log('[LLM Sync] ✅ Success! Backend response:')
    console.log('[LLM Sync] Response:', JSON.stringify(response.data, null, 2))
    console.log('[LLM Sync] ========================================')
    
    if (response.data && response.data.data) {
      const updatedConfig = response.data.data
      console.log('[LLM Sync] Backend now using:')
      console.log('[LLM Sync]   - Model:', updatedConfig.enhance_model)
      console.log('[LLM Sync]   - API Base:', updatedConfig.api_base)
      message.success(`✅ 配置已同步！API Base: ${updatedConfig.api_base}`)
    } else {
      message.success('已同步配置到后端')
    }
  } catch (e: any) {
    console.error('[LLM Sync] ========================================')
    console.error('[LLM Sync] ❌ Error syncing to backend:')
    console.error('[LLM Sync] Error:', e)
    console.error('[LLM Sync] Response:', e.response?.data)
    console.error('[LLM Sync] ========================================')
    message.error(`同步配置失败: ${e.response?.data?.message || e.message || '网络错误'}`)
  }
}

onMounted(async () => {
  loadConfigs()
  // Wait a bit for DOM to settle, then sync
  await new Promise(resolve => setTimeout(resolve, 500))
  if (savedConfigs.value.length > 0) {
    console.log('[LLM] Page loaded, auto-syncing config...')
    await syncActiveConfigToBackend()
  } else {
    console.warn('[LLM] No configs found. Please add a model configuration.')
    message.warning('请先添加 LLM 模型配置')
  }
})
</script>

<style scoped>
.page { padding: 16px; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.actions { display: flex; justify-content: flex-end; }
</style>