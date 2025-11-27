<template>
  <div class="image-management">
    <!-- Drop Zone Overlay -->
    <div v-if="isDropZoneActive" class="drop-zone-overlay">
      <div class="drop-zone-content">
        <n-icon size="64"><CloudUploadOutline /></n-icon>
        <p>释放以上传图片</p>
        <p class="hint">支持拖放或粘贴 (Ctrl+V)</p>
      </div>
    </div>
    
    <!-- Image Type Selection Modal for Dropped Files -->
    <n-modal
      v-model:show="showDropTypeModal"
      preset="dialog"
      title="选择图片类型"
      positive-text="上传"
      negative-text="取消"
      @positive-click="handleDropTypeConfirm"
      @negative-click="handleDropTypeCancel"
    >
      <div style="padding: 20px 0;">
        <p style="margin-bottom: 16px; color: #666;">请为这 {{ pendingDropFiles.length }} 张图片选择类型：</p>
        <n-radio-group v-model:value="selectedDropType" name="drop-image-type">
          <n-space vertical>
            <n-radio value="general">
              <n-space align="center">
                <n-icon :component="ImagesOutline" />
                <span>普通图片</span>
              </n-space>
            </n-radio>
            <n-radio value="advertising_campaign">
              <n-space align="center">
                <n-icon :component="MegaphoneOutline" />
                <span>活动配图</span>
              </n-space>
            </n-radio>
            <n-radio value="advertising_rule">
              <n-space align="center">
                <n-icon :component="DocumentTextOutline" />
                <span>广告规则</span>
              </n-space>
            </n-radio>
          </n-space>
        </n-radio-group>
      </div>
    </n-modal>
    
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
        <!-- Navigation Arrows -->
        <n-button
          v-if="images.length > 1"
          class="nav-arrow nav-arrow-left"
          circle
          size="large"
          type="primary"
          ghost
          @click.stop="navigatePreview('prev')"
        >
          <template #icon>
            <n-icon size="28"><ChevronBack /></n-icon>
          </template>
        </n-button>
        
        <n-button
          v-if="images.length > 1"
          class="nav-arrow nav-arrow-right"
          circle
          size="large"
          type="primary"
          ghost
          @click.stop="navigatePreview('next')"
        >
          <template #icon>
            <n-icon size="28"><ChevronForward /></n-icon>
          </template>
        </n-button>
        
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
          <div class="control-section">
            <span class="control-label">缩放</span>
            <n-button-group>
              <n-button @click="zoomOut" :disabled="zoomLevel <= 0.5" size="small">
                <template #icon>
                  <n-icon><RemoveOutline /></n-icon>
                </template>
              </n-button>
              <n-button @click="resetZoom" size="small" strong>
                {{ Math.round(zoomLevel * 100) }}%
              </n-button>
              <n-button @click="zoomIn" :disabled="zoomLevel >= 3" size="small">
                <template #icon>
                  <n-icon><AddOutline /></n-icon>
                </template>
              </n-button>
            </n-button-group>
          </div>
          
          <div class="control-divider"></div>
          
          <div class="control-section">
            <span class="control-label">旋转</span>
            <n-button-group>
              <n-button @click="rotateLeft" size="small">
                <template #icon>
                  <n-icon><RefreshOutline /></n-icon>
                </template>
              </n-button>
              <n-button @click="rotateRight" size="small">
                <template #icon>
                  <n-icon><RefreshOutline style="transform: scaleX(-1);" /></n-icon>
                </template>
              </n-button>
            </n-button-group>
          </div>
          
          <div class="control-divider"></div>
          
          <n-button type="primary" @click="downloadImage" size="small">
            <template #icon>
              <n-icon><DownloadOutline /></n-icon>
            </template>
            下载
          </n-button>
        </div>
  </div>
</n-modal>

<!-- Participation Image Preview Modal -->
<n-modal v-model:show="showParticipationPreview" preset="card" :title="participationPreviewTitle" :mask-closable="true" style="width: 800px">
  <div class="participation-preview-content">
    <div class="preview-image-wrapper">
      <img :src="getImageUrl(participationPreviewImage)" :alt="participationPreviewImage?.name" class="large-preview-image" />
    </div>
    
    <n-divider />
    
    <n-form label-placement="top">
      <n-form-item label="图片标签">
        <n-dynamic-tags v-model:value="participationPreviewImage.tags" @create="handleTagCreate">
          <template #input="{ activate, deactivate }">
            <n-input
              ref="tagInputRef"
              :placeholder="'输入标签后按回车，或粘贴 (Ctrl+V)'"
              @keyup.enter="activate"
              @blur="deactivate"
            />
          </template>
        </n-dynamic-tags>
        <template #feedback>
          <span style="font-size: 12px; color: #999;">提示：可直接粘贴标签文本</span>
        </template>
      </n-form-item>
      
      <n-form-item label="选择状态">
        <n-switch v-model:value="participationPreviewSelected" @update:value="handlePreviewSelectionToggle">
          <template #checked>已选择</template>
          <template #unchecked>未选择</template>
        </n-switch>
      </n-form-item>
    </n-form>
  </div>
  
  <template #footer>
    <div style="display: flex; justify-content: flex-end; gap: 12px;">
      <n-button @click="saveParticipationPreviewTags">保存标签</n-button>
      <n-button type="primary" @click="showParticipationPreview = false">关闭</n-button>
    </div>
  </template>
</n-modal>

