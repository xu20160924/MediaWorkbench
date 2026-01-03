<template>
  <div class="buyer-tasks">
    <n-space vertical :size="20">
      <!-- Header with stats -->
      <n-card title="买手任务" size="small">
        <template #header-extra>
          <n-button @click="loadTasks" :loading="loading">
            <template #icon>
              <n-icon><Refresh /></n-icon>
            </template>
            刷新
          </n-button>
        </template>
        
        <n-space>
          <n-statistic label="总任务数" :value="pagination.itemCount || 0" />
        </n-space>
      </n-card>

      <!-- Task List -->
      <n-spin :show="loading">
        <n-space vertical :size="16">
          <n-card
            v-for="task in tasks"
            :key="task.id"
            size="small"
            hoverable
            style="cursor: pointer;"
          >
            <div style="display: flex; gap: 16px;">
              <!-- Product Image -->
              <div style="flex-shrink: 0;">
                <n-image
                  v-if="task.main_image_url"
                  :src="task.main_image_url"
                  width="160"
                  height="160"
                  object-fit="cover"
                  preview
                  style="border-radius: 8px;"
                />
                <div v-else style="width: 160px; height: 160px; background: #f5f5f5; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #999;">
                  暂无图片
                </div>
              </div>

              <!-- Task Info -->
              <div style="flex: 1; display: flex; flex-direction: column; gap: 12px;">
                <!-- Title -->
                <n-text strong style="font-size: 16px;">{{ task.task_title }}</n-text>

                <!-- Stats Grid -->
                <n-grid cols="4" x-gap="12">
                  <n-grid-item>
                    <n-statistic label="商品价格" :value="`¥${task.item_price || '0'}`" />
                  </n-grid-item>
                  <n-grid-item>
                    <n-statistic label="预估收益" :value="`¥${task.item_income || '0'}`" />
                  </n-grid-item>
                  <n-grid-item>
                    <n-statistic label="佣金比例" :value="`${(task.rate / 100) || 0}%`" />
                  </n-grid-item>
                  <n-grid-item>
                    <n-statistic label="销量" :value="task.total_sales_volume || 0" />
                  </n-grid-item>
                </n-grid>

                <!-- Seller Info -->
                <div v-if="task.seller_name" style="display: flex; align-items: center; gap: 8px; padding: 8px; background: #f5f5f5; border-radius: 4px;">
                  <n-avatar
                    v-if="task.seller_image"
                    :src="task.seller_image"
                    size="small"
                    round
                  />
                  <div style="flex: 1;">
                    <n-text depth="3" style="font-size: 13px;">店铺：{{ task.seller_name }}</n-text>
                    <n-text v-if="task.seller_score" depth="3" style="font-size: 12px; margin-left: 8px;">
                      评分: {{ task.seller_score }}
                    </n-text>
                  </div>
                </div>

                <!-- Task Meta -->
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <n-space size="small">
                    <n-tag type="info" size="small">买手任务</n-tag>
                    <n-tag v-if="task.status === 'active'" type="success" size="small">进行中</n-tag>
                  </n-space>
                  <n-text depth="3" style="font-size: 12px;">
                    {{ formatDate(task.created_at) }}
                  </n-text>
                </div>
              </div>

              <!-- Actions -->
              <div style="flex-shrink: 0; display: flex; flex-direction: column; gap: 8px; justify-content: center;">
                <n-button
                  v-if="task.jump_url"
                  type="primary"
                  size="small"
                  @click.stop="openTaskUrl(task.jump_url)"
                >
                  查看商品
                </n-button>
                <n-button
                  size="small"
                  @click.stop="viewDetails(task)"
                >
                  详细信息
                </n-button>
                <n-button
                  type="error"
                  size="small"
                  @click.stop="deleteTask(task)"
                >
                  删除
                </n-button>
              </div>
            </div>
          </n-card>

          <!-- Empty State -->
          <n-empty
            v-if="!loading && tasks.length === 0"
            description="暂无买手任务"
            style="margin: 40px 0;"
          />
        </n-space>
      </n-spin>

      <!-- Pagination -->
      <div v-if="pagination.pageCount > 1" style="display: flex; justify-content: center; margin-top: 20px;">
        <n-pagination
          v-model:page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-count="pagination.pageCount"
          :item-count="pagination.itemCount"
          :page-sizes="pagination.pageSizes"
          show-size-picker
          :on-update:page="handlePageChange"
          :on-update:page-size="handlePageSizeChange"
        >
          <template #prefix="{ itemCount }">
            共 {{ itemCount }} 条
          </template>
        </n-pagination>
      </div>
    </n-space>

    <!-- Detail Modal -->
    <n-modal
      v-model:show="showDetailModal"
      preset="card"
      title="买手任务详情"
      style="width: 95vw; max-width: 1200px; max-height: 90vh; overflow: auto;"
      @after-enter="setupKeyboardShortcuts"
      @after-leave="removeKeyboardShortcuts"
    >
      <div v-if="viewingTask">
        <n-descriptions bordered :column="2" size="small">
          <n-descriptions-item label="任务标题" :span="2">{{ viewingTask.task_title }}</n-descriptions-item>
          <n-descriptions-item label="商品ID">{{ viewingTask.item_id }}</n-descriptions-item>
          <n-descriptions-item label="SKU ID">{{ viewingTask.sku_id }}</n-descriptions-item>
          <n-descriptions-item label="商品价格">¥{{ viewingTask.item_price }}</n-descriptions-item>
          <n-descriptions-item label="预估收益">¥{{ viewingTask.item_income }}</n-descriptions-item>
          <n-descriptions-item label="佣金比例">{{ (viewingTask.rate / 100) }}%</n-descriptions-item>
          <n-descriptions-item label="销量">{{ viewingTask.total_sales_volume }}</n-descriptions-item>
          <n-descriptions-item label="店铺名称">{{ viewingTask.seller_name }}</n-descriptions-item>
          <n-descriptions-item label="店铺评分">{{ viewingTask.seller_score }}</n-descriptions-item>
          <n-descriptions-item label="创建时间">{{ formatDate(viewingTask.created_at) }}</n-descriptions-item>
          <n-descriptions-item label="更新时间">{{ formatDate(viewingTask.updated_at) }}</n-descriptions-item>
          
          <n-descriptions-item label="商品图片" :span="2">
            <div v-if="viewingTask.small_images && viewingTask.small_images.length > 0">
              <!-- Large Image Preview in Center -->
              <div style="text-align: center; margin-bottom: 20px;">
                <n-image-group>
                  <n-image
                    :src="viewingTask.small_images[currentImageIndex]"
                    :width="600"
                    :height="600"
                    object-fit="contain"
                    show-toolbar-tooltip
                    :style="{
                      borderRadius: '12px',
                      boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
                      border: '1px solid #e0e0e6',
                      backgroundColor: '#fafafa'
                    }"
                  />
                </n-image-group>
              </div>
              
              <!-- Image Navigation -->
              <div v-if="viewingTask.small_images.length > 1" style="display: flex; justify-content: space-between; align-items: center; margin-top: 12px;">
                <n-button
                  :disabled="currentImageIndex === 0"
                  @click="previousImage"
                  secondary
                  size="small"
                >
                  <template #icon>
                    <n-icon><ChevronBack /></n-icon>
                  </template>
                  上一张
                </n-button>
                <n-text depth="3" style="font-size: 13px;">
                  {{ currentImageIndex + 1 }} / {{ viewingTask.small_images.length }}
                  <span style="margin-left: 8px; color: #999;">提示: 使用 ← → 方向键导航</span>
                </n-text>
                <n-button
                  :disabled="currentImageIndex === viewingTask.small_images.length - 1"
                  @click="nextImage"
                  secondary
                  size="small"
                >
                  下一张
                  <template #icon>
                    <n-icon><ChevronForward /></n-icon>
                  </template>
                </n-button>
              </div>
              
              <!-- Copy Image Buttons -->
              <n-space justify="center" style="margin-top: 12px;">
                <n-button
                  @click="autoCopyAllImages"
                  type="primary"
                  size="small"
                  :disabled="isAutoCopying"
                >
                  <template #icon>
                    <n-icon><Copy /></n-icon>
                  </template>
                  {{ isAutoCopying ? '正在复制...' : '逐张复制全部图片' }}
                </n-button>
                <n-button
                  @click="copyAllImagesAsCombined"
                  type="info"
                  size="small"
                  secondary
                  :disabled="isAutoCopying"
                >
                  <template #icon>
                    <n-icon><Copy /></n-icon>
                  </template>
                  复制全部(拼图)
                </n-button>
              </n-space>
              <n-text v-if="!isAutoCopying" depth="3" style="display: block; text-align: center; margin-top: 8px; font-size: 12px;">
                点击"逐张复制"后，每2秒自动复制下一张，请及时粘贴
              </n-text>
              <n-text v-else type="warning" style="display: block; text-align: center; margin-top: 8px; font-size: 12px;">
                ⏱️ 请立即粘贴！2秒后将复制下一张图片...
              </n-text>
              
              <!-- Enhanced Thumbnail Gallery -->
              <div style="margin-top: 20px;">
                <n-text depth="2" style="display: block; text-align: center; margin-bottom: 12px; font-size: 14px; font-weight: 500;">
                  点击缩略图切换查看 ({{ currentImageIndex + 1 }}/{{ viewingTask.small_images.length }})
                </n-text>
                <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; max-height: 200px; overflow-y: auto; padding: 8px;">
                  <div
                    v-for="(img, idx) in viewingTask.small_images"
                    :key="`thumb-${idx}`"
                    @click="currentImageIndex = idx"
                    :style="{
                      cursor: 'pointer',
                      border: idx === currentImageIndex ? '3px solid #18a058' : '2px solid #e0e0e6',
                      borderRadius: '8px',
                      padding: '4px',
                      opacity: idx === currentImageIndex ? 1 : 0.7,
                      transition: 'all 0.3s ease',
                      transform: idx === currentImageIndex ? 'scale(1.1)' : 'scale(1)',
                      backgroundColor: idx === currentImageIndex ? '#f0f9ff' : '#ffffff',
                      boxShadow: idx === currentImageIndex ? '0 4px 12px rgba(24,160,88,0.2)' : '0 2px 4px rgba(0,0,0,0.1)'
                    }"
                  >
                    <img
                      :src="img"
                      width="80"
                      height="80"
                      style="object-fit: cover; border-radius: 6px; display: block;"
                    />
                  </div>
                </div>
              </div>
            </div>
            <n-text v-else depth="3">暂无图片</n-text>
          </n-descriptions-item>
        </n-descriptions>
      </div>
    </n-modal>

  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import {
  NButton,
  NSpace,
  NCard,
  NStatistic,
  NImage,
  NImageGroup,
  NText,
  NTag,
  NGrid,
  NGridItem,
  NAvatar,
  NSpin,
  NPagination,
  NEmpty,
  NModal,
  NDescriptions,
  NDescriptionsItem,
  NIcon,
  useMessage,
  useDialog,
  NForm,
  NFormItem,
  NInput
} from 'naive-ui'
import { Refresh, ChevronBack, ChevronForward, Copy } from '@vicons/ionicons5'
import axios from 'axios'

