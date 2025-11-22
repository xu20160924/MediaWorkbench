<template>
  <div class="templates-page">
    <div class="page-header">
      <h2>提示词模板</h2>
      <div class="header-actions">
        <n-input v-model:value="search" placeholder="搜索模板" style="width: 260px" />
        <n-button type="primary" @click="openCreate">新增模板</n-button>
      </div>
    </div>

    <n-data-table :columns="columns" :data="filteredTemplates" :pagination="{ pageSize: 8 }" />

    <n-modal v-model:show="showModal" preset="card" :title="modalTitle" :style="{ width: '1200px' }" content-style="max-height: 75vh; overflow-y: auto;">
      <n-alert type="info" style="margin-bottom: 16px;" :show-icon="false" closable>
        <div style="font-size: 11px; line-height: 1.5;">
          <div style="font-weight: 600; margin-bottom: 6px;">💡 任务占位符（拖拽到模板中，hover查看说明）：</div>
          <div style="display: flex; flex-wrap: wrap; gap: 6px;">
            <code 
              v-for="placeholder in placeholders" 
              :key="placeholder.value"
              draggable="true"
              @dragstart="handleDragStart($event, placeholder.value)"
              :title="`${placeholder.label}: ${placeholder.description}`"
              style="background: rgba(24, 160, 88, 0.15); padding: 3px 8px; border-radius: 3px; cursor: move; font-size: 11px; user-select: none;"
            >
              {{ placeholder.value }}
            </code>
          </div>
        </div>
      </n-alert>
      <n-form :model="form" label-placement="left" label-width="100">
        <n-form-item label="名称">
          <n-input v-model:value="form.name" />
        </n-form-item>
        <n-form-item label="分类">
          <n-select v-model:value="form.category" :options="categoryOptions" />
        </n-form-item>
        <n-form-item label="标签">
          <n-select v-model:value="form.tags" multiple :options="tagOptions" filterable placeholder="输入或选择标签" />
        </n-form-item>
        <n-form-item label="模板内容">
          <div class="editor-wrapper">
            <n-input 
              ref="contentInput"
              v-model:value="form.content" 
              type="textarea" 
              :rows="14" 
              placeholder="输入模板内容，或拖拽上方占位符到此处..."
              @drop="handleDrop"
              @dragover.prevent
              @dragenter="handleDragEnter"
              @dragleave="handleDragLeave"
              class="template-editor"
              :class="{ 'drag-over': isDragOver }"
            />
            <div v-if="hasPlaceholders" class="placeholder-indicator">
              <span>✨ 包含 {{ placeholderCount }} 个占位符</span>
            </div>
          </div>
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" @click="saveTemplate">保存</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { useMessage, NButton, NSpace } from 'naive-ui'
import { NDataTable, NInput, NSelect, NForm, NFormItem, NModal, NTag, NIcon, NAlert } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { CopyOutline, ConstructOutline, TrashOutline } from '@vicons/ionicons5'
import emitter from '@/utils/eventbus'
import { useRouter } from 'vue-router'

interface PromptTemplate {
  id: string
  name: string
  category?: string
  tags?: string[]
  content: string
  locked?: boolean
  is_default?: boolean
  updated_at: string
}

const STORAGE_KEY = 'prompt_templates'

const router = useRouter()
const message = useMessage()
const search = ref('')
const showModal = ref(false)
const isEditing = ref(false)
const editingId = ref<string | null>(null)
const contentInput = ref<any>(null)

// Placeholder definitions with detailed explanations
const placeholders = [
  { 
    value: '{task_title}', 
    label: '任务标题',
    description: '广告任务的标题名称，例如："母亲节礼物推荐"、"夏季新品促销"'
  },
  { 
    value: '{hashtags}', 
    label: '话题标签',
    description: '任务要求的社交媒体话题标签，用空格分隔，例如："#母亲节礼物 #感恩妈妈 #特惠好物"'
  },
  { 
    value: '{tag_require}', 
    label: '标签要求',
    description: '任务对标签使用的具体要求，例如："必须包含品牌话题"、"至少使用3个相关标签"'
  },
  { 
    value: '{submission_rules}', 
    label: '提交规则',
    description: '任务的提交规则和注意事项，例如："字数200-500字，配图3-5张，必须包含产品链接"'
  }
]

