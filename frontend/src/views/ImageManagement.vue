<template>
  <div class="image-management">
    <!-- Preview Modal -->
    <n-modal 
      v-model:show="showPreview" 
      :mask-closable="true"
      :auto-focus="false"
      preset="card"
      :bordered="false"
      :closable="false"
      class="preview-modal"
      style="width: 100vw; height: 100vh; max-width: 100%; max-height: 100%; margin: 0;"
      :mask-style="{ backgroundColor: 'rgba(0, 0, 0, 0.85)' }"
      @after-leave="resetPreview"
    >
      <template #header>
        <div class="preview-header">
          <n-button 
            text
            class="close-button"
            @click="showPreview = false"
            aria-label="关闭预览"
          >
            <template #icon>
              <n-icon :component="Close" size="24" />
            </template>
          </n-button>
        </div>
      </template>
      <div class="preview-content" @click.self="showPreview = false">
        <div class="image-container">
          <template v-if="previewImageUrl">
            <div class="image-wrapper">
              <img 
                :src="previewImageUrl" 
                alt="图片预览" 
                class="preview-image" 
                :style="imageStyle"
                @click.stop
                @mousedown="startDrag"
                @mousemove="handleDrag"
                @mouseup="endDrag"
                @mouseleave="endDrag"
                @wheel.prevent="handleZoom"
              />
            </div>
          </template>
          <n-empty 
            v-else 
            description="预览不可用" 
            class="empty-preview"
          />
        </div>
        
        <!-- Image Controls -->
        <div class="preview-controls">
          <n-button-group>
            <n-tooltip>
              <template #trigger>
                <n-button @click="zoomOut" :disabled="zoomLevel <= 0.5">
                  <template #icon>
                    <n-icon><RemoveOutline /></n-icon>
                  </template>
                </n-button>
              </template>
              <span>缩小</span>
            </n-tooltip>
            <n-tooltip>
              <template #trigger>
                <n-button @click="resetZoom">
                  {{ Math.round(zoomLevel * 100) }}%
                </n-button>
              </template>
              <span>重置缩放</span>
            </n-tooltip>
            <n-tooltip>
              <template #trigger>
                <n-button @click="zoomIn" :disabled="zoomLevel >= 3">
                  <template #icon>
                    <n-icon><AddOutline /></n-icon>
                  </template>
                </n-button>
              </template>
              <span>放大</span>
            </n-tooltip>
          </n-button-group>
          
          <n-button-group>
            <n-tooltip>
              <template #trigger>
                <n-button @click="rotateLeft">
                  <template #icon>
                    <n-icon><RefreshOutline /></n-icon>
                  </template>
                </n-button>
              </template>
              <span>左旋转</span>
            </n-tooltip>
            <n-tooltip>
              <template #trigger>
                <n-button @click="rotateRight">
                  <template #icon>
                    <n-icon><RefreshOutline style="transform: scaleX(-1);" /></n-icon>
                  </template>
                </n-button>
              </template>
              <span>右旋转</span>
            </n-tooltip>
          </n-button-group>
          
          <n-tooltip>
            <template #trigger>
              <n-button type="primary" @click="downloadImage">
                <template #icon>
                  <n-icon><DownloadOutline /></n-icon>
                </template>
              </n-button>
            </template>
            <span>下载图片</span>
          </n-tooltip>
        </div>
      </div>
    </n-modal>

    <!-- Default Directory Modal -->
    <n-modal 
      v-model:show="showDefaultDirModal"
      preset="card"
      title="设置默认目录"
      :mask-closable="true"
      :bordered="false"
    >
      <div class="default-dir-form">
        <div class="form-row">
          <div class="form-label">普通图片</div>
          <n-input v-model:value="defaultLocations.general" placeholder="请输入本地目录路径" />
          <n-button size="small" ghost @click="selectCurrentFolder('general')">
            <template #icon>
              <n-icon><FolderOpenOutline /></n-icon>
            </template>
            请选择目录
          </n-button>
        </div>
        <div class="form-row">
          <div class="form-label">广告活动</div>
          <n-input v-model:value="defaultLocations.advertising_campaign" placeholder="请输入本地目录路径" />
          <n-button size="small" ghost @click="selectCurrentFolder('advertising_campaign')">
            <template #icon>
              <n-icon><FolderOpenOutline /></n-icon>
            </template>
            请选择目录
          </n-button>
        </div>
        <div class="form-row">
          <div class="form-label">广告规则</div>
          <n-input v-model:value="defaultLocations.advertising_rule" placeholder="请输入本地目录路径" />
          <n-button size="small" ghost @click="selectCurrentFolder('advertising_rule')">
            <template #icon>
              <n-icon><FolderOpenOutline /></n-icon>
            </template>
            请选择目录
          </n-button>
        </div>
        <div class="form-actions">
          <n-button type="primary" @click="saveDefaultLocations">保存并加载</n-button>
        </div>
      </div>
    </n-modal>

    <div class="content-wrapper">
      <div class="page-header">
        <div class="header-content">
          <div class="header-actions">
            <n-dropdown
              v-model:show="showUploadMenu"
              trigger="click"
              :options="uploadOptions"
              @select="handleUploadSelect"
            >
              <n-button type="primary" ghost>
                <template #icon>
                  <n-icon><CloudUploadOutline /></n-icon>
                </template>
                添加图片
                <n-icon><ChevronDown /></n-icon>
              </n-button>
            </n-dropdown>
            <div class="filter-group">
              <span class="filter-label">类型</span>
              <n-select
                v-model:value="imageTypeFilter"
                :options="imageTypeOptions"
                class="type-select"
                clearable
                placeholder="筛选图片类型"
              />
            </div>
            <n-button ghost class="default-dir" @click="showDefaultDirModal = true">
              <template #icon>
                <n-icon><FolderOpenOutline /></n-icon>
              </template>
              默认目录
            </n-button>
            <n-button type="error" ghost class="delete-all" @click="confirmDeleteAll">
              全部删除
            </n-button>
          </div>
          
          <h2 class="page-title">图片管理</h2>
          
          <div class="view-options">
            <n-radio-group v-model:value="viewMode" name="view-mode">
              <n-radio-button value="grid" :focusable="false">
                <template #icon>
                  <n-icon><GridOutline /></n-icon>
                </template>
                网格
              </n-radio-button>
              <n-radio-button value="list" :focusable="false">
                <template #icon>
                  <n-icon><ListOutline /></n-icon>
                </template>
                列表
              </n-radio-button>
            </n-radio-group>
          </div>
        </div>
      </div>

      <div v-if="viewMode === 'grid'" class="image-grid">
        <div v-for="(image, index) in images" :key="'grid-' + index" class="image-item">
          <div class="image-preview-container" @click="showImagePreview(image)">
            <img :src="getImageUrl(image)" :alt="image.name" class="image-preview" @error="handleImageError" />
            <div class="preview-overlay">
              <n-icon size="24"><SearchOutline /></n-icon>
              <span>预览</span>
            </div>
          </div>
          <div class="image-info">
            <div class="image-name">{{ image.name }}</div>
            <div class="image-meta">
              <span>{{ formatFileSize(image.size) }}</span>
              <span>{{ formatDate(image.created_at) }}</span>
            </div>
            <div class="image-actions">
              <n-button size="small" type="error" ghost @click="confirmDelete(image)">删除</n-button>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="list-view-container">
        <div class="content-wrapper">
          <!-- List Header -->
          <div class="list-header">
            <div class="header-item" style="width: 100px;">预览</div>
            <div class="header-item" style="flex: 2;">文件名</div>
            <div class="header-item" style="flex: 2;">工作流</div>
            <div class="header-item" style="flex: 1.5;">创建时间</div>
            <div class="header-item" style="width: 120px;">大小</div>
            <div class="header-item" style="width: 140px;">操作</div>
          </div>
          
          <!-- Empty State -->
          <n-empty v-if="images.length === 0" description="暂无图片" class="empty-state">
            <template #extra>
              <n-button size="small" @click="fetchImages">
                刷新
              </n-button>
            </template>
          </n-empty>
          
          <!-- List Content -->
          <n-list v-else class="image-list" hoverable>
            <!-- Image Items -->
            <n-list-item v-for="(image, index) in images" :key="'list-' + index" class="image-list-item">
              <n-thing>
                <div class="list-item-content">
                  <div class="list-item-row">
                    <div class="list-item-cell" style="width: 60px;">
                      <div class="list-image-container">
                        <img :src="getImageUrl(image)" class="list-image-preview" @error="handleImageError" />
                      </div>
                    </div>
                    <div class="list-item-cell" style="flex: 2;">
                      <div class="list-item-header">
                        <div class="image-name">{{ image.name }}</div>
                        <div class="image-tags">
                          <n-tag size="small" :type="image.source === 'upload' ? 'success' : 'info'" class="source-tag">
                            {{ image.source === 'upload' ? '上传' : '本地' }}
                          </n-tag>
                          <n-tag size="small" :type="image.image_type === 'advertising_campaign' ? 'warning' : 'default'" class="type-tag">
                            <template #icon>
                              <n-icon :component="getImageTypeIcon(image.image_type)" />
                            </template>
                            {{ getImageTypeLabel(image.image_type) }}
                          </n-tag>
                        </div>
                      </div>
                    </div>
                    
                    <div class="list-item-cell" style="flex: 2;">
                      <div class="detail-value">{{ image.workflow_name || '无' }}</div>
                    </div>
                    
                    <div class="list-item-cell" style="flex: 1.5;">
                      <div class="detail-value">{{ formatDate(image.created_at) }}</div>
                    </div>
                    
                    <div class="list-item-cell" style="width: 120px;">
                      <div class="detail-value">{{ formatFileSize(image.size) }}</div>
                    </div>
                    
                    <div class="list-item-cell" style="width: 80px;">
                      <div class="list-actions">
                        <n-tooltip trigger="hover">
                          <template #trigger>
                            <n-button text type="error" @click="confirmDelete(image)">
                              <template #icon>
                                <n-icon><TrashOutline /></n-icon>
                              </template>
                            </n-button>
                          </template>
                          <span>删除</span>
                        </n-tooltip>
                      </div>
                    </div>
                  </div>
                </div>
              </n-thing>
            </n-list-item>
          </n-list>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, computed, watch, h, Ref } from 'vue';

