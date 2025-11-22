<template>
  <div class="publish-page">
    <div class="page-header">
      <n-radio-group v-model:value="activeTab" name="publish-tabs" class="tab-buttons">
        <n-radio-button value="publish">发布笔记</n-radio-button>
        <n-radio-button value="history">发布历史</n-radio-button>
      </n-radio-group>
    </div>
    
    <div v-if="activeTab === 'publish'" class="tab-content">
        <n-card size="small">
      <n-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-placement="left"
        label-width="auto"
        require-mark-placement="right-hanging"
        size="large"
      >
        <n-form-item label="发布账号" path="userId">
          <n-select
            v-model:value="formData.userId"
            :options="userOptions"
            placeholder="请选择发布账号"
            clearable
            @update:value="handleUserChange"
          />
        </n-form-item>

        <n-form-item label="标题" path="title">
          <n-input
            v-model:value="formData.title"
            placeholder="请输入笔记标题"
            clearable
          />
        </n-form-item>

        <n-form-item label="描述">
          <n-input
            v-model:value="formData.description"
            type="textarea"
            placeholder="请输入笔记描述内容"
            :autosize="{ minRows: 3, maxRows: 6 }"
          />
        </n-form-item>

        <n-form-item label="话题标签" path="topics">
          <n-select
            v-model:value="selectedTopics"
            multiple
            filterable
            tag
            :options="topicOptions"
            placeholder="搜索或输入话题标签"
            :max-tag-count="5"
            @update:value="handleTopicsChange"
          />
          <template #feedback>
            最多可选择10个话题标签
          </template>
        </n-form-item>

        <n-form-item label="图片" path="images">
          <n-upload
            v-model:file-list="uploadFiles"
            :custom-request="customUpload"
            :max="9"
            accept="image/*"
            @change="handleUploadChange"
            @preview="handlePreview"
            list-type="image-card"
            multiple
            directory-dnd
          >
          </n-upload>
        </n-form-item>

        <n-form-item label="是否私密笔记">
          <n-space size="large">
            <n-switch 
              v-model:value="formData.is_private"
              size="medium"
              :round="false"
            >
              <template #checked>私密</template>
              <template #unchecked>公开</template>
            </n-switch>
          </n-space>
        </n-form-item>
      </n-form>
      <n-space justify="space-around" size="large">
        <n-button
          type="primary"
          size="medium"
          :loading="isPublishing"
          :disabled="isPublishing"
          @click="handlePublish"
          style="min-width: 120px;"
        >
          {{ isPublishing ? '发布中...' : '发布笔记' }}
        </n-button>
      </n-space>
    </n-card>
        <n-modal
          v-model:show="showPreview"
          preset="card"
          style="width: 800px"
          title="图片预览"
        >
          <img :src="previewImageUrl" style="width: 100%">
        </n-modal>
    </div>
    
    <div v-else-if="activeTab === 'history'" class="tab-content">
      <n-data-table
        :columns="noteColumns"
        :data="publishedNotes"
        :pagination="notePagination"
        :loading="loadingNotes"
        @update:page="handleNotesPageChange"
      />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, h } from 'vue'
import { publishNote, uploadImage, listActiveUsers, listNotes } from '../api/functions'
import type { ApiResponse, UploadImageResponse, ActiveUser, Note, ListNotesResponse } from '../api/config'
import { NTag, NButton, NSpace, type DataTableColumns } from 'naive-ui'
import type { UploadFileInfo } from 'naive-ui'
import { useMessage } from 'naive-ui'
import type { FormInst } from 'naive-ui'

// 热门话题示例数据
const HOT_TOPICS = [
  '头像分享', '可爱头像', '原创头像', '头像壁纸', '头像设计', '头像定制', '头像制作', '头像设计', '头像定制', '头像制作'
].map(topic => ({ label: `#${topic}`, value: topic }))

