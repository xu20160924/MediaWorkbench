<template>
  <div class="advertisement-tasks-container">
    <div class="header-section">
      <h2>广告任务管理</h2>
      <div class="header-actions">
        <n-button type="primary" @click="showCreateModal = true">
          <template #icon>
            <n-icon><Add /></n-icon>
          </template>
          创建任务
        </n-button>
        <n-button @click="loadTasks">
          <template #icon>
            <n-icon><Refresh /></n-icon>
          </template>
          刷新
        </n-button>
      </div>
    </div>

    <!-- Statistics Cards -->
    <div class="stats-section">
      <n-space>
        <n-card size="small" class="stat-card">
          <n-statistic label="总任务" :value="stats.total" />
        </n-card>
        <n-card size="small" class="stat-card active">
          <n-statistic label="进行中" :value="stats.active" />
        </n-card>
        <n-card size="small" class="stat-card completed">
          <n-statistic label="已完成" :value="stats.completed" />
        </n-card>
        <n-card size="small" class="stat-card expired">
          <n-statistic label="已过期" :value="stats.expired" />
        </n-card>
      </n-space>
    </div>

    <!-- Filter Section -->
    <div class="filter-section">
      <n-space>
        <n-select
          v-model:value="filterStatus"
          :options="statusOptions"
          placeholder="状态筛选"
          clearable
          style="width: 150px"
          @update:value="loadTasks"
        />
      </n-space>
    </div>

    <!-- Tasks Table -->
    <n-data-table
      :columns="columns"
      :data="tasks"
      :loading="loading"
      :pagination="pagination"
      :row-key="(row: AdvertisementTask) => row.id"
      remote
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
    />

    <!-- Create/Edit Modal -->
    <n-modal
      v-model:show="showCreateModal"
      preset="card"
      :title="editingTask ? '编辑任务' : '创建任务'"
      style="width: 800px"
    >
      <n-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-placement="left"
        label-width="120px"
      >
        <n-form-item label="任务ID" path="task_id">
          <n-input v-model:value="formData.task_id" :disabled="!!editingTask" placeholder="唯一任务标识" />
        </n-form-item>
        <n-form-item label="任务标题" path="task_title">
          <n-input v-model:value="formData.task_title" placeholder="任务标题" />
        </n-form-item>
        <n-form-item label="卡片标题" path="card_title">
          <n-input v-model:value="formData.card_title" placeholder="显示卡片标题" />
        </n-form-item>
        <n-form-item label="投稿规则" path="submission_rules">
          <n-input
            v-model:value="formData.submission_rules"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 6 }"
            placeholder="投稿规则说明"
          />
        </n-form-item>
        <n-form-item label="话题要求" path="tag_require">
          <n-input
            v-model:value="formData.tag_require"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 4 }"
            placeholder="必须包含的话题标签"
          />
        </n-form-item>
        <n-form-item label="图片链接" path="image_url">
          <n-input
            v-model:value="formData.image_url"
            placeholder="广告图片URL"
          />
        </n-form-item>
        <n-form-item label="话题标签" path="hashtags">
          <n-dynamic-tags v-model:value="formData.hashtags" />
        </n-form-item>
        <n-form-item label="结算方式" path="settlement_way">
          <n-input
            v-model:value="formData.settlement_way"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 6 }"
            placeholder="结算规则说明"
          />
        </n-form-item>
        <n-form-item label="奖金池金额" path="ads_pool_amount">
          <n-input-number
            v-model:value="formData.ads_pool_amount"
            :min="0"
            :precision="2"
            placeholder="奖金池金额"
            style="width: 100%"
          />
        </n-form-item>
        <n-form-item label="状态" path="status">
          <n-select
            v-model:value="formData.status"
            :options="statusOptions"
            placeholder="选择状态"
          />
        </n-form-item>
        <n-form-item label="截止日期" path="deadline">
          <n-date-picker
            v-model:value="formData.deadline"
            type="datetime"
            clearable
            style="width: 100%"
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="closeModal">取消</n-button>
          <n-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ editingTask ? '更新' : '创建' }}
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- View Details Modal -->
    <n-modal
      v-model:show="showDetailModal"
      preset="card"
      title="任务详情"
      style="width: 900px; max-height: 80vh; overflow-y: auto;"
    >
      <n-descriptions v-if="viewingTask" label-placement="left" :column="1" :label-style="{ width: '120px', flexShrink: 0 }" bordered>
        <n-descriptions-item label="任务ID">{{ viewingTask.task_id }}</n-descriptions-item>
        <n-descriptions-item label="任务标题">{{ viewingTask.task_title }}</n-descriptions-item>
        <n-descriptions-item label="卡片标题">{{ viewingTask.card_title }}</n-descriptions-item>
        <n-descriptions-item label="任务类型">
          <n-tag :type="viewingTask.task_type === 'community' || viewingTask.task_type === 'community_special' ? 'warning' : 'default'">
            {{ viewingTask.task_type === 'community' || viewingTask.task_type === 'community_special' ? '社群任务' : '普通任务' }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="广告图片">
          <div v-if="viewingTask.image">
            <img 
              :src="'http://localhost:5001' + viewingTask.image.url" 
              alt="广告图片" 
              style="max-width: 100%; max-height: 400px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" 
            />
            <div v-if="!viewingTask.image.external && viewingTask.image.path" style="margin-top: 8px; font-size: 12px; color: #999;">
              📁 本地图片: {{ viewingTask.image.path }}
            </div>
          </div>
          <div v-else style="color: #999; font-style: italic;">
            暂无图片
          </div>
        </n-descriptions-item>
        <n-descriptions-item label="投稿规则">
          <div style="white-space: pre-wrap">{{ viewingTask.submission_rules }}</div>
        </n-descriptions-item>
        <n-descriptions-item label="话题要求">
          <div style="white-space: pre-wrap">{{ viewingTask.tag_require }}</div>
        </n-descriptions-item>
        <n-descriptions-item label="话题标签">
          <div v-if="viewingTask.hashtags && viewingTask.hashtags.length > 0">
            <!-- Display formatted tags with # -->
            <div style="margin-bottom: 12px;">
              <n-space wrap :size="8">
                <n-tag 
                  v-for="(tag, index) in viewingTask.hashtags" 
                  :key="index" 
                  type="info"
                  size="medium"
                  :bordered="false"
                  style="padding: 6px 12px; font-weight: 500;"
                >
                  {{ tag.startsWith('#') ? tag : '#' + tag }}
                </n-tag>
              </n-space>
            </div>
            
            <!-- Display raw tags from database -->
            <div style="margin-top: 8px; padding: 8px 12px; background: #fafafa; border-radius: 4px; border-left: 3px solid #18a058;">
              <div style="font-size: 12px; color: #666; margin-bottom: 4px; font-weight: 500;">
                📋 数据库原始标签：
              </div>
              <div style="font-size: 13px; color: #333; font-family: monospace;">
                {{ viewingTask.hashtags.join(', ') }}
              </div>
            </div>
            
            <div style="margin-top: 10px; padding: 8px 12px; background: #f0f7ff; border-radius: 4px; font-size: 12px; color: #666;">
              💡 共 {{ viewingTask.hashtags.length }} 个标签 - 发布时需要包含以上所有标签
            </div>
          </div>
          <div v-else style="color: #999; font-style: italic;">
            暂无标签要求
          </div>
        </n-descriptions-item>
        <n-descriptions-item label="结算方式">
          <div style="white-space: pre-wrap">{{ viewingTask.settlement_way || '-' }}</div>
        </n-descriptions-item>
        <n-descriptions-item label="奖金池">
          <n-text type="success" strong style="font-size: 18px;">¥{{ viewingTask.ads_pool_amount }}</n-text>
        </n-descriptions-item>
        <n-descriptions-item label="状态">
          <n-tag :type="getStatusType(viewingTask.status)">
            {{ getStatusLabel(viewingTask.status) }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="参与状态">
          <n-space>
            <n-tag :type="viewingTask.participated ? 'success' : 'default'">
              {{ viewingTask.participated ? '已参与' : '未参与' }}
            </n-tag>
            <span v-if="viewingTask.participation_count">参与次数: {{ viewingTask.participation_count }}</span>
          </n-space>
        </n-descriptions-item>
        <n-descriptions-item label="规则卡片">
          <div v-if="viewingTask.rule_cards && viewingTask.rule_cards.length > 0">
            <div style="margin-bottom: 12px; padding: 8px; background: #f0f7ff; border-radius: 4px;">
              <n-text depth="3">共 {{ viewingTask.rule_cards_count }} 个规则，{{ viewingTask.available_rule_cards_count }} 个可用</n-text>
            </div>
            <n-space vertical size="large">
              <n-card
                v-for="card in viewingTask.rule_cards"
                :key="card.id"
                size="small"
                :bordered="true"
                style="box-shadow: 0 1px 3px rgba(0,0,0,0.1);"
              >
                <div style="display: flex; gap: 16px;">
                  <!-- Left: Image -->
                  <div v-if="card.image" style="flex-shrink: 0;">
                    <n-image
                      :src="card.image.external ? card.image.url : `http://localhost:5001${card.image.url}`"
                      width="140"
                      height="140"
                      object-fit="cover"
                      preview
                      style="border-radius: 4px;"
                      fallback-src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Crect fill='%23f5f5f5' width='140' height='140'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%23999' font-size='12'%3E暂无截图%3C/text%3E%3C/svg%3E"
                    />
                  </div>
                  <div v-else style="flex-shrink: 0; width: 140px; height: 140px; background: #f5f5f5; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 12px;">
                    暂无截图
                  </div>
                  
                  <!-- Middle: Content -->
                  <div style="flex: 1; display: flex; flex-direction: column; gap: 12px;">
                    <!-- Title and status row -->
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                      <n-text strong style="font-size: 16px;">{{ card.rule_name || `规则卡片 ${card.display_order + 1}` }}</n-text>
                      <n-space :size="8">
                        <n-tag :type="card.participated ? 'success' : 'default'" size="small" round>
                          {{ card.participated ? '✓ 已参与' : '○ 未参与' }}
                        </n-tag>
                        <n-tag v-if="card.participation_count > 0" type="info" size="small" round>
                          {{ card.participation_count }}次
                        </n-tag>
                      </n-space>
                    </div>
                    
                    <!-- Description if exists -->
                    <div v-if="card.rule_description" style="padding: 8px; background: #f5f5f5; border-radius: 4px;">
                      <n-text depth="3" style="font-size: 13px;">{{ card.rule_description }}</n-text>
                    </div>
                    
                    <!-- Structured fields as separate cards -->
                    <n-space vertical size="medium">
                      <n-card v-if="card.submission_rules" size="small" style="background: #f0f9ff; border-left: 3px solid #3b82f6;">
                        <template #header>
                          <n-text strong style="font-size: 13px; color: #3b82f6;">📝 投稿规则</n-text>
                        </template>
                        <n-text style="font-size: 13px; white-space: pre-wrap; line-height: 1.6;">{{ card.submission_rules }}</n-text>
                      </n-card>
                      
                      <n-card v-if="card.tag_require" size="small" style="background: #f0fdf4; border-left: 3px solid #10b981;">
                        <template #header>
                          <n-text strong style="font-size: 13px; color: #10b981;">🏷️ 话题要求</n-text>
                        </template>
                        <n-text style="font-size: 13px; white-space: pre-wrap; line-height: 1.6;">{{ card.tag_require }}</n-text>
                      </n-card>
                      
                      <n-card v-if="card.settlement_way" size="small" style="background: #fffbeb; border-left: 3px solid #f59e0b;">
                        <template #header>
                          <n-text strong style="font-size: 13px; color: #f59e0b;">💰 结算方式</n-text>
                        </template>
                        <n-text style="font-size: 13px; white-space: pre-wrap; line-height: 1.6;">{{ card.settlement_way }}</n-text>
                      </n-card>
                    </n-space>
                    
                    <!-- Timestamp info -->
                    <div v-if="card.last_participated_at" style="margin-top: 4px;">
                      <n-text depth="3" style="font-size: 12px; color: #999;">
                        最后参与: {{ formatDate(card.last_participated_at) }}
                      </n-text>
                    </div>
                  </div>
                  
                  <!-- Right: Action buttons -->
                  <div style="flex-shrink: 0; display: flex; align-items: center; gap: 8px;">
                    <n-button
                      v-if="!card.participated"
                      type="warning"
                      size="small"
                      secondary
                      @click="markRuleCardParticipated(card.id)"
                      style="min-width: 90px;"
                    >
                      标记已参与
                    </n-button>
                    <n-button
                      :type="card.participated ? 'default' : 'success'"
                      size="small"
                      :disabled="card.participated"
                      @click="selectRuleCard(card, viewingTask)"
                      style="min-width: 80px;"
                    >
                      {{ card.participated ? '✓ 已参与' : '参与' }}
                    </n-button>
                  </div>
                </div>
              </n-card>
            </n-space>
          </div>
          <n-text v-else depth="3" style="font-style: italic;">暂无规则卡片</n-text>
        </n-descriptions-item>
        <n-descriptions-item label="创建时间">{{ formatDate(viewingTask.created_at) }}</n-descriptions-item>
        <n-descriptions-item label="更新时间">{{ formatDate(viewingTask.updated_at) }}</n-descriptions-item>
        <n-descriptions-item v-if="viewingTask.deadline" label="截止日期">
          {{ formatDate(viewingTask.deadline) }}
        </n-descriptions-item>
      </n-descriptions>
    </n-modal>

    <!-- Participation Modal -->
    <n-modal
      v-model:show="showParticipateModal"
      preset="card"
      title="参与广告任务"
      style="width: 600px"
    >
      <div v-if="participatingTask">
        <n-alert type="info" style="margin-bottom: 16px;">
          <template #header>
            任务：{{ participatingTask.task_title }}
          </template>
          系统将使用任务信息生成文本提示词，并通过工作流生成内容
        </n-alert>

        <n-form ref="participateFormRef" :model="participateFormData">
          <n-form-item label="选择工作流" required>
            <n-select
              v-model:value="participateFormData.workflow_id"
              placeholder="请选择要执行的工作流"
              :options="workflows.map(w => ({ label: w.name, value: w.id }))"
            />
          </n-form-item>

          <n-form-item label="包含任务图片">
            <n-space vertical>
              <n-switch v-model:value="participateFormData.include_rule_image">
                <template #checked>
                  启用
                </template>
                <template #unchecked>
                  禁用
                </template>
              </n-switch>
              <n-text depth="3" style="font-size: 12px;">
                {{ participateFormData.include_rule_image ? '✅ 将任务图片作为规则图传入工作流' : '默认禁用 - 仅使用文本提示词' }}
                {{ !participatingTask.image_path && participateFormData.include_rule_image ? '（当前任务无图片）' : '' }}
              </n-text>
            </n-space>
          </n-form-item>

          <n-divider />

          <div style="margin-bottom: 16px;">
            <n-text strong>预览提示词：</n-text>
            <n-card size="small" style="margin-top: 8px; background: #f5f5f5;">
              <div style="white-space: pre-wrap; font-size: 12px;">
                任务: {{ participatingTask.task_title }}
                
                <span v-if="participatingTask.hashtags && participatingTask.hashtags.length > 0">
话题标签: {{ participatingTask.hashtags.join(' ') }}
                </span>
                <span v-if="participatingTask.tag_require">
话题要求: {{ participatingTask.tag_require }}
                </span>
                <span v-if="participatingTask.submission_rules">
投稿规则: {{ participatingTask.submission_rules }}
                </span>
              </div>
            </n-card>
          </div>

          <div class="form-actions" style="display: flex; justify-content: flex-end; gap: 8px;">
            <n-button @click="closeParticipateModal">取消</n-button>
            <n-button type="primary" @click="handleParticipate" :loading="participateLoading">
              {{ participateLoading ? '处理中...' : '开始参与' }}
            </n-button>
          </div>
        </n-form>
      </div>
    </n-modal>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onUnmounted, h } from 'vue'
import { useRouter } from 'vue-router'
import {
  NButton,
  NDataTable,
  NSpace,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSelect,
  NDatePicker,
  NTag,
  NDynamicTags,
  NIcon,
  NCard,
  NStatistic,
  NDescriptions,
  NDescriptionsItem,
  NText,
  NImage,
  NEmpty,
  NSwitch,
  useMessage,
  useDialog,
  DataTableColumns
} from 'naive-ui'
import { Add, Refresh } from '@vicons/ionicons5'
import axios from 'axios'

interface RuleCard {
  id: number
  task_id: number
  rule_name?: string
  rule_description?: string
  submission_rules?: string
  tag_require?: string
  settlement_way?: string
  image_path?: string
  image_url?: string
  image?: {
    path?: string
    url: string
    external?: boolean
  }
  display_order: number
  participated: boolean
  participation_count: number
  last_participated_at?: string
  created_at?: string
  updated_at?: string
}

interface AdvertisementTask {
  id: number
  task_id: string
  task_title: string
  card_title: string
  submission_rules: string
  tag_require: string
  settlement_way: string
  hashtags?: string[]
  image_path?: string
  image_url?: string
  image?: {
    path?: string
    url: string
    external?: boolean
  }
  ads_pool_amount: number
  status: string
  task_type: string
  participated?: boolean
  participation_count?: number
  last_participated_at?: string
  created_at: string
  updated_at: string
  deadline?: string
  extra_data?: any
  rule_cards?: RuleCard[]
  rule_cards_count?: number
  available_rule_cards_count?: number
}

export default defineComponent({
  name: 'AdvertisementTasks',
  components: {
    NButton,
    NDataTable,
    NSpace,
    NModal,
    NForm,
    NFormItem,
    NInput,
    NInputNumber,
    NSelect,
    NDatePicker,
    NTag,
    NDynamicTags,
    NIcon,
    NCard,
    NStatistic,
    NDescriptions,
    NDescriptionsItem,
    NText,
    NImage,
    NEmpty,
    NSwitch,
    Add,
    Refresh
  },
  setup() {
    const message = useMessage()
    const dialog = useDialog()
    const router = useRouter()
    
    const tasks = ref<AdvertisementTask[]>([])
    const loading = ref(false)
    const submitting = ref(false)
    const showCreateModal = ref(false)
    const showDetailModal = ref(false)
    const editingTask = ref<AdvertisementTask | null>(null)
    const viewingTask = ref<AdvertisementTask | null>(null)
    const filterStatus = ref<string | null>(null)
    
    const stats = ref({
      total: 0,
      active: 0,
      completed: 0,
      expired: 0
    })
    
    // Participation modal state
    const showParticipateModal = ref(false)
    const participatingTask = ref<AdvertisementTask | null>(null)
    const participateFormData = ref({
      workflow_id: null as number | null,
      include_rule_image: false
    })
    const workflows = ref<any[]>([])
    const participateLoading = ref(false)
    
    const pagination = ref({
      page: 1,
      pageSize: 20,
      itemCount: 0,
      pageCount: 1,
      showSizePicker: true,
      pageSizes: [10, 20, 50, 100],
      prefix: ({ itemCount }: { itemCount?: number }) => `共 ${itemCount ?? 0} 条`
    })
    
    const formData = ref({
      task_id: '',
      task_title: '',
      card_title: '',
      submission_rules: '',
      tag_require: '',
      settlement_way: '',
      hashtags: [] as string[],
      image_url: '',
      ads_pool_amount: 0,
      status: 'active',
      deadline: null as number | null
    })
    
    const formRules = {
      task_id: { required: true, message: '请输入任务ID', trigger: 'blur' },
      task_title: { required: true, message: '请输入任务标题', trigger: 'blur' }
    }
    
    const statusOptions = [
      { label: '全部', value: null },
      { label: '进行中', value: 'active' },
      { label: '已完成', value: 'completed' },
      { label: '已过期', value: 'expired' },
      { label: '草稿', value: 'draft' }
    ]
    
    const getStatusType = (status: string) => {
      const types: Record<string, any> = {
        active: 'success',
        completed: 'info',
        expired: 'warning',
        draft: 'default'
      }
      return types[status] || 'default'
    }
    
    const getStatusLabel = (status: string) => {
      const labels: Record<string, string> = {
        active: '进行中',
        completed: '已完成',
        expired: '已过期',
        draft: '草稿'
      }
      return labels[status] || status
    }
    
    const formatDate = (dateStr: string) => {
      if (!dateStr) return '-'
      return new Date(dateStr).toLocaleString('zh-CN')
    }
    

    
    const loadTasks = async () => {
      loading.value = true
      try {
        const params: any = {
          page: pagination.value.page,
          per_page: pagination.value.pageSize
        }
        if (filterStatus.value) {
          params.status = filterStatus.value
        }
        
        const response = await axios.get('http://localhost:5001/api/advertisement-tasks/', { params })
        if (response.data.success) {
          tasks.value = response.data.data.tasks
          pagination.value.itemCount = response.data.data.total
          pagination.value.pageCount = response.data.data.total_pages || Math.ceil(response.data.data.total / pagination.value.pageSize)
        } else {
          message.error(response.data.message || '加载任务失败')
        }
      } catch (error) {
        message.error('加载任务失败: ' + (error as Error).message)
      } finally {
        loading.value = false
      }
    }
    
    const loadStats = async () => {
      try {
        const response = await axios.get('http://localhost:5001/api/advertisement-tasks/stats')
        if (response.data.success) {
          stats.value = response.data.data
        }
      } catch (error) {
        console.error('Failed to load stats:', error)
      }
    }
    
    const handlePageChange = (page: number) => {
      pagination.value.page = page
      loadTasks()
    }
    
    const handlePageSizeChange = (pageSize: number) => {
      pagination.value.pageSize = pageSize
      pagination.value.page = 1  // Reset to first page when page size changes
      loadTasks()
    }
    
    const viewTask = (task: AdvertisementTask) => {
      viewingTask.value = task
      showDetailModal.value = true
    }
    
    const editTask = (task: AdvertisementTask) => {
      editingTask.value = task
      formData.value = {
        task_id: task.task_id,
        task_title: task.task_title,
        card_title: task.card_title || '',
        submission_rules: task.submission_rules || '',
        tag_require: task.tag_require || '',
        settlement_way: task.settlement_way || '',
        hashtags: task.hashtags || [],
        image_url: task.image_url || '',
        ads_pool_amount: task.ads_pool_amount,
        status: task.status,
        deadline: task.deadline ? new Date(task.deadline).getTime() : null
      }
      showCreateModal.value = true
    }
    
    const selectedRuleCard = ref<RuleCard | null>(null)
    
    const markRuleCardParticipated = async (ruleCardId: number) => {
      try {
        const response = await axios.patch(
          `http://localhost:5001/api/advertisement-tasks/rule-card/${ruleCardId}/participated`
        )
        if (response.data.success) {
          message.success('已标记为已参与')
          
          // Update the rule card in viewingTask if modal is open
          if (viewingTask.value && viewingTask.value.rule_cards) {
            const cardIndex = viewingTask.value.rule_cards.findIndex((c: RuleCard) => c.id === ruleCardId)
            if (cardIndex !== -1) {
              viewingTask.value.rule_cards[cardIndex] = response.data.data
            }
          }
          
          loadTasks()
          loadStats()
        } else {
          message.error(response.data.message || '标记失败')
        }
      } catch (error) {
        message.error('标记失败: ' + (error as Error).message)
      }
    }
    
    const selectRuleCard = (card: RuleCard, task: AdvertisementTask) => {
      if (card.participated) {
        message.warning('该规则卡片已被使用过')
        return
      }
      selectedRuleCard.value = card
      message.info(`已选择: ${card.rule_name || '规则卡片'}`, {
        duration: 2000
      })
      // Open participate modal with this task and pre-selected rule card
      openParticipateModal(task)
    }
    
    const deleteTask = (task: AdvertisementTask) => {
      dialog.warning({
        title: '确认删除',
        content: `确定要删除任务 "${task.task_title}" 吗？此操作不可恢复。`,
        positiveText: '删除',
        negativeText: '取消',
        onPositiveClick: async () => {
          try {
            const response = await axios.delete(`http://localhost:5001/api/advertisement-tasks/${task.id}`)
            if (response.data.success) {
              message.success('删除成功')
              loadTasks()
              loadStats()
            } else {
              message.error(response.data.message || '删除失败')
            }
          } catch (error) {
            message.error('删除失败: ' + (error as Error).message)
          }
        }
      })
    }

    const columns: DataTableColumns<AdvertisementTask> = [
      {
        type: 'expand',
        expandable: (row) => {
          return !!(row.rule_cards && row.rule_cards.length > 0)
        },
        renderExpand: (row) => {
          if (!row.rule_cards || row.rule_cards.length === 0) {
            return h('div', { class: 'rule-cards-expand', style: 'padding: 16px;' }, [
              h(NEmpty, { description: '暂无规则卡片', size: 'small' })
            ])
          }
          
          return h('div', { class: 'rule-cards-expand', style: 'padding: 16px; background: #fafafa;' }, [
            h(NSpace, { vertical: true, size: 'large' }, {
              default: () => (row.rule_cards || []).map((card: RuleCard) => 
                h(NCard, { 
                  size: 'small', 
                  bordered: true,
                  style: 'background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'
                }, {
                  default: () => h('div', { style: 'display: flex; gap: 16px;' }, [
                    // Left: Image
                    card.image ? h('div', { style: 'flex-shrink: 0;' }, [
                      h(NImage, {
                        src: card.image.external ? card.image.url : `http://localhost:5001${card.image.url}`,
                        width: 120,
                        height: 120,
                        objectFit: 'cover',
                        preview: true,
                        fallbackSrc: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Crect fill='%23f5f5f5' width='120' height='120'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%23999' font-size='12'%3E暂无截图%3C/text%3E%3C/svg%3E",
                        style: 'border-radius: 4px;'
                      })
                    ]) : h('div', { 
                      style: 'flex-shrink: 0; width: 120px; height: 120px; background: #f5f5f5; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 12px;' 
                    }, '暂无截图'),
                    // Middle: Content
                    h('div', { style: 'flex: 1; display: flex; flex-direction: column; gap: 12px;' }, [
                      // Title and status row
                      h('div', { style: 'display: flex; justify-content: space-between; align-items: center;' }, [
                        h(NText, { strong: true, style: 'font-size: 15px;' }, { 
                          default: () => card.rule_name || `规则卡片 ${card.display_order + 1}` 
                        }),
                        h(NSpace, { size: 8 }, {
                          default: () => [
                            h(NTag, { 
                              type: card.participated ? 'success' : 'default', 
                              size: 'small',
                              round: true
                            }, {
                              default: () => card.participated ? '✓ 已参与' : '○ 未参与'
                            }),
                            card.participation_count > 0 ? h(NTag, { 
                              type: 'info', 
                              size: 'small',
                              round: true
                            }, {
                              default: () => `${card.participation_count}次`
                            }) : null
                          ].filter(Boolean)
                        })
                      ]),
                      // Description if exists
                      card.rule_description ? h('div', { style: 'padding: 8px; background: #f5f5f5; border-radius: 4px;' }, [
                        h(NText, { depth: 3, style: 'font-size: 13px;' }, { default: () => card.rule_description })
                      ]) : null,
                      // Structured fields as separate cards
                      h(NSpace, { vertical: true, size: 'medium' }, {
                        default: () => [
                          card.submission_rules ? h(NCard, { 
                            size: 'small',
                            style: 'background: #f0f9ff; border-left: 3px solid #3b82f6;'
                          }, {
                            header: () => h(NText, { strong: true, style: 'font-size: 13px; color: #3b82f6;' }, { default: () => '📝 投稿规则' }),
                            default: () => h(NText, { style: 'font-size: 13px; white-space: pre-wrap; line-height: 1.6;' }, { default: () => card.submission_rules })
                          }) : null,
                          card.tag_require ? h(NCard, { 
                            size: 'small',
                            style: 'background: #f0fdf4; border-left: 3px solid #10b981;'
                          }, {
                            header: () => h(NText, { strong: true, style: 'font-size: 13px; color: #10b981;' }, { default: () => '🏷️ 话题要求' }),
                            default: () => h(NText, { style: 'font-size: 13px; white-space: pre-wrap; line-height: 1.6;' }, { default: () => card.tag_require })
                          }) : null,
                          card.settlement_way ? h(NCard, { 
                            size: 'small',
                            style: 'background: #fffbeb; border-left: 3px solid #f59e0b;'
                          }, {
                            header: () => h(NText, { strong: true, style: 'font-size: 13px; color: #f59e0b;' }, { default: () => '💰 结算方式' }),
                            default: () => h(NText, { style: 'font-size: 13px; white-space: pre-wrap; line-height: 1.6;' }, { default: () => card.settlement_way })
                          }) : null
                        ].filter(Boolean)
                      })
                    ]),
                    // Right: Action buttons
                    h('div', { style: 'flex-shrink: 0; display: flex; align-items: center; gap: 8px;' }, [
                      // Mark as participated button (only for unparticipated)
                      !card.participated ? h(NButton, {
                        type: 'warning',
                        size: 'small',
                        secondary: true,
                        onClick: () => markRuleCardParticipated(card.id),
                        style: 'min-width: 90px;'
                      }, {
                        default: () => '标记已参与'
                      }) : null,
                      // Normal participate button
                      h(NButton, {
                        type: card.participated ? 'default' : 'success',
                        size: 'small',
                        disabled: card.participated,
                        onClick: () => selectRuleCard(card, row),
                        style: 'min-width: 80px;'
                      }, {
                        default: () => card.participated ? '✓ 已参与' : '参与'
                      })
                    ].filter(Boolean))
                  ].filter(Boolean))
                })
              )
            })
          ])
        }
      },
      { title: '任务ID', key: 'task_id', width: 100, ellipsis: { tooltip: true } },
      { title: '任务标题', key: 'task_title', minWidth: 200, ellipsis: { tooltip: true } },
      {
        title: '类型',
        key: 'task_type',
        width: 70,
        render: (row) => {
          const isCommunity = row.task_type === 'community' || row.task_type === 'community_special'
          return h(
            NTag,
            { type: isCommunity ? 'warning' : 'default', size: 'small' },
            { default: () => isCommunity ? '社群' : '普通' }
          )
        }
      },
      {
        title: '规则卡片',
        key: 'rule_cards_count',
        width: 100,
        render: (row) => {
          if (!row.rule_cards_count) return '-'
          return h(
            NSpace,
            { size: 4 },
            {
              default: () => [
                h(NText, {}, { default: () => `${row.available_rule_cards_count || 0}/${row.rule_cards_count}` }),
                h(
                  NTag,
                  { 
                    type: (row.available_rule_cards_count || 0) > 0 ? 'success' : 'default',
                    size: 'small'
                  },
                  { default: () => '可用' }
                )
              ]
            }
          )
        }
      },
      {
        title: '奖金池',
        key: 'ads_pool_amount',
        width: 90,
        render: (row) => `¥${row.ads_pool_amount}`
      },
      {
        title: '状态',
        key: 'status',
        width: 80,
        render: (row) => h(
          NTag,
          { type: getStatusType(row.status) },
          { default: () => getStatusLabel(row.status) }
        )
      },
      {
        title: '创建时间',
        key: 'created_at',
        width: 155,
        render: (row) => formatDate(row.created_at)
      },
      {
        title: '操作',
        key: 'actions',
        width: 270,
        fixed: 'right',
        render: (row) => h(
          NSpace,
          { wrap: false, size: 8 },
          {
            default: () => [
              h(
                NButton,
                {
                  size: 'small',
                  onClick: () => viewTask(row)
                },
                { default: () => '详情' }
              ),
              h(
                NButton,
                {
                  size: 'small',
                  type: 'primary',
                  onClick: () => editTask(row)
                },
                { default: () => '编辑任务' }
              ),
              h(
                NButton,
                {
                  size: 'small',
                  type: 'error',
                  onClick: () => deleteTask(row)
                },
                { default: () => '删除' }
              )
            ]
          }
        )
      }
    ]
    
    const openParticipateModal = (task: AdvertisementTask) => {
      // Navigate to participation page instead of opening modal
      const routeData: any = {
        name: 'advertisement-task-participation',
        params: { id: task.id }
      }
      
      // If a rule card was selected, pass it as query parameter
      if (selectedRuleCard.value) {
        routeData.query = {
          rule_card_id: selectedRuleCard.value.id,
          rule_card_name: selectedRuleCard.value.rule_name || '规则卡片'
        }
        message.info(`将使用规则卡片: ${selectedRuleCard.value.rule_name || '规则卡片'}`)
      }
      
      router.push(routeData)
    }
    
    const handleParticipate = async () => {
      if (!participateFormData.value.workflow_id) {
        message.error('请选择工作流')
        return
      }
      
      if (!participatingTask.value) return
      
      participateLoading.value = true
      try {
        const response = await axios.post('http://localhost:5001/api/advertisement-tasks/participate', {
          task_ids: [participatingTask.value.id],
          workflow_id: participateFormData.value.workflow_id,
          include_rule_image: participateFormData.value.include_rule_image
        })
        
        if (response.data.success) {
          message.success('参与成功！')
          showParticipateModal.value = false
          loadTasks()
        } else {
          message.error(response.data.message || '参与失败')
        }
      } catch (error) {
        message.error('参与失败: ' + (error as Error).message)
      } finally {
        participateLoading.value = false
      }
    }
    
    const closeParticipateModal = () => {
      showParticipateModal.value = false
      participatingTask.value = null
      participateFormData.value = {
        workflow_id: null,
        include_rule_image: false
      }
    }
    
    const handleSubmit = async () => {
      submitting.value = true
      try {
        const data = {
          ...formData.value,
          deadline: formData.value.deadline ? new Date(formData.value.deadline).toISOString() : null
        }
        
        let response
        if (editingTask.value) {
          response = await axios.put(
            `http://localhost:5001/api/advertisement-tasks/${editingTask.value.id}`,
            data
          )
        } else {
          response = await axios.post('http://localhost:5001/api/advertisement-tasks/', data)
        }
        
        if (response.data.success) {
          message.success(editingTask.value ? '更新成功' : '创建成功')
          closeModal()
          loadTasks()
          loadStats()
        } else {
          message.error(response.data.message || '操作失败')
        }
      } catch (error) {
        message.error('操作失败: ' + (error as Error).message)
      } finally {
        submitting.value = false
      }
    }
    
    const closeModal = () => {
      showCreateModal.value = false
      editingTask.value = null
      formData.value = {
        task_id: '',
        task_title: '',
        card_title: '',
        submission_rules: '',
        tag_require: '',
        settlement_way: '',
        hashtags: [],
        image_url: '',
        ads_pool_amount: 0,
        status: 'active',
        deadline: null
      }
    }
    
    onMounted(() => {
      loadTasks()
      loadStats()
      
      // Listen for visibility changes to reload stats when page becomes visible
      document.addEventListener('visibilitychange', handleVisibilityChange)
    })
    
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        // Page became visible, reload stats
        loadStats()
      }
    }
    
    onUnmounted(() => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    })
    
    
    return {
      tasks,
      loading,
      submitting,
      showCreateModal,
      showDetailModal,
      showParticipateModal,
      editingTask,
      viewingTask,
      participatingTask,
      filterStatus,
      stats,
      pagination,
      formData,
      participateFormData,
      workflows,
      participateLoading,
      formRules,
      statusOptions,
      columns,
      getStatusType,
      getStatusLabel,
      formatDate,
      loadTasks,
      handlePageChange,
      handlePageSizeChange,
      viewTask,
      editTask,
      deleteTask,
      markRuleCardParticipated,
      selectRuleCard,
      selectedRuleCard,
      openParticipateModal,
      handleParticipate,
      closeParticipateModal,
      handleSubmit,
      closeModal
    }
  }
})
</script>

<style scoped>
.advertisement-tasks-container {
  padding: 24px;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-section h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-section {
  margin-bottom: 20px;
}

.stat-card {
  min-width: 150px;
}

.stat-card.active {
  border-left: 4px solid #18a058;
}

.stat-card.completed {
  border-left: 4px solid #2080f0;
}

.stat-card.expired {
  border-left: 4px solid #f0a020;
}

.filter-section {
  margin-bottom: 16px;
}

/* Rule Cards Styling */
.rule-cards-expand {
  padding: 16px 24px;
  background: #fafafa;
}

.rule-card-item {
  background: white;
  transition: all 0.3s ease;
}

.rule-card-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.rule-card-info {
  flex: 1;
  min-width: 0;
}

.empty-state {
  padding: 24px;
  text-align: center;
}
</style>