interface ImageItem {
  id?: string | number;
  name: string;
  url?: string;
  local_path?: string;
  size?: number;
  created_at?: string;
  image_type?: string;
  source?: string;
  workflow_name?: string;
}

interface Position {
  x: number;
  y: number;
}

type ViewMode = 'grid' | 'list';
import { 
  useMessage, 
  useDialog,
  NButton,
  NIcon,
  NImage,
  NModal,
  NDropdown,
  NButtonGroup,
  NTooltip,
  NEmpty,
  NList,
  NListItem,
  NThing,
  NRadioGroup,
  NRadioButton,
  NTag,
  NSelect
  ,
  NInput
} from 'naive-ui';
import { 
  CloudUploadOutline,
  FolderOpenOutline,
  GridOutline, 
  ListOutline, 
  TrashOutline, 
  EyeOutline,
  ChevronDown,
  ImagesOutline,
  MegaphoneOutline,
  DocumentTextOutline,
  CloseOutline,
  AddOutline,
  SearchOutline,
  RefreshOutline,
  RemoveOutline,
  DownloadOutline
} from '@vicons/ionicons5';
import api from '@/api';

export default defineComponent({
  name: 'ImageManagement',
  components: {
    NButton,
    NIcon,
    NImage,
    NModal,
    NDropdown,
    NButtonGroup,
    NTooltip,
    NEmpty,
    CloudUploadOutline,
    ChevronDown,
    FolderOpenOutline,
    GridOutline,
    ListOutline,
    TrashOutline,
    EyeOutline,
    ImagesOutline,
    MegaphoneOutline,
    DocumentTextOutline,
    Close: CloseOutline,
    AddOutline,
    SearchOutline,
    RefreshOutline,
    RemoveOutline,
    DownloadOutline
  },
  
  setup() {
    const message = useMessage();
    const dialog = useDialog();
    
    // State
    const viewMode = ref<ViewMode>('grid');
    const showPreview = ref(false);
    const showDefaultDirModal = ref(false);
    const showUploadMenu = ref(false);
    const previewImageUrl = ref('');
    const images = ref<ImageItem[]>([]);
    const loading = ref(false);
    const imageTypeFilter = ref('all');
    
    // Image type options for the dropdown
    const imageTypeOptions = [
      { label: '所有类型', value: 'all' },
      { label: '普通图片', value: 'general' },
      { label: '活动配图', value: 'advertising_campaign' },
      { label: '广告规则', value: 'advertising_rule' },
    ];
    
    // Image preview state
    const scale = ref(1);
    const rotate = ref(0);
    const position = ref<Position>({ x: 0, y: 0 });
    const isDragging = ref(false);
    const dragStart = ref({ x: 0, y: 0 });
    
    // Calculate zoom level for display
    const zoomLevel = computed(() => Math.round(scale.value * 100) + '%');
    
    // Image URL helper
    const getImageUrl = (image: any): string => {
      if (!image) {
        console.log('No image provided');
        return '';
      }
      
      // Debug log the image object
      console.log('Image object:', JSON.parse(JSON.stringify(image)));
      
      // If URL is directly provided, use it
      if (image.url) {
        console.log('Using direct URL:', image.url);
        return image.url;
      }
      
      // Handle different possible path properties
      const filePath = image.file_path || image.local_path || image.path || '';
      if (!filePath) {
        console.log('No valid path found in image object');
        return '';
      }
      
      const baseEnv = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');
      const devStaticBase = import.meta.env.DEV ? 'http://127.0.0.1:5002' : baseEnv;
      const p = String(filePath).replace(/\\/g, '/');
      // Map to backend static routes
      // Uploads: handle both 'upload/images/<filename>' and '/uploads/<filename>'
      const uploadMatch = p.match(/(?:^|\/)upload\/images\/(.+)$/) || p.match(/(?:^|\/)uploads\/(.+)$/);
      if (uploadMatch && uploadMatch[1]) {
        const url = `${devStaticBase}/images/uploads/${uploadMatch[1]}`;
        console.log('Generated upload URL:', url);
        return url;
      }
      // Outputs: handle both 'output/images/<filename>' and '/output/<filename>'
      const outputMatch = p.match(/(?:^|\/)output\/images\/(.+)$/) || p.match(/(?:^|\/)output\/(.+)$/);
      if (outputMatch && outputMatch[1]) {
        const url = `${devStaticBase}/images/output/${outputMatch[1]}`;
        console.log('Generated output URL:', url);
        return url;
      }
      // Fallback: direct http or base + path
      if (p.startsWith('http')) {
        console.log('Generated direct URL:', p);
        return p;
      }
      const normalized = p.startsWith('/') ? p.slice(1) : p;
      const url = `${baseEnv}/${normalized}`;
      console.log('Generated fallback URL:', url);
      return url;
    };
    
    // Format file size
    const formatFileSize = (bytes: number): string => {
      if (!bytes) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
    };
    
    // Format date
    const formatDate = (dateString: string): string => {
      if (!dateString) return '';
      return new Date(dateString).toLocaleString();
    };
    
    // Image preview handlers
    const showImagePreview = (image: any) => {
      if (!image) {
        console.error('No image provided for preview');
        return;
      }
      
      // Reset preview state
      scale.value = 1;
      rotate.value = 0;
      position.value = { x: 0, y: 0 };
      
      // Get the image URL and force refresh if needed
      let url = getImageUrl(image);
      if (!url) {
        console.error('Could not generate URL for image:', image);
        message.error('无法加载图片');
        return;
      }
      
      // Add timestamp to prevent caching issues
      const timestamp = new Date().getTime();
      const separator = url.includes('?') ? '&' : '?';
      previewImageUrl.value = `${url}${separator}t=${timestamp}`;
      
      console.log('Showing image preview:', previewImageUrl.value);
      showPreview.value = true;
      
      // Preload the image to check if it's valid
      const img = new Image();
      img.onload = () => {
        console.log('Image loaded successfully');
      };
      img.onerror = () => {
        console.error('Failed to load image:', url);
        message.error('图片加载失败');
        showPreview.value = false;
      };
      img.src = previewImageUrl.value;
    };
    
    
    // Download image
    const downloadImage = async () => {
      if (!previewImageUrl.value) return;
      
      try {
        const response = await fetch(previewImageUrl.value);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = previewImageUrl.value.split('/').pop() || 'image';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } catch (error) {
        console.error('下载失败:', error);
        message.error('下载失败');
      }
    };
    
    // Image error handler
    const handleImageError = (e: Event) => {
      const img = e.target as HTMLImageElement;
      img.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM2NjYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0ibHVjaWRlIGx1Y2lkZS1pbWFnZSI+PHJlY3Qgd2lkdGg9IjE4IiBoZWlnaHQ9IjE4IiB4PSIzIiB5PSIzIiByeD0iMiIgcnk9IjIiLz48Y2lyY2xlIGN4PSI4LjUiIGN5PSI4LjUiIHI9IjEuNSIvPjxwb2x5bGluZSBwb2ludHM9IjIxIDE1IDE2IDEwIDUgMjEiLz48L3N2Zz4=';
    };
    
    // Delete confirmation
    const confirmDelete = async (image: any) => {
      dialog.warning({
        title: '确认删除',
        content: '确定要删除这张图片吗？',
        positiveText: '删除',
        negativeText: '取消',
        onPositiveClick: async () => {
          try {
            // Remove the leading /api since it's already included in the baseURL
            await api.delete(`/images/delete/${image.id}`);
            message.success('删除成功');
            await fetchImages();
          } catch (error: any) {
            console.error('删除失败:', error);
            const errorMessage = error.response?.data?.message || '删除失败';
            message.error(errorMessage);
          }
        }
      });
    };

    const confirmDeleteAll = async () => {
      if (images.value.length === 0) {
        message.warning('没有可删除的图片');
        return;
      }

      dialog.warning({
        title: '确认删除所有图片',
        content: '此操作将删除全部图片记录，上传/生成的文件也会尝试删除。此操作不可撤销！',
        positiveText: '确认全部删除',
        negativeText: '取消',
        onPositiveClick: async () => {
          const loading = message.loading('正在删除所有图片...', { duration: 0 });
          try {
            // First try the batch delete endpoint
            try {
              const response = await api.delete('/images/clear-all');
              if (response.status === 200) {
                message.success('成功删除所有图片');
                images.value = []; // Clear the local images array immediately
                await fetchImages(); // Refresh the list
                return;
              }
            } catch (e) {
              console.warn('Batch delete failed, falling back to individual deletes');
            }

            // Fallback to individual deletes if batch delete fails
            const total = images.value.length;
            let successCount = 0;
            const errors: string[] = [];

            for (const img of [...images.value]) { // Create a copy of the array to avoid modification during iteration
              try {
                await api.delete(`/images/delete/${img.id}`);
                successCount++;
                // Update progress
                loading.content = `正在删除图片 (${successCount}/${total})...`;
              } catch (error: any) {
                console.error(`Failed to delete image ${img.id}:`, error);
                errors.push(`图片 ${img.id} 删除失败: ${error.response?.data?.message || '未知错误'}`);
              }
            }

            // Show results
            if (successCount > 0) {
              message.success(`成功删除 ${successCount} 张图片`);
            }
            if (errors.length > 0) {
              message.error(`${errors.length} 张图片删除失败，请检查控制台`);
              console.error('Failed to delete some images:', errors);
            }

            // Refresh the list
            await fetchImages();
          } catch (error) {
            console.error('Delete all failed:', error);
            message.error('删除失败: ' + (error.response?.data?.message || '未知错误'));
          } finally {
            loading.destroy();
          }
        }
      });
    };
    
    // Upload options
    const uploadOptions = [
      { 
        type: 'group',
        label: '上传单个图片',
        key: 'single',
        children: [
          { 
            label: '普通图片', 
            key: 'general',
            icon: () => h(ImagesOutline)
          },
          { 
            label: '广告图片', 
            key: 'advertising_campaign',
            icon: () => h(MegaphoneOutline)
          },
          { 
            label: '广告规则', 
            key: 'advertising_rule',
            icon: () => h(DocumentTextOutline)
          }
        ]
      },
      { 
        type: 'group',
        label: '上传图片目录',
        key: 'directory',
        children: [
          { 
            label: '普通图片目录', 
            key: 'dir_general',
            icon: () => h(FolderOpenOutline)
          },
          { 
            label: '广告图片目录', 
            key: 'dir_advertising_campaign',
            icon: () => h(FolderOpenOutline)
          },
          { 
            label: '广告规则目录', 
            key: 'dir_advertising_rule',
            icon: () => h(FolderOpenOutline)
          }
        ]
      }
    ];
    
    // Get icon for image type
    const getImageTypeIcon = (type: string) => {
      switch (type) {
        case 'advertising_campaign':
          return MegaphoneOutline;
        case 'advertising_rule':
          return DocumentTextOutline;
        default:
          return ImagesOutline;
      }
    };
    
    // Get label for image type
    const getImageTypeLabel = (type: string) => {
      const option = imageTypeOptions.find((opt: any) => opt.value === type);
      return option ? option.label : '未知类型';
    };
    
    // Get image style object
    const getImageStyle = () => {
      return {
        'transform': `scale(${scale.value}) rotate(${rotate.value}deg) translate(${position.value.x}px, ${position.value.y}px)`,
        'cursor': isDragging.value ? 'grabbing' : 'grab',
        'transition': isDragging.value ? 'none' : 'transform 0.2s ease',
        'max-width': '100%',
        'max-height': '100%',
        'user-select': 'none',
        'user-drag': 'none',
        '-webkit-user-drag': 'none',
        '-moz-user-select': 'none',
        '-webkit-user-select': 'none',
        '-ms-user-select': 'none'
      };
    };
    
    // Image style for preview
    const imageStyle = computed(getImageStyle);
    
    // Drag functions
    const startDrag = (e: MouseEvent) => {
      isDragging.value = true;
      dragStart.value = { x: e.clientX - position.value.x, y: e.clientY - position.value.y };
    };

    const handleDrag = (e: MouseEvent) => {
      if (!isDragging.value) return;
      position.value = {
        x: e.clientX - dragStart.value.x,
        y: e.clientY - dragStart.value.y
      };
    };

    const endDrag = () => {
      isDragging.value = false;
    };

    // Handle zoom with mouse wheel
    const handleZoom = (e: WheelEvent) => {
      e.preventDefault();
      const delta = e.deltaY > 0 ? -0.1 : 0.1;
      const newScale = Number(scale.value) + delta;
      scale.value = Math.min(Math.max(0.5, newScale), 3);
    };

    // Zoom controls
    const zoomIn = () => {
      scale.value = Math.min(Number(scale.value) + 0.1, 3);
    };

    const zoomOut = () => {
      scale.value = Math.max(Number(scale.value) - 0.1, 0.5);
    };

    const resetZoom = () => {
      scale.value = 1;
    };

    // Rotate controls
    const rotateLeft = () => {
      rotate.value = (rotate.value - 90) % 360;
    };

    const rotateRight = () => {
      rotate.value = (rotate.value + 90) % 360;
    };

    // Handle upload selection from dropdown
    const handleUploadSelect = (key: string) => {
      const isDirectory = key.startsWith('dir_');
      const imageType = isDirectory ? key.replace('dir_', '') : key;
      
      const input = document.createElement('input');
      input.type = 'file';
      input.multiple = isDirectory; // Allow multiple files for directory upload
      input.accept = 'image/*';
      
      // Enable directory upload for webkit browsers
      if (isDirectory && 'webkitdirectory' in input) {
        (input as any).webkitdirectory = true;
      }
      
      input.onchange = (e: Event) => {
        const target = e.target as HTMLInputElement;
        if (target.files && target.files.length > 0) {
          if (isDirectory) {
            handleDirectoryUpload(target.files, imageType);
          } else {
            handleFileUpload(target.files[0], imageType);
          }
        }
      };
      
      input.click();
    };
    
    const isValidImageFile = (file: File): boolean => {
      const name = (file?.name || '').toLowerCase();
      if (!name || name.startsWith('.')) return false;
      const ext = name.includes('.') ? name.split('.').pop() as string : '';
      return ['png', 'jpg', 'jpeg'].includes(ext);
    };
    
    // Handle single file upload
    const handleFileUpload = async (file: File, imageType: string) => {
      if (!isValidImageFile(file)) {
        message.warning('不支持的文件类型，已跳过');
        return;
      }
      const formData = new FormData();
      formData.append('file', file);
      formData.append('image_type', imageType);
      
      try {
        console.log('Uploading file:', file.name, 'type:', imageType, 'size:', file.size, 'bytes');
        
        // Log form data for debugging
        for (let [key, value] of formData.entries()) {
          console.log(key, value);
        }
        
        // Remove the /api prefix since it's already included in the base URL
        const response = await api.post('/images/upload', formData, {
          timeout: 30000,
          validateStatus: (status) => status < 500
        });
        
        console.log('Upload response:', response);
        
        // Handle different response formats
        if (!response) {
          throw new Error('No response from server');
        }
        
        // Check for error status
        if (response.status >= 400) {
          const errorData = response.data || {};
          throw new Error(
            errorData.message || 
            errorData.error || 
            `Server responded with status ${response.status}`
          );
        }
        
        // Check for success flag in response
        if (response.data && response.data.success === false) {
          throw new Error(response.data.message || '上传失败');
        }
        
        // If we have data in the response, add it to the images array
        if (response.data && response.data.data) {
          // Make sure the response data has the correct structure
          const newImage = response.data.data;
          if (newImage && !newImage.url && newImage.local_path) {
            // Ensure the URL is properly constructed
            newImage.url = `${import.meta.env.VITE_API_BASE_URL || ''}${newImage.local_path}`;
          }
          // Add the new image to the beginning of the array
          images.value = [newImage, ...images.value];
        }
        
        message.success('图片上传成功');
        await fetchImages();
      } catch (error: any) {
        console.error('Upload error details:', {
          name: error.name,
          message: error.message,
          response: error.response?.data,
          stack: error.stack
        });
        
        let errorMessage = '图片上传失败，请稍后重试';
        
        if (error.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          const { data, status } = error.response;
          errorMessage = data?.message || data?.error || `服务器错误 (${status})`;
        } else if (error.request) {
          // The request was made but no response was received
          errorMessage = '无法连接到服务器，请检查网络连接';
        } else if (error.code === 'ECONNABORTED') {
          errorMessage = '请求超时，请稍后重试';
        } else if (error.message) {
          errorMessage = error.message;
        }
        
        console.error('上传失败:', errorMessage);
        message.error(`上传失败: ${errorMessage}`);
      }
    };
    
    // Handle directory upload
    const handleDirectoryUpload = async (files: FileList, imageType: string) => {
      const allFiles = Array.from(files);
      const validFiles = allFiles.filter(isValidImageFile);
      const skippedCount = allFiles.length - validFiles.length;
      let successCount = 0;
      let failCount = 0;
      for (const file of validFiles) {
        try {
          await uploadFile(file, imageType);
          successCount += 1;
        } catch (e: any) {
          failCount += 1;
        }
      }
      await fetchImages();
      if (successCount > 0) {
        message.success(`已上传 ${successCount} 个文件`);
      }
      if (skippedCount > 0) {
        message.warning(`已跳过 ${skippedCount} 个非图片文件`);
      }
      if (failCount > 0) {
        message.error(`上传失败 ${failCount} 个文件`);
      }
    };
    
    // Helper function to upload a single file
    const uploadFile = async (file: File, imageType: string) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('image_type', imageType);
      
      const response = await api.post('/images/upload', formData, {
        timeout: 60000
      });
      
      if (response.data && response.data.success === false) {
        throw new Error(response.data.message || 'Upload failed');
      }
      
      return response.data;
    };

    // Fetch images from API
    const fetchImages = async () => {
      try {
        loading.value = true;
        const params: any = {};
        
        if (imageTypeFilter.value !== 'all') {
          params.image_type = imageTypeFilter.value;
        }
        
        let response = await api.get('/images', { params });
        const payload = response?.data || {};
        const items = Array.isArray(payload?.data)
          ? payload.data
          : Array.isArray(payload?.items)
            ? payload.items
            : Array.isArray(payload?.data?.items)
              ? payload.data.items
              : [];
        let normalized = items.map((img: any) => ({
          ...img,
          url: getImageUrl(img)
        }));
        if (imageTypeFilter.value !== 'all') {
          const wanted = imageTypeFilter.value;
          normalized = normalized.filter((it: any) => {
            const t = it?.image_type || 'general';
            return t === wanted;
          });
        }
        images.value = normalized;
      } catch (error: any) {
        try {
          const fallback = await api.get('/images');
          const payload = fallback?.data || {};
          const items = Array.isArray(payload?.data)
            ? payload.data
            : Array.isArray(payload?.items)
              ? payload.items
              : Array.isArray(payload?.data?.items)
                ? payload.data.items
                : [];
          let normalized = items.map((img: any) => ({
            ...img,
            url: getImageUrl(img)
          }));
          if (imageTypeFilter.value !== 'all') {
            const wanted = imageTypeFilter.value;
            normalized = normalized.filter((it: any) => (it?.image_type || 'general') === wanted);
          }
          images.value = normalized;
        } catch (e2: any) {
          console.error('Failed to fetch images:', error);
          const errorMessage = e2.response?.data?.message || '获取图片列表失败';
          message.error(errorMessage);
        }
      } finally {
        loading.value = false;
      }
    };

    // Default directories for auto-scan by image type
    const defaultLocations = ref<Record<string, string>>({
      general: '',
      advertising_campaign: '',
      advertising_rule: ''
    });

    const basePaths = ref<{ upload_folder: string; output_folder: string }>({
      upload_folder: '',
      output_folder: ''
    });

    const loadBasePaths = async () => {
      try {
        const res = await api.get('/images/base-paths');
        const data = res?.data?.data || res?.data || {};
        basePaths.value.upload_folder = data.upload_folder || 'upload/images';
        basePaths.value.output_folder = data.output_folder || 'output/images';
      } catch (e) {
        basePaths.value.upload_folder = 'upload/images';
        basePaths.value.output_folder = 'output/images';
      }
    };

    const loadDefaultLocations = async () => {
      try {
        const res = await api.get('/images/default-locations');
        const list = Array.isArray(res?.data?.data) ? res.data.data : res?.data || [];
        list.forEach((item: any) => {
          if (item?.image_type && item?.directory) {
            defaultLocations.value[item.image_type] = item.directory;
          }
        });
      } catch (e) {
        console.warn('加载默认目录失败', e);
      }
    };

    const saveDefaultLocations = async () => {
      const types = Object.keys(defaultLocations.value);
      const pending = types.filter(t => defaultLocations.value[t]);
      if (pending.length === 0) {
        message.warning('请填写至少一个目录');
        return;
      }
      const loadingMsg = message.loading('正在保存并加载目录...', { duration: 0 });
      try {
        for (const t of pending) {
          const val = defaultLocations.value[t] || '';
          const isAbs = val.startsWith('/') || /^[A-Za-z]:\\/.test(val);
          if (isAbs) {
            await api.post('/images/default-location', {
              image_type: t,
              directory: val
            });
          }
        }
        message.success('默认目录已保存并加载');
        showDefaultDirModal.value = false;
        await fetchImages();
      } catch (err: any) {
        console.error('保存默认目录失败', err);
        message.error(err?.response?.data?.message || '保存默认目录失败');
      } finally {
        loadingMsg.destroy();
      }
    };

    const scanConfiguredDirectories = async () => {
      const entries = Object.entries(defaultLocations.value).filter(([_, dir]) => !!dir);
      for (const [type, dir] of entries) {
        try {
          await api.post('/images/scan-directory', { directory: dir, image_type: type });
        } catch (e) {
          console.warn(`扫描目录失败: ${type} -> ${dir}`, e);
        }
      }
    };

    const selectCurrentFolder = async (type: string) => {
      const pickWithInput = () => new Promise<FileList | null>((resolve) => {
        const input = document.createElement('input');
        input.type = 'file';
        (input as any).webkitdirectory = true;
        input.onchange = (e: Event) => {
          const target = e.target as HTMLInputElement;
          resolve(target.files || null);
        };
        input.click();
      });

      const uploadFiles = async (files: FileList | null) => {
        if (!files || files.length === 0) return 0;
        const arr = Array.from(files);
        const root = (arr[0] as any).webkitRelativePath ? String((arr[0] as any).webkitRelativePath).split('/')[0] : '选定目录';
        defaultLocations.value[type] = `browser://${root}`;
        let count = 0;
        for (const f of arr) {
          if (isValidImageFile(f)) {
            try {
              await uploadFile(f as File, type);
              count += 1;
            } catch {}
          }
        }
        return count;
      };

      try {
        if ((window as any).showDirectoryPicker) {
          const dirHandle = await (window as any).showDirectoryPicker();
          const files: File[] = [];
          if (dirHandle && dirHandle.values) {
            for await (const handle of dirHandle.values()) {
              if (handle.kind === 'file') {
                const file = await handle.getFile();
                files.push(file);
              }
            }
          } else if (dirHandle && dirHandle.entries) {
            for await (const [name, handle] of (dirHandle as any).entries()) {
              if (handle.kind === 'file') {
                const file = await handle.getFile();
                files.push(file);
              }
            }
          }
          defaultLocations.value[type] = `browser://${dirHandle.name || '选定目录'}`;
          let count = 0;
          for (const f of files) {
            if (isValidImageFile(f)) {
              try {
                await uploadFile(f, type);
                count += 1;
              } catch {}
            }
          }
          if (count > 0) {
            message.success(`已从目录加载 ${count} 张图片`);
            await fetchImages();
          } else {
            message.info('目录中没有可用图片');
          }
        } else {
          const files = await pickWithInput();
          const count = await uploadFiles(files);
          if (count > 0) {
            message.success(`已从目录加载 ${count} 张图片`);
            await fetchImages();
          } else {
            message.info('目录中没有可用图片');
          }
        }
      } catch (e) {
        message.error('选择目录失败');
      }
    };

    // Reset preview state
    const resetPreview = () => {
      previewImageUrl.value = '';
      scale.value = 1;
      rotate.value = 0;
      position.value = { x: 0, y: 0 };
      isDragging.value = false;
    };

    // Initial data fetch
    onMounted(() => {
      fetchImages();
      loadBasePaths();
      loadDefaultLocations().then(scanConfiguredDirectories);
    });
    watch(imageTypeFilter, () => {
      fetchImages();
    });

    // Make sure handleDirectoryUpload is available in the template
    const handleDirectoryUploadWrapper = async (files: FileList, imageType: string) => {
      return handleDirectoryUpload(files, imageType);
    };

    return {
      // State
      viewMode,
      showPreview,
      showDefaultDirModal,
      showUploadMenu,
      previewImageUrl,
      images,
      loading,
      imageTypeFilter,
      imageTypeOptions,
      uploadOptions,
      zoomLevel,
      imageStyle,
      defaultLocations,
      basePaths,
      saveDefaultLocations,
      loadDefaultLocations,
      loadBasePaths,
      scanConfiguredDirectories,
      selectCurrentFolder,
      
      // Methods
      getImageUrl,
      formatFileSize,
      formatDate,
      showImagePreview,
      handleZoom,
      fetchImages,
      getImageTypeIcon: (type: string) => {
        const icons: Record<string, any> = {
          advertising_campaign: MegaphoneOutline,
          advertising_rule: DocumentTextOutline,
          default: ImagesOutline
        };
        return icons[type || ''] || icons.default;
      },
      getImageTypeLabel: (type: string) => {
        const labels: Record<string, string> = {
          advertising_campaign: '活动配图',
          advertising_rule: '广告规则',
          default: '普通图片'
        };
        return labels[type || ''] || labels.default;
      },
      handleImageError,
      confirmDelete,
      confirmDeleteAll,
      handleUploadSelect,
      handleDirectoryUpload: handleDirectoryUploadWrapper,
      downloadImage,
      zoomIn,
      zoomOut,
      resetZoom,
      rotateLeft,
      rotateRight,
      startDrag,
      handleDrag,
      endDrag,
      
      // Icons
      CloudUploadOutline,
      ChevronDown,
      DownloadOutline,
      Close: CloseOutline,
      SearchOutline,
      RefreshOutline,
      AddOutline,
      RemoveOutline,
      GridOutline,
      ListOutline,
      TrashOutline,
      
      // Components
      NList,
      NListItem,
      NThing,
      NRadioGroup,
      NRadioButton,
      NIcon,
      NButton,
      NButtonGroup,
      NTooltip,
      NTag,
      NEmpty,
      NSelect,
      NDropdown,
      NModal
    };
  },
});
</script>