interface BuyerTask {
  id: number
  item_id: string
  sku_id: string
  plan_id: string
  plan_type: number
  task_title: string
  item_price: string
  item_income: string
  rate: number
  total_sales_volume: number
  main_image_url: string
  small_images: string[]
  jump_url: string
  item_url: string
  seller_id: string
  seller_name: string
  seller_score: string
  seller_image: string
  status: string
  created_at: string
  updated_at: string
  task_type: string
}

const message = useMessage()
const dialog = useDialog()
const tasks = ref<BuyerTask[]>([])
const loading = ref(false)
const showDetailModal = ref(false)
const viewingTask = ref<BuyerTask | null>(null)
const isAutoCopying = ref(false)

const pagination = ref({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  pageCount: 1,
  pageSizes: [10, 20, 50, 100]
})

// Convert external image URL to proxied URL
const proxyImageUrl = (url: string): string => {
  if (!url) return url
  // Only proxy XHS image URLs
  if (url.includes('xiaohongshu.com') || url.includes('xhscdn.com')) {
    return `http://localhost:5001/api/proxy/image?url=${encodeURIComponent(url)}`
  }
  return url
}

// Transform task images to use proxy
const transformTaskImages = (task: BuyerTask): BuyerTask => {
  return {
    ...task,
    small_images: task.small_images?.map(proxyImageUrl) || []
  }
}

