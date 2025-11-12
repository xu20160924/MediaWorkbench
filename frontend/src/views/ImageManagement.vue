<template>
  <div class="image-management">
    <!-- Preview Modal -->
    <n-modal 
      v-model:show="showPreview" 
      :mask-closable="true"
      :auto-focus="false"
      preset="card"
      style="width: 95%; max-width: 1200px; height: 95vh;"
      :bordered="false"
      :closable="false"
      class="preview-modal"
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
      <div class="preview-content">
        <div class="image-container">
          <img 
            :src="previewImageUrl" 
            alt="图片预览" 
            class="preview-image" 
            v-if="previewImageUrl" 
            @click="showPreview = false"
          />
          <n-empty 
            v-else 
            description="预览不可用" 
            class="empty-preview"
          />
        </div>
      </div>
    </n-modal>

    <div class="content-wrapper">
      <div class="page-header">
        <div class="header-content">
          <n-dropdown
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
          
          <input
            id="file-upload"
            type="file"
            multiple
            accept="image/*"
            style="display: none"
            @change="handleFileSelect"
          />
          
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
            <img :src="getImageUrl(image.path)" :alt="image.name" class="image-preview" @error="handleImageError" />
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
                <template #avatar>
                  <div class="list-image-container">
                    <img :src="getImageUrl(image.path)" class="list-image-preview" @error="handleImageError" />
                  </div>
                </template>
                <div class="list-item-content">
                  <div class="list-item-row">
                    <div class="list-item-cell" style="flex: 2;">
                      <div class="list-item-header">
                        <div class="image-name">{{ image.name }}</div>
                        <n-tag size="small" :type="image.source === 'upload' ? 'success' : 'info'" class="source-tag">
                          {{ image.source === 'upload' ? '上传' : '本地' }}
                        </n-tag>
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
                          删除
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
import { defineComponent, ref, onMounted, h } from 'vue';
import { 
  useMessage, 
  useDialog, 
  NList, 
  NListItem, 
  NThing, 
  NRadioGroup, 
  NRadioButton, 
  NIcon, 
  NButton, 
  NTag,
  NTooltip,
  NEmpty
} from 'naive-ui';
import { DownloadOutline, TrashOutline, Close, SearchOutline } from '@vicons/ionicons5';
import { GridOutline, ListOutline } from '@vicons/ionicons5';
import { listImages, uploadImage } from '@/api/functions';
import { CloudUploadOutline, ChevronDown, FolderOpenOutline, ImageOutline } from '@vicons/ionicons5';