<!-- Participation Prompt Modal -->
<n-modal v-model:show="showPromptModal" preset="card" title="参与广告提示词" :mask-closable="true" :bordered="false">
  <div class="prompt-content">{{ participationPrompt }}</div>
  <div class="form-actions">
    <n-button type="primary" @click="showPromptModal=false">关闭</n-button>
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
          <n-input v-model:value="defaultLocations.general" placeholder="请输入服务器绝对路径，如: /tmp/images" />
          <n-button size="small" @click="selectCurrentFolder('general')">
            <template #icon><n-icon><FolderOpenOutline /></n-icon></template>
            浏览
          </n-button>
        </div>
        <div class="form-row">
          <div class="form-label">活动配图</div>
          <n-input v-model:value="defaultLocations.advertising_campaign" placeholder="请输入服务器绝对路径，如: /tmp/ads" />
          <n-button size="small" @click="selectCurrentFolder('advertising_campaign')">
            <template #icon><n-icon><FolderOpenOutline /></n-icon></template>
            浏览
          </n-button>
        </div>
        <div class="form-row">
          <div class="form-label">广告规则</div>
          <n-input v-model:value="defaultLocations.advertising_rule" placeholder="请输入服务器绝对路径，如: /tmp/rules" />
          <n-button size="small" @click="selectCurrentFolder('advertising_rule')">
            <template #icon><n-icon><FolderOpenOutline /></n-icon></template>
            浏览
          </n-button>
        </div>
        <div class="form-row">
          <div class="form-label">规则卡片</div>
          <n-input v-model:value="defaultLocations.rule_card_screenshot" placeholder="请输入服务器绝对路径，如: /tmp/rule_cards" />
          <n-button size="small" @click="selectCurrentFolder('rule_card_screenshot')">
            <template #icon><n-icon><FolderOpenOutline /></n-icon></template>
            浏览
          </n-button>
        </div>
        <div class="form-actions">
          <n-button type="primary" @click="saveDefaultLocations">保存并加载</n-button>
        </div>
      </div>
    </n-modal>

    <!-- Main Content -->
    <div class="content-wrapper">
      <div class="content-header" style="padding-top: 12px;">
        <div class="header-row">
          <div class="header-actions-left">
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
            <div class="filter-group">
              <span class="filter-label">参与状态</span>
              <n-select
                v-model:value="participationFilter"
                :options="participationOptions"
                class="type-select"
                clearable
                placeholder="筛选参与状态"
              />
            </div>
            <n-button ghost class="default-dir" @click="showDefaultDirModal = true">
              <template #icon>
                <n-icon><FolderOpenOutline /></n-icon>
              </template>
              默认目录
            </n-button>
            <n-button :type="selectMode ? 'primary' : 'default'" ghost @click="toggleSelectMode">
              <template #icon>
                <n-icon v-if="!selectMode"><CheckboxOutline /></n-icon>
                <n-icon v-else><CloseOutline /></n-icon>
              </template>
              {{ selectMode ? '取消选择' : '批量选择' }}
            </n-button>
            <n-button v-if="selectMode" type="primary" ghost @click="selectAll">
              <template #icon>
                <n-icon><CheckmarkDoneOutline /></n-icon>
              </template>
              全选
            </n-button>
            <n-button v-if="selectMode && hasSelectedImages" type="error" ghost @click="confirmDeleteSelected">
              <template #icon>
                <n-icon><TrashOutline /></n-icon>
              </template>
              删除选中 ({{ selectedCount }})
            </n-button>
            <n-button v-if="selectMode && hasSelectedImages" type="warning" ghost @click="showBatchStatusModal">
              <template #icon>
                <n-icon><RefreshOutline /></n-icon>
              </template>
              更新状态 ({{ selectedCount }})
            </n-button>
            <n-button v-if="!selectMode" type="warning" ghost @click="cleanupOrphanImages">
              <template #icon>
                <n-icon><TrashOutline /></n-icon>
              </template>
              清理脏数据
            </n-button>
          </div>
          <div class="header-actions-right">
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
          <div class="image-preview-container" @click="selectMode ? onSelect(image) : showImagePreview(image)">
            <img :src="getImageUrl(image)" :alt="image.name" class="image-preview" @error="handleImageError" />
            <div v-if="!selectMode" class="preview-overlay">
              <n-icon size="24"><SearchOutline /></n-icon>
              <span>预览</span>
            </div>
            <!-- Preview button in select mode -->
            <n-button v-if="selectMode && isSelectable(image)" class="preview-btn" size="tiny" circle type="info" @click.stop="openParticipationPreview(image)">
              <template #icon>
                <n-icon><EyeOutline /></n-icon>
              </template>
            </n-button>
          </div>
          <div class="image-info">
            <div class="image-name">{{ image.name }}</div>
            <div class="image-meta">
              <span>{{ formatFileSize(image.size) }}</span>
              <span>{{ formatDate(image.created_at) }}</span>
            </div>
            <div class="image-actions">
              <div class="actions-left">
                <n-tag v-if="image.participated" type="success">已参与</n-tag>
                <n-button v-if="image.image_type==='advertising_rule'" size="small" type="primary" ghost @click="toggleParticipated(image)">参与</n-button>
                <n-button size="small" type="error" ghost @click="confirmDelete(image)">删除</n-button>
              </div>
              <div class="actions-right">
                <n-button v-if="selectMode && isSelectable(image)" 
                  circle
                  size="medium" 
                  :type="isSelected(image) ? 'success' : 'default'" 
                  :ghost="!isSelected(image)"
                  @click.stop="onSelect(image)">
                  <template #icon>
                    <n-icon size="20">
                      <CheckmarkCircleOutline v-if="isSelected(image)" />
                      <EllipseOutline v-else />
                    </n-icon>
                  </template>
                </n-button>
              </div>
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
            <n-list-item v-for="(image, index) in images" :key="'list-' + index" class="image-list-item" @click="selectMode ? onSelect(image) : undefined">
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
                    
                    <div class="list-item-cell" style="width: 180px;">
                      <div class="list-actions">
                        <n-tag v-if="image.participated" size="small" type="success">已参与</n-tag>
                        <n-tooltip v-if="image.image_type==='advertising_rule'" trigger="hover">
                          <template #trigger>
                            <n-button text @click="toggleParticipated(image)">
                              <template #icon>
                                <n-icon><AddOutline /></n-icon>
                              </template>
                            </n-button>
                          </template>
                          <span>参与</span>
                        </n-tooltip>
                        <n-button v-if="selectMode && isSelectable(image)" 
                          circle
                          size="medium"
                          :type="isSelected(image) ? 'success' : 'default'" 
                          :ghost="!isSelected(image)"
                          @click.stop="onSelect(image)"
                          class="select-button">
                          <template #icon>
                            <n-icon size="20">
                              <CheckmarkCircleOutline v-if="isSelected(image)" />
                              <EllipseOutline v-else />
                            </n-icon>
                          </template>
                        </n-button>
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
import { useRouter } from 'vue-router';

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
  participated?: boolean;
  tags?: string[];
  variables?: {
    participated?: boolean;
    [key: string]: any;
  };
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
  NCard,
  NThing,
  NRadioGroup,
  NRadioButton,
  NRadio,
  NSpace,
  NTag,
  NSelect,
  NInput,
  NForm,
  NFormItem,
  NSwitch,
  NDivider,
  NDynamicTags
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
  DownloadOutline,
  ChevronBack,
  ChevronForward,
  CheckboxOutline,
  CheckmarkCircleOutline,
  EllipseOutline,
  CheckmarkDoneOutline
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
    DownloadOutline,
    CheckboxOutline,
    CheckmarkCircleOutline,
    EllipseOutline,
    CheckmarkDoneOutline
  },
  
  setup() {
    const message = useMessage();
    const dialog = useDialog();
    
    // State
    const viewMode = ref<ViewMode>('grid');
    const showPreview = ref(false);
    const showDefaultDirModal = ref(false);
    const showUploadMenu = ref(false);
    const showDropTypeModal = ref(false);
    const previewImageUrl = ref('');
    const currentPreviewIndex = ref(-1);
    const images = ref<ImageItem[]>([]);
    const pendingDropFiles = ref<File[]>([]);
    const selectedDropType = ref('general');
    const loading = ref(false);
    const imageTypeFilter = ref('all');
    const participationFilter = ref('all');
    const selectMode = ref(false);
    const selectedRegular = ref<number[]>([]);
    const selectedEvent = ref<number[]>([]);
    const showPromptModal = ref(false);
    const participationPrompt = ref('');
    
    // Participation preview
    const showParticipationPreview = ref(false);
    const participationPreviewImage = ref<any>({});
    const tagInputRef = ref<any>(null);
    
    const participationPreviewTitle = computed(() => {
      return participationPreviewImage.value?.name || '图片预览';
    });
    
    const participationPreviewSelected = computed({
      get: () => {
        const id = Number(participationPreviewImage.value?.id || -1);
        const type = participationPreviewImage.value?.image_type || '';
        if (type === 'general') return selectedRegular.value.includes(id);
        if (type === 'advertising_campaign') return selectedEvent.value.includes(id);
        return false;
      },
      set: (val: boolean) => {
        const id = Number(participationPreviewImage.value?.id || -1);
        const type = participationPreviewImage.value?.image_type || '';
        if (type === 'general') {
          const idx = selectedRegular.value.indexOf(id);
          if (val && idx < 0) selectedRegular.value.push(id);
          else if (!val && idx >= 0) selectedRegular.value.splice(idx, 1);
        } else if (type === 'advertising_campaign') {
          const idx = selectedEvent.value.indexOf(id);
          if (val && idx < 0) selectedEvent.value.push(id);
          else if (!val && idx >= 0) selectedEvent.value.splice(idx, 1);
        }
      }
    });
    
    // Image type options for the dropdown
    const imageTypeOptions = [
      { label: '所有类型', value: 'all' },
      { label: '普通图片', value: 'general' },
      { label: '活动配图', value: 'advertising_campaign' },
      { label: '广告规则', value: 'advertising_rule' },
    ];
    
    // Participation filter options
    const participationOptions = [
      { label: '全部', value: 'all' },
      { label: '已参与', value: 'participated' },
      { label: '未参与', value: 'not_participated' },
    ];
    
    // Image preview state
    const scale = ref(1);
    const rotate = ref(0);
    const position = ref<Position>({ x: 0, y: 0 });
    const isDragging = ref(false);
    const dragStart = ref({ x: 0, y: 0 });
    
    // Calculate zoom level for display (as number, not string)
    const zoomLevel = computed(() => scale.value);
    
    // Image URL helper - uses ID-based endpoint for reliable image serving
    const getImageUrl = (image: any): string => {
      if (!image) {
        return '';
      }
      
      const baseEnv = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');
      
      // PRIMARY: Use ID-based endpoint - most reliable method
      if (image.id) {
        return `${baseEnv}/images/${image.id}/file`;
      }
      
      // FALLBACK: Check for full URL
      if (image.url?.startsWith('http')) {
        return image.url;
      }
      if (image.img_url?.startsWith('http')) {
        return image.img_url;
      }
      
      // FALLBACK: Try to construct URL from path
      let imagePath = image.img_url || image.url || image.file_path || image.local_path || image.path || '';
      
      if (!imagePath) {
        return '';
      }
      
      let p = String(imagePath).replace(/\\/g, '/');
      
      if (p.startsWith('http')) {
        return p;
      }
      
      // Extract filename from various path formats
      const filename = p.split('/').pop() || '';
      if (!filename) {
        return '';
      }
      
      // Try upload folder first, then output folder
      if (p.includes('upload') || p.includes('Upload')) {
        return `${baseEnv}/images/uploads/${filename}`;
      } else if (p.includes('output') || p.includes('Output')) {
        return `${baseEnv}/images/output/${filename}`;
      }
      
      // Default to uploads
      return `${baseEnv}/images/uploads/${filename}`;
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
      
      // Find the index of the image in the current images array
      const index = images.value.findIndex(img => img.id === image.id);
      currentPreviewIndex.value = index;
      
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
    
    // Navigate to previous/next image
    const navigatePreview = (direction: 'prev' | 'next') => {
      if (images.value.length === 0 || currentPreviewIndex.value === -1) return;
      
      let newIndex = currentPreviewIndex.value;
      if (direction === 'prev') {
        newIndex = currentPreviewIndex.value > 0 ? currentPreviewIndex.value - 1 : images.value.length - 1;
      } else {
        newIndex = currentPreviewIndex.value < images.value.length - 1 ? currentPreviewIndex.value + 1 : 0;
      }
      
      const newImage = images.value[newIndex];
      if (newImage) {
        showImagePreview(newImage);
      }
    };
    
    // Keyboard navigation
    const handleKeydown = (e: KeyboardEvent) => {
      if (!showPreview.value) return;
      
      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        navigatePreview('prev');
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        navigatePreview('next');
      } else if (e.key === 'Escape') {
        e.preventDefault();
        showPreview.value = false;
      }
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
            const errors: Array<{id: number | string, name: string, error: string}> = [];

            for (const img of [...images.value]) { // Create a copy of the array to avoid modification during iteration
              try {
                await api.delete(`/images/delete/${img.id}`);
                successCount++;
                // Update progress
                loading.content = `正在删除图片 (${successCount}/${total})...`;
              } catch (error: any) {
                console.error(`Failed to delete image ${img.id}:`, error);
                const errorMsg = error.response?.data?.message || error.message || '未知错误';
                errors.push({
                  id: img.id || 'unknown',
                  name: img.name || '未命名',
                  error: errorMsg
                });
              }
            }

            // Show results
            if (successCount > 0) {
              message.success(`成功删除 ${successCount} 张图片`);
            }
            if (errors.length > 0) {
              const errorDetails = errors.map(e => `  - ${e.name} (ID: ${e.id}): ${e.error}`).join('\n');
              message.error(`${errors.length} 张图片删除失败，请检查控制台查看详情`);
              console.error('删除失败的图片详情:\n', errorDetails);
              console.error('完整错误信息:', errors);
            }

            // Refresh the list
            await fetchImages();
          } catch (error: any) {
            console.error('Delete all failed:', error);
            message.error('删除失败: ' + (error?.response?.data?.message || error?.message || '未知错误'));
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
            label: '活动配图', 
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
            label: '活动配图目录', 
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
        const params: any = {
          per_page: 1000  // Request a large number to get all images
        };
        
        if (imageTypeFilter.value !== 'all') {
          params.image_type = imageTypeFilter.value;
        } else {
          // Exclude rule_card_screenshot from 'all' filter
          params.exclude_type = 'rule_card_screenshot';
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
        } else {
          // Exclude rule_card_screenshot from 'all' filter
          normalized = normalized.filter((it: any) => {
            const t = it?.image_type || 'general';
            return t !== 'rule_card_screenshot';
          });
        }
        if (participationFilter.value !== 'all') {
          normalized = normalized.filter((it: any) => {
            const participated = it?.participated || false;
            if (participationFilter.value === 'participated') {
              return participated === true;
            } else if (participationFilter.value === 'not_participated') {
              return participated === false;
            }
            return true;
          });
        }
        images.value = normalized;
      } catch (error: any) {
        try {
          const fallback = await api.get('/images', { params: { per_page: 1000 } });
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
          } else {
            // Exclude rule_card_screenshot from 'all' filter
            normalized = normalized.filter((it: any) => (it?.image_type || 'general') !== 'rule_card_screenshot');
          }
          if (participationFilter.value !== 'all') {
            normalized = normalized.filter((it: any) => {
              const participated = it?.participated || false;
              if (participationFilter.value === 'participated') {
                return participated === true;
              } else if (participationFilter.value === 'not_participated') {
                return participated === false;
              }
              return true;
            });
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
      advertising_rule: '',
      rule_card_screenshot: ''
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
        console.log('[DEBUG] Loaded default locations from backend:', list);
        list.forEach((item: any) => {
          if (item?.image_type && item?.directory) {
            defaultLocations.value[item.image_type] = item.directory;
            console.log(`[DEBUG] Set ${item.image_type} = ${item.directory}`);
          }
        });
        console.log('[DEBUG] Final defaultLocations:', defaultLocations.value);
      } catch (e) {
        console.warn('加载默认目录失败', e);
      }
    };

    const saveDefaultLocations = async () => {
      const types = Object.keys(defaultLocations.value);
      const pending = types.filter(t => defaultLocations.value[t]);
      console.log('[DEBUG] Saving default locations:', pending.map(t => `${t}=${defaultLocations.value[t]}`));
      if (pending.length === 0) {
        message.warning('请填写至少一个目录');
        return;
      }
      const loadingMsg = message.loading('正在保存并加载目录...', { duration: 0 });
      try {
        for (const t of pending) {
          const val = defaultLocations.value[t] || '';
          const isAbs = val.startsWith('/') || /^[A-Za-z]:\\/.test(val);
          console.log(`[DEBUG] Processing ${t}: value="${val}", isAbsolute=${isAbs}`);
          if (isAbs) {
            const response = await api.post('/images/default-location', {
              image_type: t,
              directory: val
            });
            console.log(`[DEBUG] Saved ${t}, response:`, response.data);
          } else {
            console.warn(`[DEBUG] Skipping ${t} because path is not absolute:`, val);
          }
        }
        message.success('默认目录已保存并加载');
        showDefaultDirModal.value = false;
        await loadDefaultLocations();
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
        const isAbs = String(dir).startsWith('/') || /^[A-Za-z]:\\/.test(String(dir));
        if (!isAbs || String(dir).startsWith('browser://')) continue;
        try {
          await api.post('/images/scan-directory', { directory: dir, image_type: type });
        } catch (e) {
          console.warn(`扫描目录失败: ${type} -> ${dir}`, e);
        }
      }
    };

    const selectCurrentFolder = async (type: string) => {
      try {
        if ((window as any).showDirectoryPicker) {
          // Use native directory picker (works on macOS Chrome/Edge)
          const dirHandle = await (window as any).showDirectoryPicker();
          const folderName = dirHandle.name;
          
          // Try to get the full path automatically
          let detectedPath = '';
          
          // Attempt 1: Try to get files and extract path from File object
          try {
            const files: File[] = [];
            let fileCount = 0;
            
            // Get first few files to try to extract path
            for await (const entry of dirHandle.values()) {
              if (entry.kind === 'file' && fileCount < 3) {
                const file = await entry.getFile();
                files.push(file);
                fileCount++;
                
                // Try to get path from file
                if ((file as any).path) {
                  const filePath = (file as any).path;
                  detectedPath = filePath.substring(0, filePath.lastIndexOf('/'));
                  break;
                } else if ((file as any).webkitRelativePath) {
                  // For webkit, we get relative path, need to construct absolute
                  const relativePath = (file as any).webkitRelativePath;
                  console.log('Relative path:', relativePath);
                }
              }
              if (detectedPath) break;
            }
          } catch (e) {
            console.log('Could not auto-detect path:', e);
          }
          
          // If we detected a path automatically, use it
          if (detectedPath) {
            defaultLocations.value[type] = detectedPath;
            message.success(`已自动检测并设置路径: ${detectedPath}`);
          } else {
            // Fallback: Ask user to input manually
            await new Promise<void>((resolve) => {
              let inputValue = '';
              
              dialog.info({
                title: '输入文件夹路径',
                content: () => h('div', { style: 'display: flex; flex-direction: column; gap: 12px;' }, [
                  h('p', { style: 'color: #666;' }, `已选择文件夹: ${folderName}`),
                  h('p', { style: 'font-size: 13px; color: #999;' }, '由于浏览器安全限制，无法自动获取完整路径。'),
                  h('p', { style: 'font-size: 13px; color: #999;' }, '请手动输入该文件夹的绝对路径:'),
                  h(NInput, {
                    placeholder: `/Users/username/path/to/${folderName}`,
                    defaultValue: '',
                    onUpdateValue: (v: string) => { inputValue = v; }
                  }),
                  h('p', { style: 'font-size: 12px; color: #999; margin-top: 8px;' }, '💡 提示: 在Finder中右键点击文件夹，按住Option键，选择"拷贝...的路径名称"')
                ]),
                positiveText: '确定',
                negativeText: '取消',
                onPositiveClick: () => {
                  if (inputValue && inputValue.trim()) {
                    defaultLocations.value[type] = inputValue.trim();
                    message.success(`已设置路径: ${inputValue.trim()}`);
                  }
                  resolve();
                },
                onNegativeClick: () => {
                  resolve();
                },
                onClose: () => {
                  resolve();
                }
              });
            });
          }
        } else {
          // Fallback: show info message
          message.info('您的浏览器不支持文件夹选择，请手动输入服务器绝对路径');
        }
      } catch (e: any) {
        // User cancelled
        if (e.name !== 'AbortError') {
          console.error('选择目录失败:', e);
        }
      }
    };

    // Reset preview state
    const resetPreview = () => {
      previewImageUrl.value = '';
      currentPreviewIndex.value = -1;
      scale.value = 1;
      rotate.value = 0;
      position.value = { x: 0, y: 0 };
      isDragging.value = false;
      dragStart.value = { x: 0, y: 0 };
    };

    // Handle paste from clipboard
    const handlePaste = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;
      
      for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf('image') !== -1) {
          const file = items[i].getAsFile();
          if (file) {
            // Default to general type for pasted images
            handleFileUpload(file, 'general');
            message.success('已粘贴图片，正在上传...');
          }
          break;
        }
      }
    };

    // Handle drag and drop
    const isDropZoneActive = ref(false);
    
    const handleDragOver = (e: DragEvent) => {
      e.preventDefault();
      isDropZoneActive.value = true;
    };
    
    const handleDragLeave = (e: DragEvent) => {
      e.preventDefault();
      isDropZoneActive.value = false;
    };
    
    const handleDrop = (e: DragEvent) => {
      e.preventDefault();
      isDropZoneActive.value = false;
      
      const files = e.dataTransfer?.files;
      if (!files || files.length === 0) return;
      
      // Filter image files
      const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
      
      if (imageFiles.length === 0) {
        message.warning('未检测到图片文件');
        return;
      }
      
      // Store pending files and show type selection modal
      pendingDropFiles.value = imageFiles;
      selectedDropType.value = 'general'; // Default selection
      showDropTypeModal.value = true;
    };
    
    const handleDropTypeConfirm = () => {
      // Upload all dropped image files with selected type
      pendingDropFiles.value.forEach(file => {
        handleFileUpload(file, selectedDropType.value);
      });
      
      message.success(`正在上传 ${pendingDropFiles.value.length} 个图片（${getImageTypeLabel(selectedDropType.value)}）...`);
      
      // Clear pending files
      pendingDropFiles.value = [];
      showDropTypeModal.value = false;
    };
    
    const handleDropTypeCancel = () => {
      pendingDropFiles.value = [];
      showDropTypeModal.value = false;
    };

    // Initial data fetch
    onMounted(() => {
      fetchImages();
      loadBasePaths();
      loadDefaultLocations().then(scanConfiguredDirectories);
      
      // Add paste event listener
      document.addEventListener('paste', handlePaste);
      
      // Add drag-drop listeners to the main content area
      const contentArea = document.querySelector('.content-wrapper');
      if (contentArea) {
        contentArea.addEventListener('dragover', handleDragOver as any);
        contentArea.addEventListener('dragleave', handleDragLeave as any);
        contentArea.addEventListener('drop', handleDrop as any);
      }
      window.addEventListener('keydown', handleKeydown);
    });
    
    // Cleanup event listeners
    const onUnmounted = () => {
      document.removeEventListener('paste', handlePaste);
      const contentArea = document.querySelector('.content-wrapper');
      if (contentArea) {
        contentArea.removeEventListener('dragover', handleDragOver as any);
        contentArea.removeEventListener('dragleave', handleDragLeave as any);
        contentArea.removeEventListener('drop', handleDrop as any);
      }
      window.removeEventListener('keydown', handleKeydown);
    };
    watch(imageTypeFilter, () => {
      fetchImages();
    });
    watch(participationFilter, () => {
      fetchImages();
    });

    // Make sure handleDirectoryUpload is available in the template
    const handleDirectoryUploadWrapper = async (files: FileList, imageType: string) => {
      return handleDirectoryUpload(files, imageType);
    };

    const router = useRouter();
    
    const handleParticipation = (img: ImageItem) => {
      // Navigate to the participation page
      router.push({
        name: 'image-participation',
        params: { id: img.id }
      });
    };
    
    const toggleParticipated = async (img: ImageItem) => {
      try {
        // Check if this is an advertising rule image (matching backend's ImageType.ADVERTISING_RULE.value)
        if (img.image_type !== 'advertising_rule') {
          message.warning('只有广告规则图片可以标记参与状态');
          return;
        }

        // If not already participated, open the participation process
        if (!img.participated) {
          handleParticipation(img);
          return;
        }
        
        // If already participated, show confirmation before unparticipating
        dialog.warning({
          title: '确认取消参与',
          content: '确定要取消参与此图片吗？',
          positiveText: '确定',
          negativeText: '取消',
          onPositiveClick: async () => {
            try {
              await api.post(`/images/participate/${img.id}`, 
                { participated: false },
                { headers: { 'Content-Type': 'application/json' } }
              );
              
              // Update the local state
              images.value = images.value.map(it => 
                it.id === img.id 
                  ? { 
                      ...it, 
                      participated: false,
                      variables: {
                        ...(it.variables || {}),
                        participated: false
                      }
                    } 
                  : it
              );
              
              message.success('已取消参与');
            } catch (e: any) {
              console.error('API Error:', e);
              const errorMessage = e?.response?.data?.message || '操作失败';
              message.error(`取消参与失败: ${errorMessage}`);
            }
          }
        });
      } catch (e) {
        console.error('Unexpected error in toggleParticipated:', e);
        message.error('发生未知错误，请稍后重试');
      }
    };

    const isSelectable = (img: any) => ['general','advertising_campaign'].includes(img?.image_type || '');
    const isSelected = (img: any) => {
      const id = Number(img?.id || -1);
      if ((img?.image_type || '') === 'general') return selectedRegular.value.includes(id);
      if ((img?.image_type || '') === 'advertising_campaign') return selectedEvent.value.includes(id);
      return false;
    };
    const onSelect = (img: any) => {
      const id = Number(img?.id || -1);
      const type = img?.image_type || '';
      if (type === 'general') {
        const idx = selectedRegular.value.indexOf(id);
        if (idx >= 0) selectedRegular.value.splice(idx,1); else selectedRegular.value.push(id);
      } else if (type === 'advertising_campaign') {
        const idx = selectedEvent.value.indexOf(id);
        if (idx >= 0) selectedEvent.value.splice(idx,1); else selectedEvent.value.push(id);
      }
    };
    
    const openParticipationPreview = (img: any) => {
      participationPreviewImage.value = { ...img, tags: img.tags || [] };
      showParticipationPreview.value = true;
    };
    
    const handleTagCreate = (label: string) => {
      return label.trim();
    };
    
    const handlePreviewSelectionToggle = (val: boolean) => {
      // The computed property handles the actual selection logic
    };
    
    const saveParticipationPreviewTags = async () => {
      try {
        const imageId = participationPreviewImage.value.id;
        const tags = participationPreviewImage.value.tags || [];
        
        // Update the image in the main images array
        const imageIndex = images.value.findIndex(img => img.id === imageId);
        if (imageIndex >= 0) {
          images.value[imageIndex].tags = tags;
        }
        
        // Optional: Send to backend to persist tags
        // await api.patch(`/images/${imageId}`, { tags });
        
        message.success('标签已保存');
      } catch (error) {
        message.error('保存标签失败');
      }
    };
    const toggleSelectMode = () => {
      selectMode.value = !selectMode.value;
      // Clear selections when toggling off
      if (!selectMode.value) {
        selectedRegular.value = [];
        selectedEvent.value = [];
      }
    };
    
    // Select all selectable images
    const selectAll = () => {
      selectedRegular.value = [];
      selectedEvent.value = [];
      
      images.value.forEach(img => {
        if (isSelectable(img)) {
          const id = Number(img.id);
          if (img.image_type === 'general') {
            selectedRegular.value.push(id);
          } else if (img.image_type === 'advertising_campaign') {
            selectedEvent.value.push(id);
          }
        }
      });
      
      message.success(`已选择 ${selectedCount.value} 张图片`);
    };
    
    // Show batch status update modal
    const showBatchStatusModal = () => {
      if (!hasSelectedImages.value) {
        message.warning('请先选择要更新状态的图片');
        return;
      }
      
      // Determine which type of images are selected
      const hasRegular = selectedRegular.value.length > 0;
      const hasAd = selectedEvent.value.length > 0;
      
      let statusLabel = '';
      let statusOptions: any[] = [];
      
      // Both general and event images use "已使用/未使用" (used/unused)
      // Only advertising_rule uses "已参与/未参与" (participated/not participated)
      if (hasRegular && hasAd) {
        statusLabel = '状态';
        statusOptions = [
          { label: '已使用', value: 'used' },
          { label: '未使用', value: 'unused' }
        ];
      } else if (hasRegular) {
        statusLabel = '状态 (普通图片)';
        statusOptions = [
          { label: '已使用', value: 'used' },
          { label: '未使用', value: 'unused' }
        ];
      } else if (hasAd) {
        statusLabel = '状态 (活动配图)';
        statusOptions = [
          { label: '已使用', value: 'used' },
          { label: '未使用', value: 'unused' }
        ];
      }
      
      // Use ref for reactive radio selection
      const selectedStatus = ref(statusOptions[0]?.value || '');
      
      dialog.create({
        title: `更新图片状态 (${selectedCount.value} 张)`,
        content: () => h('div', { style: 'padding: 16px 0;' }, [
          h('p', { style: 'margin-bottom: 12px; color: #666;' }, `选择要设置的${statusLabel}:`),
          h(NRadioGroup, {
            value: selectedStatus.value,
            onUpdateValue: (v: string) => { selectedStatus.value = v; }
          }, () => h(NSpace, { vertical: true }, () => statusOptions.map(opt =>
            h(NRadio, { value: opt.value }, () => opt.label)
          )))
        ]),
        positiveText: '确定',
        negativeText: '取消',
        onPositiveClick: async () => {
          await batchUpdateStatus(selectedStatus.value);
        }
      });
    };
    
    // Batch update image status
    const batchUpdateStatus = async (status: string) => {
      const loadingMsg = message.loading(`正在更新 ${selectedCount.value} 张图片状态...`, { duration: 0 });
      try {
        const allSelectedIds = [...selectedRegular.value, ...selectedEvent.value];
        let successCount = 0;
        
        for (const id of allSelectedIds) {
          try {
            const image = images.value.find(img => img.id === id);
            if (!image) continue;
            
            // Determine the appropriate field based on status and image type
            let updateData: any = {};
            if (status === 'used' || status === 'unused') {
              updateData.used = (status === 'used');
            } else if (status === 'participated' || status === 'not_participated') {
              updateData.participated = (status === 'participated');
            }
            
            await api.patch(`/images/${id}`, updateData);
            
            // Update local state
            if (image) {
              Object.assign(image, updateData);
            }
            
            successCount++;
          } catch (e) {
            console.error(`Failed to update image ${id}:`, e);
          }
        }
        
        loadingMsg.destroy();
        
        if (successCount === allSelectedIds.length) {
          message.success(`已成功更新 ${successCount} 张图片状态`);
        } else {
          message.warning(`成功更新 ${successCount} 张，失败 ${allSelectedIds.length - successCount} 张`);
        }
        
        // Clear selections and refresh
        selectedRegular.value = [];
        selectedEvent.value = [];
        selectMode.value = false;
        await fetchImages();
      } catch (error: any) {
        loadingMsg.destroy();
        console.error('Batch status update failed:', error);
        message.error('批量更新状态失败');
      }
    };
    
    // Computed properties for batch delete
    const selectedCount = computed(() => {
      return selectedRegular.value.length + selectedEvent.value.length;
    });
    
    const hasSelectedImages = computed(() => {
      return selectedCount.value > 0;
    });
    
    // Batch delete selected images
    const confirmDeleteSelected = async () => {
      if (!hasSelectedImages.value) {
        message.warning('请先选择要删除的图片');
        return;
      }
      
      dialog.warning({
        title: '确认删除',
        content: `确定要删除选中的 ${selectedCount.value} 张图片吗？此操作不可撤销。`,
        positiveText: '确定删除',
        negativeText: '取消',
        onPositiveClick: async () => {
          const loadingMsg = message.loading(`正在删除 ${selectedCount.value} 张图片...`, { duration: 0 });
          try {
            const allSelectedIds = [...selectedRegular.value, ...selectedEvent.value];
            let successCount = 0;
            const errors: Array<{id: number, error: string}> = [];
            
            for (const id of allSelectedIds) {
              try {
                await api.delete(`/images/delete/${id}`);
                successCount++;
                loadingMsg.content = `正在删除图片 (${successCount}/${allSelectedIds.length})...`;
              } catch (error: any) {
                console.error(`Failed to delete image ${id}:`, error);
                errors.push({
                  id,
                  error: error.response?.data?.message || error.message || '未知错误'
                });
              }
            }
            
            if (errors.length === 0) {
              message.success(`成功删除 ${successCount} 张图片`);
            } else {
              message.warning(`成功删除 ${successCount} 张，失败 ${errors.length} 张`);
            }
            
            // Clear selections and refresh
            selectedRegular.value = [];
            selectedEvent.value = [];
            selectMode.value = false;
            await fetchImages();
          } catch (error: any) {
            console.error('Batch delete failed:', error);
            message.error('删除失败: ' + (error?.response?.data?.message || error?.message || '未知错误'));
          } finally {
            loadingMsg.destroy();
          }
        }
      });
    };
    
    const generateParticipation = async () => {
      const loadingMsg = message.loading('正在生成提示词...', { duration: 0 });
      try {
        const res = await api.post('/prompt/participation', {
          regular_image_ids: selectedRegular.value,
          event_image_ids: selectedEvent.value
        });
        participationPrompt.value = (res?.data?.data?.prompt) || (res?.data?.prompt) || '';
        showPromptModal.value = true;
      } catch (e: any) {
        message.error(e?.response?.data?.message || '生成失败');
      } finally {
        loadingMsg.destroy();
      }
    };
    const onQuickParticipate = async (img: any) => {
      selectedRegular.value = [];
      selectedEvent.value = [];
      const id = Number(img?.id || -1);
      const type = img?.image_type || '';
      if (type === 'general') selectedRegular.value = [id];
      else if (type === 'advertising_campaign') selectedEvent.value = [id];
      await generateParticipation();
    };
    
    // Cleanup orphan images (dirty data with missing files)
    const cleanupOrphanImages = async () => {
      dialog.warning({
        title: '清理脏数据',
        content: '将扫描并删除数据库中指向不存在文件的图片记录（如显示为占位图的条目）。此操作不可撤销，是否继续？',
        positiveText: '扫描并清理',
        negativeText: '取消',
        onPositiveClick: async () => {
          const loadingMsg = message.loading('正在扫描脏数据...', { duration: 0 });
          try {
            // First do a dry run to show count
            const dryRunRes = await api.post('/images/cleanup-orphans', { 
              dry_run: true,
              image_type: imageTypeFilter.value !== 'all' ? imageTypeFilter.value : undefined
            });
            
            const orphanCount = dryRunRes?.data?.data?.orphan_count || 0;
            
            if (orphanCount === 0) {
              loadingMsg.destroy();
              message.success('未发现脏数据');
              return;
            }
            
            loadingMsg.destroy();
            
            // Confirm actual deletion
            dialog.warning({
              title: '确认清理',
              content: `发现 ${orphanCount} 条脏数据记录。确定要删除这些记录吗？`,
              positiveText: `删除 ${orphanCount} 条`,
              negativeText: '取消',
              onPositiveClick: async () => {
                const deleteMsg = message.loading(`正在删除 ${orphanCount} 条脏数据...`, { duration: 0 });
                try {
                  const res = await api.post('/images/cleanup-orphans', { 
                    dry_run: false,
                    image_type: imageTypeFilter.value !== 'all' ? imageTypeFilter.value : undefined
                  });
                  
                  const deletedCount = res?.data?.data?.deleted_count || 0;
                  message.success(`已清理 ${deletedCount} 条脏数据`);
                  
                  // Refresh image list
                  await fetchImages();
                } catch (e: any) {
                  message.error('清理失败: ' + (e?.response?.data?.message || e?.message || '未知错误'));
                } finally {
                  deleteMsg.destroy();
                }
              }
            });
          } catch (e: any) {
            loadingMsg.destroy();
            message.error('扫描失败: ' + (e?.response?.data?.message || e?.message || '未知错误'));
          }
        }
      });
    };

    return {
      // State
      viewMode,
      showPreview,
      showDefaultDirModal,
      showUploadMenu,
      showDropTypeModal,
      previewImageUrl,
      currentPreviewIndex,
      images,
      pendingDropFiles,
      selectedDropType,
      navigatePreview,
      loading,
      imageTypeFilter,
      imageTypeOptions,
      participationFilter,
      participationOptions,
      selectMode,
      showPromptModal,
      participationPrompt,
      selectedRegular,
      selectedEvent,
      showParticipationPreview,
      participationPreviewImage,
      participationPreviewTitle,
      participationPreviewSelected,
      tagInputRef,
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
      isDropZoneActive,
      
      // Methods
      toggleParticipated,
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
      confirmDeleteSelected,
      cleanupOrphanImages,
      selectedCount,
      hasSelectedImages,
      toggleSelectMode,
      selectAll,
      showBatchStatusModal,
      handleUploadSelect,
      handleTagCreate,
      handlePreviewSelectionToggle,
      saveParticipationPreviewTags,
      openParticipationPreview,
      isSelectable,
      isSelected,
      onSelect,
      handleDirectoryUpload: handleDirectoryUploadWrapper,
      handleDropTypeConfirm,
      handleDropTypeCancel,
      downloadImage,
      resetPreview,
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
      ChevronBack,
      ChevronForward,
      DownloadOutline,
      Close: CloseOutline,
      SearchOutline,
      RefreshOutline,
      AddOutline,
      RemoveOutline,
      GridOutline,
      ListOutline,
      TrashOutline,
      ImagesOutline,
      MegaphoneOutline,
      DocumentTextOutline,
      
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
      NModal,
      NForm,
      NFormItem,
      NSwitch,
      NDivider,
      NDynamicTags
    };
  },
});
</script>