<style scoped>
/* Preview Modal Styles */
.preview-modal .n-card {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  max-width: 100%;
  margin: 0;
  padding: 0;
  background: transparent;
  box-shadow: none;
  border-radius: 0;
}

.preview-header {
  position: fixed;
  top: 16px;
  right: 16px;
  z-index: 1000;
  padding: 0;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
  backdrop-filter: blur(4px);
}

.close-button {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  transition: all 0.2s;
  margin: 0;
  padding: 0;
}

.close-button:hover {
  background: rgba(0, 0, 0, 0.7);
  transform: scale(1.1);
}

.preview-content {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  margin: 0;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.9);
  cursor: zoom-out;
}

.image-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  margin: 0;
  overflow: hidden;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  padding: 0;
  margin: 0;
  transition: transform 0.2s ease;
  will-change: transform;
  touch-action: none;
  user-select: none;
  -webkit-user-drag: none;
}

.preview-controls {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 12px;
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.7);
  border-radius: 24px;
  backdrop-filter: blur(8px);
  z-index: 100;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.preview-controls .n-button {
  transition: all 0.2s ease;
}

.preview-controls .n-button:not(:disabled):hover {
  transform: scale(1.1);
}

.preview-controls .n-button:active {
  transform: scale(0.95);
}

/* Hide controls when not interacting */
.preview-content:not(:hover) .preview-controls {
  opacity: 0;
  pointer-events: none;
  transform: translateX(-50%) translateY(20px);
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.preview-content:hover .preview-controls {
  opacity: 1;
  pointer-events: auto;
  transform: translateX(-50%) translateY(0);
  transition: opacity 0.3s ease 0.3s, transform 0.3s ease 0.3s;
}

.empty-preview {
  height: 100%;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1e1e1e;
  color: #fff;
}

/* Override Naive UI styles */
:deep(.n-card-header) {
  padding: 0 !important;
  margin: 0 !important;
}

:deep(.n-card__content) {
  padding: 0 !important;
  margin: 0 !important;
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .preview-modal {
    width: 100% !important;
    height: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    border-radius: 0 !important;
  }
  
  .preview-header {
    padding: 4px;
  }
  
  .close-button {
    width: 36px;
    height: 36px;
  }
}

:root {
  --border-color: #e0e0e0;
  --hover-bg: #f8f8f8;
  --detail-label-color: #666;
  --detail-value-color: #333;
  --font-size-base: 15px;
  --font-size-large: 17px;
  --font-size-xlarge: 22px;
  --grid-gap: 16px;
  --card-padding: 12px;
  --content-padding: 24px;
}

/* Reset all margins and padding that might be constraining the width */
body, html {
  margin: 0;
  padding: 0;
  width: 100%;
  overflow-x: hidden;
}

.image-management {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #fff;
  padding: 0;
  box-sizing: border-box;
}

/* Main content wrapper - full width with no max-width constraint */
.content-wrapper {
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-wrapper > *:not(.list-view-container) {
  padding: 0 24px;
}

/* Grid View - Full width grid */
.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--grid-gap);
  padding: 16px 0 0 0;
  margin: 0;
  width: 100%;
  box-sizing: border-box;
}