export default defineComponent({
  name: 'ImageManagement',
  components: {
    CloudUploadOutline,
    ChevronDown,
    FolderOpenOutline,
    ImageOutline,
    NList,
    NListItem,
    NThing,
    NRadioGroup,
    NRadioButton,
    NIcon,
    GridOutline,
    ListOutline,
    DownloadOutline,
    TrashOutline,
    NTooltip,
    NButton,
    NTag,
    NEmpty
  },
  setup() {
    const message = useMessage();
    const dialog = useDialog();
    const viewMode = ref<'grid' | 'list'>('grid');
    const showPreview = ref(false);
    const previewImageUrl = ref('');
    interface ImageItem {
      id: number;
      name: string;
      path: string;
      size: number;
      created_at: string;
      source: 'upload' | 'local_dir';
      workflow_name?: string;
    }

    const images = ref<ImageItem[]>([]);

    const uploadOptions = [
      {
        label: '上传图片',
        key: 'upload',
        props: {
          icon: () => h(NIcon, null, { default: () => h(ImageOutline) })
        }
      },
      {
        label: '从文件夹添加',
        key: 'directory',
        props: {
          icon: () => h(NIcon, null, { default: () => h(FolderOpenOutline) })
        }
      }
    ];

    const handleUploadSelect = (key: string) => {
      if (key === 'upload') {
        document.getElementById('file-upload')?.click()
      } else if (key === 'directory') {
        // @ts-ignore - webkitdirectory is not in the standard yet
        const input = document.createElement('input')
        input.type = 'file'
        input.webkitdirectory = true
        input.multiple = true
        input.accept = 'image/*'
        input.onchange = handleDirectorySelect
        input.click()
      }
    };

    const handleFileSelect = async (event: Event) => {
      const input = event.target as HTMLInputElement
      if (input.files && input.files.length > 0) {
        const files = Array.from(input.files)
        // Filter out non-image files
        const imageFiles = files.filter(file => file.type.startsWith('image/'))
        if (imageFiles.length === 0) {
          message.error('请选择有效的图片文件')
          return
        }
        await uploadFiles(imageFiles)
      }
    };

    const handleDirectorySelect = async (event: Event) => {
      const input = event.target as HTMLInputElement
      if (input.files && input.files.length > 0) {
        await uploadFiles(Array.from(input.files))
      }
    };

    const uploadFiles = async (files: File[]) => {
      if (files.length === 0) return

      const uploadPromises = files.map(async (file) => {
        const formData = new FormData()
        formData.append('file', file)  // Note: backend expects 'file' not 'files'
        
        try {
          const response = await uploadImage(formData)
          if (response && response.success) {
            return { success: true, file: file.name }
          } else {
            return { success: false, file: file.name, error: response?.message || '上传失败' }
          }
        } catch (error: any) {
          console.error(`Upload failed for ${file.name}:`, error)
          return { 
            success: false, 
            file: file.name, 
            error: error?.response?.data?.message || '上传失败，请检查网络连接'
          }
        }
      })

      try {
        const results = await Promise.all(uploadPromises)
        const successCount = results.filter(r => r.success).length
        const errorCount = results.length - successCount
        
        if (successCount > 0) {
          message.success(`成功上传 ${successCount} 个文件`)
          await fetchImages()
        }
        
        if (errorCount > 0) {
          const errorFiles = results
            .filter(r => !r.success)
            .map(r => `${r.file}: ${r.error}`)
            .join('\n')
          message.error(`${errorCount} 个文件上传失败：\n${errorFiles}`)
        }
      } catch (error) {
        console.error('Error processing uploads:', error)
        message.error('处理上传时发生错误')
      } finally {
        // Reset file input
        const input = document.getElementById('file-upload') as HTMLInputElement
        if (input) input.value = ''
      }
    };

    // Function to show image preview
    const showImagePreview = (image: ImageItem) => {
      console.log('Showing preview for image:', image);
      
      // Use the direct file URL from the backend
      let url = '';
      
      // If the path is a full URL, use it directly
      if (image.path.startsWith('http')) {
        url = image.path;
      } else {
        // Otherwise, construct the URL using the filename
        const filename = image.path.split('/').pop() || '';
        url = `/api/images/uploads/${encodeURIComponent(filename)}?t=${new Date().getTime()}`;
      }
      
      console.log('Using preview URL:', url);
      previewImageUrl.value = url;
      showPreview.value = true;
      
      // For debugging - log if the image loads or fails
      const img = new Image();
      img.onload = () => {
        console.log('Preview image loaded successfully');
        console.log('Image dimensions:', img.width, 'x', img.height);
      };
      img.onerror = (e) => {
        console.error('Failed to load preview image:', e);
        console.error('Failed URL:', url);
      };
      img.src = url;
    };

    // Define fetchImages before it's used
    const fetchImages = async () => {
      try {
        const response = await listImages({ page: 1, page_size: 20 });
        if (response.success && response.data) {
          images.value = response.data.items.map((img) => {
            // Ensure source is either 'upload' or 'local_dir'
            const source = img.source === 'local_dir' ? 'local_dir' : 'upload';
            return {
              id: img.id,
              name: img.filename || `image-${img.id}`,
              path: img.file_path,
              size: 0, // Backend doesn't currently provide file size
              created_at: img.created_at,
              source: source,
              workflow_name: img.workflow_name
            };
          });
        } else {
          throw new Error(response.message || 'Failed to load images');
        }
      } catch (error) {
        console.error('Error fetching images:', error);
        message.error('获取图片列表失败: ' + (error as Error).message);
      }
    };

    const getImageUrl = (path: string) => {
      if (!path) {
        console.warn('getImageUrl called with empty path');
        return '';
      }
      
      // If it's already a full URL, return as is
      if (path.startsWith('http')) {
        console.log('Returning full URL:', path);
        return path;
      }
      
      // Log the original path for debugging
      console.log('Original image path:', path);
      
      // Remove any 'uploads/' prefix if present
      let cleanPath = path.replace(/^uploads[\\/]/, '');
      
      // Get just the filename without any path
      let filename = cleanPath.split('/').pop() || cleanPath;
      
      // Remove any URL parameters if present
      filename = filename.split('?')[0];
      
      console.log('Extracted filename:', filename);
      
      // Base URL for uploaded images
      const baseUrl = '/api/images/uploads';
      const timestamp = new Date().getTime();
      
      // Encode the filename but keep forward slashes as is
      const encodedFilename = encodeURIComponent(filename).replace(/%2F/g, '/');
      
      // Construct the final URL
      const imageUrl = `${baseUrl}/${encodedFilename}?t=${timestamp}`;
      
      console.log('Generated image URL:', imageUrl);
      return imageUrl;
    };

    const formatFileSize = (bytes: number) => {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const formatDate = (dateString: string) => {
      return new Date(dateString).toLocaleString();
    };

    const downloadImage = (image: { name: string; path: string }) => {
      const link = document.createElement('a');
      link.href = getImageUrl(image.path);
      link.download = image.name;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    };

    const deleteImage = async (image: any) => {
      try {
        const url = new URL(`/api/images/delete/${image.id}`, window.location.origin);
        
        console.log('Sending DELETE request to:', url.toString());
        
        const response = await fetch(url.toString(), {
          method: 'DELETE',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          mode: 'cors',
          cache: 'no-cache',
          redirect: 'follow',
          referrerPolicy: 'no-referrer'
        });

        console.log('Delete response status:', response.status);
        
        // Read the response once
        const responseText = await response.text();
        let responseData;
        
        try {
          responseData = responseText ? JSON.parse(responseText) : {};
          console.log('Response data:', responseData);
        } catch (e) {
          console.warn('Response is not valid JSON:', responseText);
          responseData = { message: responseText };
        }

        if (!response.ok) {
          throw new Error(responseData.message || `删除图片失败 (${response.status})`);
        }

        // If we get here, the delete was successful
        const index = images.value.findIndex(img => img.id === image.id);
        if (index !== -1) {
          images.value.splice(index, 1);
        }
        
        message.success('图片删除成功');
      } catch (error: any) {
        console.error('Error deleting image:', error);
        message.error(error.message || '删除图片失败');
      }
    };

    const confirmDelete = (image: { id: number; name: string }) => {
      dialog.warning({
        title: '确认删除',
        content: `确定要删除图片 "${image.name}" 吗？`,
        positiveText: '删除',
        negativeText: '取消',
        onPositiveClick: () => deleteImage(image),
      });
    };

    const handleImageError = (e: Event) => {
      const img = e.target as HTMLImageElement;
      console.error('Failed to load image:', img.src);
      
      // Log additional debugging information
      const imageSrc = img.getAttribute('src') || '';
      console.log('Image source:', imageSrc);
      console.log('Image alt:', img.alt);
      
      // Only set the error image if it's not already set to prevent infinite loops
      if (!img.src.startsWith('data:image/svg+xml')) {
        // Log the error to help with debugging
        console.error('Image failed to load, showing error placeholder');
        
        // Create a simple error placeholder SVG with more visible error information
        const svg = `
          <svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 200 100" fill="#f8f8f8" stroke="#ff4d4f" stroke-width="2">
            <rect x="2" y="2" width="196" height="96" rx="4" fill="#fff2f0" stroke-width="2"/>
            <text x="50%" y="40%" text-anchor="middle" font-family="Arial" font-size="12" fill="#ff4d4f">Image failed to load</text>
            <text x="50%" y="60%" text-anchor="middle" font-family="Arial" font-size="10" fill="#999">${img.alt || 'No description'}</text>
          </svg>
        `;
        const svgData = `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svg)))}`;
        img.src = svgData;
        img.onerror = null; // Prevent infinite loop
      }
    };

    onMounted(() => {
      fetchImages();
    });

    return {
      images,
      viewMode,
      uploadOptions,
      showPreview,
      previewImageUrl,
      handleUploadSelect,
      handleFileSelect,
      getImageUrl,
      formatFileSize,
      formatDate,
      confirmDelete,
      handleImageError,
      showImagePreview,
      GridOutline,
      ListOutline,
      DownloadOutline,
      TrashOutline,
      CloudUploadOutline,
      ChevronDown,
      FolderOpenOutline,
      ImageOutline,
      SearchOutline,
      Close
    };
  },
});
</script>

<style scoped>
/* Preview Modal Styles */
.preview-modal .n-card {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 0;
  overflow: hidden;
  background: #1e1e1e;
}

.preview-header {
  position: absolute;
  top: 0;
  right: 0;
  z-index: 10;
  padding: 8px;
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
  flex: 1;
  display: flex;
  padding: 0;
  margin: 0;
  height: 100%;
  overflow: hidden;
}

.image-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  margin: 0;
  overflow: auto;
  background: #1e1e1e;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  padding: 0;
  margin: 0;
  transition: transform 0.2s;
  cursor: zoom-out;
}

.preview-image:hover {
  transform: scale(1.01);
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
  margin: 0;
  padding: 24px;
  box-sizing: border-box;
  overflow-y: auto;
  flex: 1;
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
  padding: 16px 0 0 0;
  margin: 0;
  box-sizing: border-box;
}

.list-header {
  display: flex;
  padding: 12px 16px;
  background-color: #f8f9fa;
  border-radius: 8px;
  font-weight: 600;
  margin-bottom: 12px;
}

.header-item {
  padding: 0 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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
  }
  
  .list-header {
    min-width: 900px; /* Ensure header matches content width when scrolling */
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
