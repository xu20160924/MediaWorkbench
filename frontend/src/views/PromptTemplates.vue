<template>
  <div class="templates-page">
    <div class="page-header">
      <h2>提示词模板</h2>
      <div class="header-actions">
        <n-input v-model:value="search" placeholder="搜索模板" style="width: 260px" />
        <n-button type="primary" @click="openCreate">新增模板</n-button>
      </div>
    </div>

    <n-card>
      <n-data-table :columns="columns" :data="filteredTemplates" :pagination="{ pageSize: 8 }" />
    </n-card>

    <n-modal v-model:show="showModal" preset="card" :title="modalTitle" :style="{ width: '720px' }">
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
          <n-input v-model:value="form.content" type="textarea" :rows="12" />
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
import { NCard, NDataTable, NInput, NSelect, NForm, NFormItem, NModal, NTag, NIcon } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { CopyOutline, SendOutline, ConstructOutline, TrashOutline } from '@vicons/ionicons5'
import emitter from '@/utils/eventbus'
import { useRouter } from 'vue-router'

interface PromptTemplate {
  id: string
  name: string
  category?: string
  tags?: string[]
  content: string
  locked?: boolean
  updated_at: string
}

const STORAGE_KEY = 'prompt_templates'

const router = useRouter()
const message = useMessage()
const search = ref('')
const showModal = ref(false)
const isEditing = ref(false)
const editingId = ref<string | null>(null)

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

const columns: DataTableColumns<PromptTemplate> = [
  { title: '名称', key: 'name' },
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
      return h('div', [
        h(
          NButton,
          {
            size: 'small',
            type: 'success',
            style: 'margin-right: 8px',
            onClick: () => applyToAgent(row)
          },
          { default: () => [h(NIcon, null, { default: () => h(ConstructOutline) }), ' 应用到托管'] }
        ),
        h(
          NButton,
          {
            size: 'small',
            style: 'margin-right: 8px',
            onClick: () => copyContent(row.content)
          },
          { default: () => [h(NIcon, null, { default: () => h(CopyOutline) }), ' 复制'] }
        ),
        h(
          NButton,
          {
            size: 'small',
            type: 'info',
            style: 'margin-right: 8px',
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
            disabled: !!row.locked,
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
    const resp = await fetch((import.meta.env.VITE_API_BASE_URL || '/api') + '/prompt/templates')
    const json = await resp.json()
    if (json && json.success && Array.isArray(json.data)) {
      const defaults = json.data.map((t: any) => ({
        id: t.id,
        name: t.name,
        category: t.category,
        tags: t.tags || [],
        content: t.content,
        locked: true,
        updated_at: new Date().toISOString()
      }))
      const existingIds = new Set(templates.value.map(t => t.id))
      defaults.forEach(d => {
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

function applyToAgent(row: PromptTemplate) {
  emitter.emit('apply-template-to-agent', row.content)
  router.push('/agent')
  message.success('已发送到托管配置')
}

onMounted(async () => {
  loadFromStorage()
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
</style>