<style scoped>
/* Drop Zone Overlay */
.drop-zone-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(24, 160, 88, 0.15);
  backdrop-filter: blur(4px);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.drop-zone-content {
  background: white;
  border: 3px dashed var(--n-color-target);
  border-radius: 16px;
  padding: 48px 64px;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.drop-zone-content .n-icon {
  color: var(--n-color-target);
  margin-bottom: 16px;
}

.drop-zone-content p {
  margin: 8px 0;
  font-size: 18px;
  font-weight: 500;
  color: #333;
}

.drop-zone-content .hint {
  font-size: 14px;
  font-weight: 400;
  color: #666;
  margin-top: 12px;
}

/* Participation Preview Modal */
.participation-preview-content {
  padding: 16px 0;
}

.preview-image-wrapper {
  width: 100%;
  max-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  border-radius: 8px;
  overflow: hidden;
}

.large-preview-image {
  max-width: 100%;
  max-height: 400px;
  object-fit: contain;
  border-radius: 4px;
}

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
  width: auto;
  height: auto;
  max-width: 90vw;
  max-height: calc(90vh - 120px);
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
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 12px;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 28px;
  backdrop-filter: blur(12px);
  z-index: 100;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.1);
  opacity: 0.92;
  transition: all 0.3s ease;
}