export default defineComponent({
  setup() {
    const activeTab = ref('publish')
    const formRef = ref<FormInst | null>(null)
    const uploadFiles = ref([])
    const isPublishing = ref(false)
    const selectedTopics = ref<string[]>([])
    const message = useMessage()
    const userOptions = ref<{ label: string; value: number }[]>([])
    
    // Published notes state
    const publishedNotes = ref<Note[]>([])
    const loadingNotes = ref(false)
    const notePagination = ref({
      page: 1,
      pageSize: 10,
      showSizePicker: true,
      pageSizes: [10, 20, 50],
      itemCount: 0,
      prefix: ({ itemCount }: any) => `总共 ${itemCount} 条记录`
    })
    
    const formData = ref({
      userId: undefined as number | undefined,
      title: '',
      description: '',
      is_private: true,
      images: [] as string[],
      topics: [] as string[]
    })

    const rules = {
      userId: {
        required: true,
        message: '请选择发布账号',
        trigger: 'change',
        type: 'number'
      },
      title: {
        required: true,
        message: '请输入笔记标题',
        trigger: ['blur', 'input']
      },
      images: {
        validator: (rule: any, value: string[]) => {
          return formData.value.images.length > 0
        },
        message: '请至少上传一张图片',
        trigger: ['change']
      }
    }

    const topicOptions = ref(HOT_TOPICS)

    const showPreview = ref(false)
    const previewImageUrl = ref('')

    onMounted(() => {
      // 获取活跃用户列表
      listActiveUsers().then((res: any) => {
        const response = res as ApiResponse<ActiveUser[]>
        if (response.success && response.data) {
          userOptions.value = response.data.map(user => ({
            label: user.nickname || user.username,
            value: user.id
          }))
        } else {
          message.error('获取用户列表失败')
        }
      })

      // 检查是否有保存的标题
      const savedTitle = localStorage.getItem('xhs_Title')
      if (savedTitle) {
        formData.value.title = JSON.parse(savedTitle)
        localStorage.removeItem('xhs_Title')
      }

      // 检查是否有保存的文案
      const savedCaption = localStorage.getItem('xhs_Caption')
      if (savedCaption) {
        formData.value.description = JSON.parse(savedCaption)
        localStorage.removeItem('xhs_Caption')
      }

      // 检查是否有保存的话题
      const savedTopics = localStorage.getItem('xhs_Topics')
      if (savedTopics) {
        selectedTopics.value = JSON.parse(savedTopics)
        localStorage.removeItem('xhs_Topics')
      }

      // 检查是否有选中的图片
      const selectedImages = localStorage.getItem('selectedImages')
      if (selectedImages) {
        const imageUrls = JSON.parse(selectedImages)
        formData.value.images = imageUrls
        uploadFiles.value = imageUrls.map((url: string) => ({
          id: url,
          name: url.split('/').pop(),
          status: 'finished',
          url
        }))
        localStorage.removeItem('selectedImages')
      }
    })

    const handleTopicsChange = (values: string[]) => {
      if (values.length > 10) {
        selectedTopics.value = values.slice(0, 10)
        message.warning('最多只能选择10个话题')
        return
      }
      
      // 只更新话题，不改描述内容
      selectedTopics.value = values
    }

    const handlePreview = (file: UploadFileInfo) => {
      previewImageUrl.value = file.url || ''
      showPreview.value = true
    }

    const customUpload = async ({ file, onFinish, onError }: any) => {
      try {
        const uploadImageData = new FormData()
        uploadImageData.append('file', file.file)

        const response = await uploadImage(uploadImageData) as ApiResponse<UploadImageResponse>
        
        if (response.success && response.data) {
          // 更新文件状态和URL
          file.status = 'finished'
          file.url = response.data.path
          
          // 更新表单数据中的图片路径
          const currentFiles = uploadFiles.value
            .filter((f: any) => f.status === 'finished' && f.url)
            .map((f: any) => f.url)
          formData.value.images = currentFiles

          onFinish()
        } else {
          throw new Error(response.message || '上传失败')
        }
      } catch (error: any) {
        file.status = 'error'
        onError()
        message.error(error.message || '上传失败')
      }
    }

    const handleUploadChange = ({ fileList }: any) => {
      uploadFiles.value = fileList
      // 更新表单数据中的图片路径，确保只包含已完成上传的图片
      const finishedFiles = fileList
        .filter((file: any) => file.status === 'finished' && file.url)
        .map((file: any) => file.url)
      formData.value.images = finishedFiles
    }

    const handlePublish = async () => {
      try {
        if (!formRef.value) return

        // 先验证是否选择了账号
        if (!formData.value.userId) {
          message.error('请选择发布账号')
          return
        }

        await formRef.value.validate()
        isPublishing.value = true

        // 修改发布数据的构造方式，只传递userId
        const publishData = {
          userId: formData.value.userId,
          title: formData.value.title,
          description: formData.value.description,
          images: formData.value.images,
          topics: selectedTopics.value,
          is_private: formData.value.is_private
        }

        const publishResponse = await publishNote(publishData) as ApiResponse
        if (publishResponse.success) {
          message.success('笔记发布成功！')
          // 重置表单
          formRef.value?.restoreValidation()
          formData.value = {
            userId: undefined,
            title: '',
            description: '',
            is_private: true,
            images: [],
            topics: []
          }
          uploadFiles.value = []
          selectedTopics.value = []
        } else {
          throw new Error(publishResponse.message || '发布失败')
        }
      } catch (error: any) {
        console.error(error)
        message.error(error?.message || '发布失败')
      } finally {
        isPublishing.value = false
      }
    }

    const handleUserChange = (value: number | null) => {
      if (value) {
        // 清除可能存在的验证错误
        formRef.value?.restoreValidation()
      }
    }
    
    // Published notes functions
    const fetchPublishedNotes = async (page: number = 1) => {
      loadingNotes.value = true
      try {
        const response = await listNotes({ page, per_page: notePagination.value.pageSize }) as ApiResponse<ListNotesResponse>
        if (response.success && response.data) {
          publishedNotes.value = response.data.notes
          notePagination.value.itemCount = response.data.total
          notePagination.value.page = response.data.page
        }
      } catch (error: any) {
        message.error('获取发布历史失败')
      } finally {
        loadingNotes.value = false
      }
    }
    
    const handleNotesPageChange = (page: number) => {
      fetchPublishedNotes(page)
    }
    
    const noteColumns: DataTableColumns<Note> = [
      {
        title: 'ID',
        key: 'id',
        width: 60
      },
      {
        title: '标题',
        key: 'title',
        ellipsis: {
          tooltip: true
        },
        width: 200
      },
      {
        title: '描述',
        key: 'description',
        ellipsis: {
          tooltip: true
        },
        width: 300,
        render: (row: Note) => {
          return row.description.substring(0, 100) + (row.description.length > 100 ? '...' : '')
        }
      },
      {
        title: '话题',
        key: 'topics',
        width: 150,
        render: (row: Note) => {
          return h(
            NSpace,
            { size: 'small' },
            {
              default: () => row.topics.slice(0, 3).map(topic => 
                h(NTag, { size: 'small', type: 'info' }, { default: () => topic })
              )
            }
          )
        }
      },
      {
        title: '状态',
        key: 'status',
        width: 100,
        render: (row: Note) => {
          const statusMap = {
            'published': { type: 'success' as const, text: '已发布' },
            'publishing': { type: 'warning' as const, text: '发布中' },
            'failed': { type: 'error' as const, text: '失败' }
          }
          const status = statusMap[row.status] || { type: 'default' as const, text: row.status }
          return h(NTag, { type: status.type }, { default: () => status.text })
        }
      },
      {
        title: '发布时间',
        key: 'published_at',
        width: 180,
        render: (row: Note) => {
          return row.published_at ? new Date(row.published_at).toLocaleString('zh-CN') : '-'
        }
      },
      {
        title: '操作',
        key: 'actions',
        width: 100,
        render: (row: Note) => {
          return h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              text: true,
              onClick: () => {
                if (row.note_id && row.xhs_response) {
                  window.open(`https://www.xiaohongshu.com/explore/${row.note_id}`, '_blank')
                } else {
                  message.warning('笔记未成功发布')
                }
              }
            },
            { default: () => '查看' }
          )
        }
      }
    ]
    
    // Fetch notes on mount
    onMounted(() => {
      fetchPublishedNotes()
    })

    return {
      activeTab,
      formRef,
      formData,
      rules,
      uploadFiles,
      isPublishing,
      selectedTopics,
      topicOptions,
      userOptions,
      handleTopicsChange,
      customUpload,
      handleUploadChange,
      handlePublish,
      showPreview,
      previewImageUrl,
      handlePreview,
      handleUserChange,
      publishedNotes,
      loadingNotes,
      notePagination,
      noteColumns,
      handleNotesPageChange
    }
  }
})
</script>