/* List View - Full width */
.list-view-container {
  width: 100%;
  padding: 0;
  margin: 0;
  box-sizing: border-box;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.list-header {
  display: flex;
  padding: 12px 24px;
  background-color: #f8f9fa;
  border-radius: 8px 8px 0 0;
  font-weight: 600;
  margin: 0;
  align-items: center;
  min-width: 100%;
  border-bottom: 1px solid var(--border-color);
}

.header-item {
  padding: 0 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* List item styles */
.image-list {
  flex: 1;
  border-radius: 0 0 8px 8px;
  overflow: auto;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  min-height: 0; /* Allows the list to shrink below its content size */
}

.image-list-item {
  transition: background-color 0.2s;
  flex-shrink: 0;
}

.image-list-item:hover {
  background-color: #f8f9fa;
}

.list-item-content {
  width: 100%;
}

.list-item-row {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 12px 0;
}

.list-item-cell {
  padding: 0 12px;
  display: flex;
  align-items: center;
}

.list-image-container {
  width: 60px;
  height: 60px;
  border-radius: 4px;
  overflow: hidden;
  flex-shrink: 0;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
}

.list-image-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: pointer;
}

.list-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.image-name {
  font-weight: 500;
  color: var(--n-text-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.source-tag {
  flex-shrink: 0;
}

.detail-value {
  color: var(--n-text-color-secondary);
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.list-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  width: 100%;
}

/* Make sure the list items match header width */
:deep(.n-list-item) {
  padding: 0 !important;
}

:deep(.n-list-item__main) {
  width: 100%;
  padding: 0 24px;
}

:deep(.n-list-item.n-list-item--hoverable:hover) {
  background-color: #f8f9fa;
}

/* Responsive adjustments */
@media (min-width: 1600px) {
  .image-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    padding: 12px 24px;
  }
  
  .list-view-container {
    padding: 12px 24px;
  }
}

@media (max-width: 768px) {
  .image-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    padding: 8px;
    gap: 10px;
  }
  
  .list-view-container {
    padding: 8px;
  }
  
  :root {
    --font-size-base: 14px;
    --font-size-large: 16px;
    --font-size-xlarge: 20px;
  }
}

@media (max-width: 1024px) {
  .image-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    padding: 12px;
    gap: 12px;
  }
  
  .list-view-container {
    padding: 12px;
  }
}