// Drag and drop handlers
let draggedPlaceholder = ''
const isDragOver = ref(false)

const handleDragStart = (event: DragEvent, placeholder: string) => {
  draggedPlaceholder = placeholder
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'copy'
    event.dataTransfer.setData('text/plain', placeholder)
  }
}

const handleDragEnter = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = true
}

const handleDragLeave = (event: DragEvent) => {
  event.preventDefault()
  // Only set to false if we're leaving the textarea entirely
  const target = event.target as HTMLElement
  if (!target.closest('.template-editor')) {
    isDragOver.value = false
  }
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  event.stopPropagation()
  isDragOver.value = false
  
  const placeholder = event.dataTransfer?.getData('text/plain') || draggedPlaceholder
  
  if (placeholder && contentInput.value) {
    // Get the textarea element
    const textarea = contentInput.value.textareaElRef as HTMLTextAreaElement
    if (textarea) {
      // Save current scroll position
      const scrollTop = textarea.scrollTop
      
      // Calculate insertion position based on mouse coordinates
      const cursorPos = getTextareaCaretPosition(textarea, event.clientX, event.clientY)
      
      // Focus and set selection at insertion point
      textarea.focus()
      textarea.setSelectionRange(cursorPos, cursorPos)
      
      // Use execCommand to insert text - this properly adds to undo history
      const insertSuccess = document.execCommand('insertText', false, placeholder)
      
      if (!insertSuccess) {
        // Fallback for browsers that don't support execCommand
        const textBefore = form.value.content.substring(0, cursorPos)
        const textAfter = form.value.content.substring(cursorPos)
        form.value.content = textBefore + placeholder + textAfter
        
        setTimeout(() => {
          textarea.setSelectionRange(cursorPos + placeholder.length, cursorPos + placeholder.length)
        }, 0)
      }
      
      // Restore scroll position
      setTimeout(() => {
        textarea.scrollTop = scrollTop
      }, 0)
    }
  }
}

// Helper function to calculate caret position from mouse coordinates
const getTextareaCaretPosition = (textarea: HTMLTextAreaElement, clientX: number, clientY: number): number => {
  const rect = textarea.getBoundingClientRect()
  const x = clientX - rect.left
  const y = clientY - rect.top
  
  // Get textarea styles
  const style = window.getComputedStyle(textarea)
  const paddingLeft = parseFloat(style.paddingLeft)
  const paddingTop = parseFloat(style.paddingTop)
  const lineHeight = parseFloat(style.lineHeight) || 20
  const fontSize = parseFloat(style.fontSize) || 13
  
  // Calculate approximate line and column
  const scrollTop = textarea.scrollTop
  const scrollLeft = textarea.scrollLeft
  const adjustedY = y + scrollTop - paddingTop
  const adjustedX = x + scrollLeft - paddingLeft
  const lineIndex = Math.max(0, Math.floor(adjustedY / lineHeight))
  
  // Split content into lines
  const lines = textarea.value.split('\n')
  
  // If clicking beyond text, append to end
  if (lineIndex >= lines.length) {
    return textarea.value.length
  }
  
  // Calculate position up to the target line
  let position = 0
  for (let i = 0; i < lineIndex && i < lines.length; i++) {
    position += lines[i].length + 1 // +1 for newline
  }
  
  // Calculate column position within the line using canvas measurement
  const targetLine = lines[lineIndex] || ''
  if (targetLine.length === 0) {
    return position
  }
  
  // Create a canvas to measure text width accurately
  const canvas = document.createElement('canvas')
  const context = canvas.getContext('2d')
  if (context) {
    context.font = `${fontSize}px Monaco, Menlo, 'Ubuntu Mono', monospace`
    
    // Binary search to find the closest character position
    let left = 0
    let right = targetLine.length
    let bestPos = 0
    let minDist = Infinity
    
    while (left <= right) {
      const mid = Math.floor((left + right) / 2)
      const textWidth = context.measureText(targetLine.substring(0, mid)).width
      const dist = Math.abs(textWidth - adjustedX)
      
      if (dist < minDist) {
        minDist = dist
        bestPos = mid
      }
      
      if (textWidth < adjustedX) {
        left = mid + 1
      } else {
        right = mid - 1
      }
    }
    
    position += bestPos
  } else {
    // Fallback: use character width approximation
    const charWidth = fontSize * 0.6 // Monospace approximation
    const columnIndex = Math.max(0, Math.floor(adjustedX / charWidth))
    position += Math.min(columnIndex, targetLine.length)
  }
  
  return Math.min(position, textarea.value.length)
}

