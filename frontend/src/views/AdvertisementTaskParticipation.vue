<template>
  <div class="advertisement-task-participation">
    <div class="header">
      <n-button type="primary" @click="goBack" class="back-button">
        <template #icon>
          <n-icon><arrow-back /></n-icon>
        </template>
        返回
      </n-button>
      <h1>参与广告任务</h1>
    </div>

    <div class="content" v-if="loading">
      <n-spin size="large" />
      <p>加载中...</p>
    </div>

    <div class="content" v-else-if="error">
      <n-result
        status="error"
        title="加载失败"
        :description="error"
      >
        <template #footer>
          <n-button @click="loadTask">重试</n-button>
        </template>
      </n-result>
    </div>

    <div class="content" v-else-if="task">
      <!-- Task Information Card -->
      <n-card :title="task.task_title" class="task-card">
        <template #header-extra>
          <n-tag :type="task.task_type === 'community_special' ? 'warning' : 'default'">
            {{ task.task_type === 'community_special' ? '社群特别任务' : '普通任务' }}
          </n-tag>
        </template>

        <n-descriptions label-placement="left" :column="1" bordered>
          <n-descriptions-item label="任务ID">{{ task.task_id }}</n-descriptions-item>
          <n-descriptions-item label="卡片标题">{{ task.card_title }}</n-descriptions-item>
          
          <!-- Show hashtags if available -->
          <n-descriptions-item label="话题标签" v-if="task.hashtags && task.hashtags.length > 0">
            <n-space wrap :size="8">
              <n-tag 
                v-for="(tag, index) in task.hashtags" 
                :key="index" 
                type="info"
                size="small"
              >
                {{ tag.startsWith('#') ? tag : '#' + tag }}
              </n-tag>
            </n-space>
          </n-descriptions-item>

          <!-- Show image if available -->
          <n-descriptions-item label="任务图片" v-if="task.image">
            <img 
              :src="'http://localhost:5001' + task.image.url" 
              alt="任务图片" 
              style="max-width: 100%; max-height: 300px; border-radius: 4px;" 
            />
          </n-descriptions-item>

          <n-descriptions-item label="奖金池">¥{{ task.ads_pool_amount }}</n-descriptions-item>
          <n-descriptions-item label="状态">
            <n-tag :type="getStatusType(task.status)">
              {{ getStatusLabel(task.status) }}
            </n-tag>
          </n-descriptions-item>
        </n-descriptions>

        <n-divider />

        <!-- Participation Form -->
        <n-form ref="formRef" :model="formData">
          <n-alert type="info" style="margin-bottom: 16px;">
            <template #header>
              系统将根据任务信息生成文本提示词
            </template>
            系统会自动使用任务标题、标签和规则生成提示词并执行参与流程
          </n-alert>

          <n-form-item label="包含任务图片">
            <n-space vertical>
              <n-switch v-model:value="formData.include_rule_image">
                <template #checked>启用</template>
                <template #unchecked>禁用</template>
              </n-switch>
              <n-text depth="3" style="font-size: 12px;">
                {{formData.include_rule_image ? '✅ 将任务图片作为规则图传入工作流' : '默认禁用 - 仅使用文本提示词'}}
                {{ !task.image_path && formData.include_rule_image ? '（当前任务无图片）' : '' }}
              </n-text>
            </n-space>
          </n-form-item>

          <n-divider>提示词预览</n-divider>

          <n-card size="small" style="background: #f5f5f5; margin-bottom: 16px;">
            <div style="white-space: pre-wrap; font-size: 13px; font-family: monospace;">任务: {{ task.task_title }}

<span v-if="task.hashtags && task.hashtags.length > 0">话题标签: {{ task.hashtags.join(' ') }}

</span><span v-if="task.tag_require">话题要求: {{ task.tag_require }}

</span><span v-if="task.submission_rules">投稿规则: {{ task.submission_rules }}</span></div>
          </n-card>

          <div class="form-actions">
            <n-button type="primary" @click="handleSubmit" :loading="submitting" size="large">
              {{ submitting ? '处理中...' : '开始参与' }}
            </n-button>
            <n-button @click="goBack" :disabled="submitting" size="large">取消</n-button>
          </div>
        </n-form>
      </n-card>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowBack } from '@vicons/ionicons5'
import { useMessage } from 'naive-ui'
import axios from 'axios'

interface AdvertisementTask {
  id: number
  task_id: string
  task_title: string
  card_title: string
  submission_rules: string
  tag_require: string
  hashtags?: string[]
  image_path?: string
  image?: {
    path?: string
    url: string
    external?: boolean
  }
  ads_pool_amount: number
  status: string
  task_type: string
}

export default defineComponent({
  name: 'AdvertisementTaskParticipation',
  components: {
    ArrowBack
  },
  props: {
    id: {
      type: [String, Number],
      required: true
    }
  },
  setup(props) {
    const router = useRouter()
    const message = useMessage()

    const task = ref<AdvertisementTask | null>(null)
    const loading = ref(true)
    const submitting = ref(false)
    const error = ref<string | null>(null)

    const formData = ref({
      include_rule_image: false
    })

    const getStatusType = (status: string) => {
      const statusMap: Record<string, any> = {
        active: 'success',
        completed: 'info',
        expired: 'warning',
        draft: 'default'
      }
      return statusMap[status] || 'default'
    }

    const getStatusLabel = (status: string) => {
      const labelMap: Record<string, string> = {
        active: '进行中',
        completed: '已完成',
        expired: '已过期',
        draft: '草稿'
      }
      return labelMap[status] || status
    }

    const loadTask = async () => {
      loading.value = true
      error.value = null

      try {
        const response = await axios.get(`http://localhost:5001/api/advertisement-tasks/${props.id}`)
        if (response.data.success) {
          task.value = response.data.data
        } else {
          error.value = response.data.message || '加载任务失败'
        }
      } catch (err) {
        error.value = '网络错误，请稍后重试'
        console.error('Failed to load task:', err)
      } finally {
        loading.value = false
      }
    }

    const handleSubmit = async () => {
      if (!task.value) {
        message.error('任务信息未加载')
        return
      }

      const requestData = {
        task_ids: [task.value.id],
        include_rule_image: formData.value.include_rule_image
      }

      console.log('Submitting participation request:', requestData)

      submitting.value = true
      try {
        const response = await axios.post('http://localhost:5001/api/advertisement-tasks/participate', requestData)

        console.log('Participation response:', response.data)

        if (response.data.success) {
          message.success('参与成功！')
          setTimeout(() => {
            router.push('/advertisement-tasks')
          }, 1000)
        } else {
          message.error(response.data.message || '参与失败')
        }
      } catch (err: any) {
        console.error('Participation error:', err)
        console.error('Error response:', err.response?.data)
        message.error('参与失败: ' + (err.response?.data?.message || err.message))
      } finally {
        submitting.value = false
      }
    }

    const goBack = () => {
      router.push('/advertisement-tasks')
    }

    onMounted(() => {
      loadTask()
    })

    return {
      task,
      loading,
      submitting,
      error,
      formData,
      getStatusType,
      getStatusLabel,
      loadTask,
      handleSubmit,
      goBack
    }
  }
})
</script>

<style scoped>
.advertisement-task-participation {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.back-button {
  flex-shrink: 0;
}

.content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.task-card {
  width: 100%;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.form-actions button {
  flex: 1;
}
</style>