@media (max-width: 1200px) {
  :root {
    --font-size-base: 14px;
    --font-size-large: 16px;
    --font-size-xlarge: 20px;
  }
  
  .list-header {
    padding: 10px 12px;
  }
}

@media (max-width: 768px) {
  :root {
    --content-max-width: 100%;
    --grid-gap: 16px;
  }
  
  .content-wrapper {
    flex: 1;
    width: 100%;
    max-width: 100%;
    padding: 16px;
    margin: 0;
    overflow-y: auto;
    box-sizing: border-box;
  }
  
  .list-view-container {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    padding: 8px 0;
  }
  
  .list-header,
  :deep(.n-list-item__main) {
    min-width: 900px; /* Ensure header and content match width when scrolling */
    padding: 12px 16px;
  }
  
  .image-name {
    max-width: 120px;
  }
  
  .list-image-container {
    width: 50px;
    height: 50px;
  }
  
  .header-item,
  .list-item-cell {
    padding: 0 8px;
    font-size: 13px;
  }
  
  .detail-value {
    font-size: 13px;
  }
}

.page-header {
  width: 100%;
  margin: 0 0 24px 0;
  padding: 0 0 16px 0;
  border-bottom: 1px solid var(--border-color);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  gap: 20px;
  position: relative;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  color: var(--detail-label-color);
  font-size: 14px;
}