// Check if template contains placeholders
const hasPlaceholders = computed(() => {
  if (!form.value.content) return false
  return placeholders.some(p => form.value.content.includes(p.value))
})

// Count placeholders in template
const placeholderCount = computed(() => {
  if (!form.value.content) return 0
  let count = 0
  placeholders.forEach(p => {
    const matches = form.value.content.match(new RegExp(p.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'))
    if (matches) count += matches.length
  })
  return count
})

const templates = ref<PromptTemplate[]>([])

const form = ref<PromptTemplate>({
  id: '',
  name: '',
  category: 'general',
  tags: [],
  content: '',
  updated_at: ''
})

const categoryOptions = [
  { label: '通用', value: 'general' },
  { label: '增强提示词', value: 'enhance' },
  { label: '文案生成', value: 'caption' },
  { label: '图像生成', value: 'image' }
]

const tagOptions = [
  { label: '通用', value: '通用' },
  { label: '风格', value: '风格' },
  { label: '品牌', value: '品牌' },
  { label: '活动', value: '活动' }
]

const filteredTemplates = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return templates.value
  return templates.value.filter(t =>
    t.name.toLowerCase().includes(q) ||
    (t.category || '').toLowerCase().includes(q) ||
    (t.tags || []).some(tag => tag.toLowerCase().includes(q))
  )
})

const modalTitle = computed(() => isEditing.value ? '编辑模板' : '新增模板')

const columns: DataTableColumns<PromptTemplate> = [
  { 
    title: '名称', 
    key: 'name',
    render(row) {
      return h('div', { style: 'display: flex; align-items: center; gap: 8px' }, [
        h('span', row.name),
        row.is_default ? h(NTag, { type: 'success', size: 'small' }, { default: () => '默认' }) : null
      ])
    }
  },
  { title: '分类', key: 'category' },
  { 
    title: '标签', 
    key: 'tags',
    render(row) {
      const tags = row.tags || []
      return h('div', tags.map(tag => h(NTag, { style: 'margin-right: 6px' }, { default: () => tag })))
    }
  },
  { 
    title: '更新时间', 
    key: 'updated_at',
    render(row) {
      return new Date(row.updated_at).toLocaleString()
    }
  },
  {
    title: '操作',
    key: 'actions',
    render(row) {
      return h('div', { style: 'display: flex; gap: 4px; flex-wrap: wrap' }, [
        h(
          NButton,
          {
            size: 'small',
            type: row.is_default ? 'default' : 'warning',
            disabled: !!row.is_default,
            onClick: () => setAsDefault(row.id)
          },
          { default: () => row.is_default ? '已设为默认' : '设为默认' }
        ),
        h(
          NButton,
          {
            size: 'small',
            type: 'success',
            onClick: () => applyToAgent(row)
          },
          { default: () => [h(NIcon, null, { default: () => h(ConstructOutline) }), ' 应用'] }
        ),
        h(
          NButton,
          {
            size: 'small',
            onClick: () => copyContent(row.content)
          },
          { default: () => [h(NIcon, null, { default: () => h(CopyOutline) }), ' 复制'] }
        ),
        h(
          NButton,
          {
            size: 'small',
            type: 'info',
            disabled: !!row.locked,
            onClick: () => openEdit(row)
          },
          { default: () => '编辑' }
        ),
        h(
          NButton,
          {
            size: 'small',
            type: 'error',
            onClick: () => removeTemplate(row.id)
          },
          { default: () => [h(NIcon, null, { default: () => h(TrashOutline) }), ' 删除'] }
        )
      ])
    }
  }
]

function saveToStorage() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(templates.value))
}

function loadFromStorage() {
  const data = localStorage.getItem(STORAGE_KEY)
  if (data) {
    try {
      templates.value = JSON.parse(data)
    } catch {}
  }
}