const loadTasks = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      per_page: pagination.value.pageSize
    }
    
    const response = await axios.get('http://localhost:5001/api/buyer-tasks/', { params })
    if (response.data.success) {
      // Transform images to use proxy
      tasks.value = response.data.data.tasks.map(transformTaskImages)
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

const handlePageChange = (page: number) => {
  pagination.value.page = page
  loadTasks()
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.value.pageSize = pageSize
  pagination.value.page = 1
  loadTasks()
}

const openTaskUrl = (url: string) => {
  // Open URL directly - browser will handle app protocol links
  window.open(url, '_blank')
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

// Image navigation within current task
const currentImageIndex = ref(0)

const previousImage = () => {
  if (currentImageIndex.value > 0) {
    currentImageIndex.value--
  }
}

const nextImage = () => {
  if (viewingTask.value && currentImageIndex.value < viewingTask.value.small_images.length - 1) {
    currentImageIndex.value++
  }
}

// Auto copy all images - preload then copy quickly
const autoCopyAllImages = async () => {
  if (!viewingTask.value || !viewingTask.value.small_images || viewingTask.value.small_images.length === 0) {
    message.error('没有可复制的图片')
    return
  }
  
  const imageUrls = viewingTask.value.small_images
  const totalImages = imageUrls.length
  isAutoCopying.value = true
  
  const loadingMsg = message.loading('正在预加载图片...', { duration: 0 })
  
  try {
    // Step 1: Fetch all images as blobs directly (avoids CORS canvas tainting)
    const pngBlobs: Blob[] = []
    for (let i = 0; i < imageUrls.length; i++) {
      const url = imageUrls[i]
      loadingMsg.destroy()
      const progressMsg = message.loading(`正在加载图片 ${i + 1}/${totalImages}...`, { duration: 0 })
      
      // Fetch image as blob
      const response = await fetch(url)
      if (!response.ok) throw new Error(`图片 ${i + 1} 加载失败`)
      const blob = await response.blob()
      
      // Convert to PNG if needed
      if (blob.type === 'image/png') {
        pngBlobs.push(blob)
      } else {
        // Convert to PNG via canvas
        const img = new Image()
        const objectUrl = URL.createObjectURL(blob)
        await new Promise<void>((resolve, reject) => {
          img.onload = () => resolve()
          img.onerror = () => reject(new Error('图片转换失败'))
          img.src = objectUrl
        })
        
        const canvas = document.createElement('canvas')
        canvas.width = img.width
        canvas.height = img.height
        const ctx = canvas.getContext('2d')
        ctx?.drawImage(img, 0, 0)
        URL.revokeObjectURL(objectUrl)
        
        const pngBlob = await new Promise<Blob>((resolve, reject) => {
          canvas.toBlob((b) => {
            if (b) resolve(b)
            else reject(new Error('转换PNG失败'))
          }, 'image/png')
        })
        pngBlobs.push(pngBlob)
      }
      progressMsg.destroy()
    }
    
    message.info(`已准备好 ${totalImages} 张图片，开始逐张复制...`, { duration: 1500 })
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // Step 3: Copy each blob - wait for focus if needed
    let copiedCount = 0
    for (let i = 0; i < pngBlobs.length; i++) {
      // Wait for document to be focused before copying
      while (!document.hasFocus()) {
        message.warning('请点击此窗口继续复制...', { duration: 1000 })
        await new Promise(resolve => setTimeout(resolve, 500))
      }
      
      try {
        await navigator.clipboard.write([
          new ClipboardItem({ 'image/png': pngBlobs[i] })
        ])
        copiedCount++
        message.info(`${i + 1}/${totalImages} 已复制，快速粘贴！`, { duration: 600 })
        // 600ms delay for pasting
        await new Promise(resolve => setTimeout(resolve, 600))
      } catch (copyErr) {
        // If copy fails due to focus, wait and retry
        if ((copyErr as Error).message.includes('not focused')) {
          message.warning('请点击此窗口，然后继续', { duration: 2000 })
          i-- // Retry this image
          await new Promise(resolve => setTimeout(resolve, 1000))
        } else {
          throw copyErr
        }
      }
    }
    
    message.success(`全部 ${copiedCount} 张图片复制完成！`)
  } catch (error) {
    console.error('Copy failed:', error)
    message.error('复制失败: ' + (error as Error).message)
  } finally {
    isAutoCopying.value = false
  }
}

// Copy all images to clipboard as a combined image
const copyAllImagesAsCombined = async () => {
  if (!viewingTask.value || !viewingTask.value.small_images || viewingTask.value.small_images.length === 0) {
    message.error('没有可复制的图片')
    return
  }
  
  const imageUrls = viewingTask.value.small_images
  const loadingMsg = message.loading(`正在加载 ${imageUrls.length} 张图片...`, { duration: 0 })
  
  try {
    // Load all images via fetch to avoid CORS issues
    const loadedImages: HTMLImageElement[] = []
    for (const url of imageUrls) {
      // Fetch as blob first
      const response = await fetch(url)
      if (!response.ok) throw new Error('图片加载失败')
      const blob = await response.blob()
      
      // Create image from blob
      const img = new Image()
      const objectUrl = URL.createObjectURL(blob)
      await new Promise<void>((resolve, reject) => {
        img.onload = () => {
          URL.revokeObjectURL(objectUrl)
          resolve()
        }
        img.onerror = () => {
          URL.revokeObjectURL(objectUrl)
          reject(new Error('图片加载失败'))
        }
        img.src = objectUrl
      })
      loadedImages.push(img)
    }
    
    // Calculate canvas size - arrange images in a grid
    const cols = Math.min(3, loadedImages.length) // Max 3 columns
    const rows = Math.ceil(loadedImages.length / cols)
    const padding = 10
    
    // Find max dimensions for uniform sizing
    const maxWidth = Math.max(...loadedImages.map(img => img.width))
    const maxHeight = Math.max(...loadedImages.map(img => img.height))
    
    // Scale down if images are too large (max 400px per image)
    const scale = Math.min(1, 400 / Math.max(maxWidth, maxHeight))
    const cellWidth = Math.round(maxWidth * scale)
    const cellHeight = Math.round(maxHeight * scale)
    
    const canvasWidth = cols * cellWidth + (cols + 1) * padding
    const canvasHeight = rows * cellHeight + (rows + 1) * padding
    
    // Create canvas and draw all images
    const canvas = document.createElement('canvas')
    canvas.width = canvasWidth
    canvas.height = canvasHeight
    const ctx = canvas.getContext('2d')
    
    if (!ctx) throw new Error('无法创建画布')
    
    // White background
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvasWidth, canvasHeight)
    
    // Draw each image
    loadedImages.forEach((img, idx) => {
      const col = idx % cols
      const row = Math.floor(idx / cols)
      const x = padding + col * (cellWidth + padding)
      const y = padding + row * (cellHeight + padding)
      
      // Center image in cell
      const imgScale = Math.min(cellWidth / img.width, cellHeight / img.height)
      const drawWidth = img.width * imgScale
      const drawHeight = img.height * imgScale
      const offsetX = (cellWidth - drawWidth) / 2
      const offsetY = (cellHeight - drawHeight) / 2
      
      ctx.drawImage(img, x + offsetX, y + offsetY, drawWidth, drawHeight)
    })
    
    // Convert to PNG blob
    const pngBlob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob((b) => {
        if (b) resolve(b)
        else reject(new Error('转换PNG失败'))
      }, 'image/png')
    })
    
    // Copy to clipboard
    await navigator.clipboard.write([
      new ClipboardItem({
        'image/png': pngBlob
      })
    ])
    
    loadingMsg.destroy()
    message.success(`已将 ${loadedImages.length} 张图片合并复制到剪贴板`)
  } catch (error) {
    loadingMsg.destroy()
    console.error('Copy failed:', error)
    message.error('复制失败: ' + (error as Error).message)
  }
}