.type-select {
  width: 200px;
}

.delete-all {
  margin-left: auto;
}

.default-dir {
  margin-left: 8px;
}

.default-dir-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.default-dir-form .form-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.default-dir-form .form-label {
  width: 100px;
  color: var(--detail-label-color);
}

.default-dir-form .form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.page-title {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  margin: 0;
}

.view-options {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-left: auto;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
  padding: 12px;
  margin-top: 12px;
}

.image-item {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.image-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.image-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.image-preview {
  width: 100%;
  height: 280px;
  object-fit: contain;
  background-color: #f8f8f8;
  border-radius: 6px;
  padding: 4px;
  display: block;
  background-color: #f5f5f5;
  transition: transform 0.2s ease;
}

.image-info {
  padding: 8px 12px 12px;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.image-name {
  font-weight: 500;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 13px;
  color: #444;
}

.image-meta {
  display: flex;
  justify-content: space-between;
  color: #666;
  font-size: 12px;
  margin-bottom: 12px;
}

.image-actions {
  display: flex;
  gap: 6px;
  margin-top: 6px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

.image-actions .n-button {
  --n-height: 24px;
  --n-padding: 0 8px;
  font-size: 12px;
}

/* Table Styles */
.table-header {
  background-color: #f8f8f8;
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 10;
}

.table-row {
  display: flex;
  padding: 12px 16px;
  align-items: center;
  font-weight: 500;
  color: var(--detail-label-color);
  font-size: 14px;
  background: #f8f8f8;
}

.table-cell {
  padding: 0 8px;
  display: flex;
  align-items: center;
  min-height: 40px;
}

.table-body {
  overflow-y: auto;
  max-height: calc(100vh - 200px);
}

/* List view container */
.list-view-container {
  margin-top: 0;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding-top: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* Empty state container */
.empty-state-container {
  padding: 40px 0;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
  flex-grow: 1;
}

/* List item styles */
.image-list-item {
  display: flex;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  align-items: center;
  transition: background-color 0.2s ease;
}

.image-list-item:hover {
  background-color: #f9f9f9;
}

.image-list-item {
  transition: background-color 0.2s ease;
  border-bottom: 1px solid var(--border-color);
}

.image-list-item:hover {
  background-color: #f9f9f9;
}

.list-image-preview {
  width: 60px;
  height: 60px;
  object-fit: cover;
  border-radius: 4px;
  background-color: #f5f5f5;
}

.list-image-meta {
  display: flex;
  gap: 8px;
  color: #666;
  font-size: 13px;
  margin-top: 4px;
}

.list-header {
  display: flex;
  padding: 12px 16px;
  background-color: #f8f8f8;
  border-bottom: 1px solid var(--border-color);
  font-weight: 500;
  color: var(--detail-label-color);
  font-size: 14px;
}

.header-item {
  padding: 0 8px;
  display: flex;
  align-items: center;
}

.empty-state {
  padding: 40px 0;
  text-align: center;
  color: var(--detail-label-color);
}

.list-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  padding-right: 8px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .image-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 16px;
  }
  
  .list-image-preview {
    width: 50px;
    height: 50px;
  }
}
</style>