<style scoped>
.publish-page {
  width: 100%;
  padding: 24px;
}

/* Header with tab buttons - matches advertisement tab style */
.page-header {
  margin-bottom: 24px;
  display: flex;
  align-items: center;
}

/* Remove card padding and borders to match advertisement tasks layout */
.tab-content :deep(.n-card) {
  border: none !important;
  box-shadow: none !important;
}

.tab-content :deep(.n-card__content) {
  padding: 0 !important;
}

/* Add vertical spacing to form for readability */
.tab-content :deep(.n-form) {
  padding: 16px 0;
}

/* :deep(.n-card) {
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
} */

:deep(.n-card-header) {
  text-align: center;
  font-size: 1.5em;
  font-weight: 600;
  padding: 24px 24px 0;
}

:deep(.n-form) {
  padding: 12px;
}

:deep(.n-form-item) {
  margin-bottom: 24px;
}

:deep(.n-form-item-label) {
  font-weight: 500;
  font-size: 0.95em;
  color: #333;
}

:deep(.n-input) {
  border-radius: 8px;
}

:deep(.n-input-wrapper) {
  transition: all 0.3s ease;
}

:deep(.n-input-wrapper:hover) {
  transform: translateY(-1px);
}

:deep(.n-upload) {
  margin-top: 8px;
}