.preview-controls:hover {
  opacity: 1;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.2);
  transform: translateX(-50%) translateY(-4px);
}

.preview-controls .n-button {
  transition: all 0.2s ease;
  min-width: 40px;
  height: 40px;
}

.preview-controls .n-button:not(:disabled):hover {
  transform: scale(1.1);
}

.preview-controls .n-button:active {
  transform: scale(0.95);
}

/* Always show controls with slight fade-in animation */
.preview-content .preview-controls {
  animation: slideUpFadeIn 0.4s ease-out;
}

@keyframes slideUpFadeIn {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(20px);
  }
  to {
    opacity: 0.92;
    transform: translateX(-50%) translateY(0);
  }
}

/* Navigation Arrows */
.nav-arrow {
  position: fixed;
  top: 50%;
  transform: translateY(-50%);
  z-index: 1002;
  opacity: 0.7;
  transition: all 0.3s ease;
  background: rgba(0, 0, 0, 0.5) !important;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
}

.nav-arrow:hover {
  opacity: 1;
  transform: translateY(-50%) scale(1.1);
  background: rgba(0, 0, 0, 0.7) !important;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.nav-arrow:active {
  transform: translateY(-50%) scale(0.95);
}

.nav-arrow-left {
  left: 20px;
}

.nav-arrow-right {
  right: 20px;
}

.control-section {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-label {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  white-space: nowrap;
  user-select: none;
}

.control-divider {
  width: 1px;
  height: 24px;
  background: linear-gradient(to bottom, transparent, rgba(0, 0, 0, 0.15), transparent);
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
  
  .nav-arrow {
    opacity: 0.8;
  }
  
  .nav-arrow-left {
    left: 10px;
  }
  
  .nav-arrow-right {
    right: 10px;
  }
}

@media (max-width: 480px) {
  .nav-arrow {
    width: 44px !important;
    height: 44px !important;
    opacity: 0.85;
  }
  
  .nav-arrow-left {
    left: 8px;
  }
  
  .nav-arrow-right {
    right: 8px;
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

/* Grid View - Full width grid - Large images for maximum detail */
.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
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

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  margin-bottom: 16px;
}

.header-actions-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.header-actions-right {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
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

.participation-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.counts { color: #888; }
.image-preview-container {
  position: relative;
}

.preview-btn {
  position: absolute !important;
  top: 8px;
  right: 8px;
  z-index: 10;
  opacity: 0;
  transition: opacity 0.2s;
}

.image-preview-container:hover .preview-btn {
  opacity: 1;
}
.list-image-container { position: relative; }
.prompt-content { white-space: pre-wrap; line-height: 1.6; }

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-color);
  margin: 0 0 16px 0;
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
  justify-content: space-between;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

.actions-left {
  display: flex;
  gap: 6px;
  align-items: center;
}

.actions-right {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-left: auto;
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

/* Responsive adjustments for tablets and mobile */
@media (max-width: 1024px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .view-options {
    margin-left: 0;
    width: 100%;
    justify-content: flex-start;
  }
}

@media (max-width: 768px) {
  .page-title {
    font-size: 20px;
  }
  
  .image-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 12px;
    padding: 8px;
  }
  
  .image-preview {
    height: 200px;
  }
  
  .image-info {
    padding: 6px 8px 8px;
  }
  
  .image-name {
    font-size: 12px;
  }
  
  .image-meta {
    font-size: 11px;
  }
  
  .list-image-preview {
    width: 50px;
    height: 50px;
  }
  
  /* Make controls touch-friendly */
  .n-button {
    min-height: 44px !important;
  }
  
  /* Modal adjustments */
  .default-dir-form .form-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .default-dir-form .form-label {
    width: 100%;
    margin-bottom: 4px;
  }
  
  /* Preview modal adjustments */
  .simple-preview-controls {
    flex-wrap: wrap;
    gap: 12px;
  }
}

/* Extra small devices (phones in portrait) */
@media (max-width: 480px) {
  .content-wrapper {
    padding: 8px;
  }
  
  .page-title {
    font-size: 18px;
  }
  
  .image-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    padding: 4px;
  }
  
  .image-preview {
    height: 150px;
  }
  
  .image-actions {
    flex-wrap: wrap;
  }
  
  .filters-section {
    flex-direction: column;
    gap: 8px;
  }
  
  .filter-group {
    width: 100%;
  }
}
</style>