async function loadDefaults() {
  try {
    // Remove old system templates that are no longer needed
    const systemTemplateIds = ['enhance_system', 'caption_system']
    templates.value = templates.value.filter(t => !systemTemplateIds.includes(t.id))
    
    const resp = await fetch((import.meta.env.VITE_API_BASE_URL || '/api') + '/prompt/templates')
    const json = await resp.json()
    if (json && json.success && Array.isArray(json.data)) {
      // Filter out system templates from backend response
      const defaults = json.data
        .filter((t: any) => !t.tags?.includes('系统模板'))
        .map((t: any) => ({
          id: t.id,
          name: t.name,
          category: t.category,
          tags: t.tags || [],
          content: t.content,
          locked: true,
          updated_at: new Date().toISOString()
        }))
      const existingIds = new Set(templates.value.map(t => t.id))
      defaults.forEach((d: any) => {
        if (!existingIds.has(d.id)) templates.value.unshift(d)
      })
      saveToStorage()
    }
  } catch {}
}

function openCreate() {
  isEditing.value = false
  editingId.value = null
  form.value = {
    id: '',
    name: '',
    category: 'general',
    tags: [],
    content: '',
    updated_at: ''
  }
  showModal.value = true
}

function openEdit(row: PromptTemplate) {
  isEditing.value = true
  editingId.value = row.id
  form.value = { ...row }
  showModal.value = true
}

function saveTemplate() {
  if (!form.value.name || !form.value.content) {
    message.error('请填写名称和内容')
    return
  }
  if (isEditing.value && editingId.value) {
    const idx = templates.value.findIndex(t => t.id === editingId.value)
    if (idx !== -1) {
      templates.value[idx] = { ...form.value, updated_at: new Date().toISOString(), locked: false }
    }
  } else {
    const id = 'tpl_' + Math.random().toString(36).slice(2)
    templates.value.unshift({ ...form.value, id, updated_at: new Date().toISOString(), locked: false })
  }
  saveToStorage()
  showModal.value = false
  message.success('已保存模板')
}

function removeTemplate(id: string) {
  templates.value = templates.value.filter(t => t.id !== id)
  saveToStorage()
  message.success('已删除模板')
}

function copyContent(content: string) {
  navigator.clipboard.writeText(content)
  message.success('已复制到剪贴板')
}

function setAsDefault(id: string) {
  // Unset all other defaults
  templates.value.forEach(t => {
    t.is_default = t.id === id
  })
  saveToStorage()
  message.success('已设为默认模板')
}

function applyToAgent(row: PromptTemplate) {
  emitter.emit('apply-template-to-agent', row.content)
  router.push('/agent')
  message.success('已发送到托管配置')
}

onMounted(async () => {
  loadFromStorage()
  // Force remove system templates immediately (by ID, name, or tag)
  templates.value = templates.value.filter(t => {
    // Remove by specific IDs
    if (t.id === 'enhance_system' || t.id === 'caption_system') return false
    // Remove if name contains "系统模板"
    if (t.name?.includes('系统模板')) return false
    // Remove if tags contain "系统模板"
    if (t.tags?.includes('系统模板')) return false
    return true
  })
  saveToStorage()
  await loadDefaults()
})
</script>

<style scoped>
.templates-page {
  padding: 20px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* Editor wrapper */
.editor-wrapper {
  width: 100%;
}

/* Template editor styling */
.template-editor :deep(textarea) {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
  transition: all 0.3s ease;
}

/* Drag over state - green border */
.template-editor.drag-over :deep(textarea) {
  border-color: #18a058 !important;
  box-shadow: 0 0 0 2px rgba(24, 160, 88, 0.2) !important;
  background: rgba(24, 160, 88, 0.02);
}

/* Placeholder styling in template content */
.template-editor :deep(textarea)::placeholder {
  color: #999;
}

/* Placeholder indicator badge */
.placeholder-indicator {
  margin-top: 8px;
  padding: 6px 12px;
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.15) 0%, rgba(255, 152, 0, 0.1) 100%);
  border-left: 3px solid #ff9800;
  border-radius: 4px;
  font-size: 12px;
  color: #f57c00;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
</style>