:deep(.n-upload-trigger) {
  width: 112px;
  height: 112px;
  border-radius: 12px;
  border: 2px dashed #e5e5e5;
  transition: all 0.3s ease;
}

:deep(.n-upload-trigger:hover) {
  border-color: var(--n-primary-color);
  transform: translateY(-2px);
}

:deep(.n-upload-file-list) {
  display: grid;
  grid-template-columns: repeat(auto-fill, 112px);
  gap: 16px;
  margin-top: 16px;
}

:deep(.n-upload-file--image-card) {
  width: 112px;
  height: 112px;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
}

:deep(.n-upload-file--image-card:hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

:deep(.n-button) {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

:deep(.n-button:not(.n-button--disabled):hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

:deep(.n-switch) {
  transition: all 0.3s ease;
}

:deep(.n-switch:hover) {
  transform: translateY(-1px);
}

:deep(.n-modal-mask) {
  backdrop-filter: blur(8px);
}

:deep(.n-modal-wrapper .n-card) {
  border-radius: 16px;
  overflow: hidden;
}

/* 添加响应式布局 */
@media (max-width: 600px) {
  .publish-page {
    padding: 0 12px;
  }
  
  :deep(.n-form-item-label) {
    margin-bottom: 8px;
  }
  
  :deep(.n-upload-file-list) {
    gap: 12px;
  }
}
</style> 