// viewDetails function - reset image index when opening modal
const viewDetails = (task: BuyerTask) => {
  viewingTask.value = task
  currentImageIndex.value = 0  // Reset to first image
  showDetailModal.value = true
}

// Keyboard shortcuts for image navigation
const handleKeyPress = (e: KeyboardEvent) => {
  if (!showDetailModal.value) return
  
  if (e.key === 'ArrowLeft') {
    e.preventDefault()
    previousImage()
  } else if (e.key === 'ArrowRight') {
    e.preventDefault()
    nextImage()
  } else if (e.key === 'Escape') {
    showDetailModal.value = false
  }
}

const setupKeyboardShortcuts = () => {
  window.addEventListener('keydown', handleKeyPress)
}

const removeKeyboardShortcuts = () => {
  window.removeEventListener('keydown', handleKeyPress)
}

// Delete task function
const deleteTask = async (task: BuyerTask) => {
  const confirmed = await new Promise<boolean>((resolve) => {
    dialog.warning({
      title: '确认删除',
      content: `确定要删除任务"${task.task_title}"吗？此操作不可撤销。`,
      positiveText: '删除',
      negativeText: '取消',
      onPositiveClick: () => resolve(true),
      onNegativeClick: () => resolve(false)
    })
  })
  
  if (!confirmed) return
  
  try {
    const response = await fetch(`/api/buyer-tasks/${task.id}`, {
      method: 'DELETE'
    })
    
    const result = await response.json()
    
    if (result.success) {
      message.success(result.message || '删除成功')
      // Remove task from local list
      const index = tasks.value.findIndex(t => t.id === task.id)
      if (index > -1) {
        tasks.value.splice(index, 1)
        pagination.value.itemCount--
      }
    } else {
      message.error(result.error || '删除失败')
    }
  } catch (error) {
    message.error('删除失败: ' + (error as Error).message)
  }
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.buyer-tasks {
  padding: 20px;
}
</style>
