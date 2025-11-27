<template>
  <div class="participation-process">
    <!-- Step 1: Select Regular Images -->
    <div v-if="step === 1" class="step-container">
      <h2>步骤 1: 选择普通图片 ({{ unusedRegularImages.length }})</h2>
      <n-card class="image-card">
        <div class="image-grid-container" v-if="unusedRegularImages.length > 0">
          <div class="image-grid">
            <div
              v-for="image in unusedRegularImages"
              :key="image.id"
              class="image-item"
              :class="{ selected: selectedRegularImagesSet.has(image.id) }"
              @click="toggleRegularImage(image.id)"
            >
              <img 
                :data-src="getImageUrl(image)" 
                :alt="image.filename" 
                class="preview-image lazy-image"
                loading="lazy"
              />
              <div class="image-info">
                <div class="image-info-top">
                  <span class="image-name">{{ image.filename }}</span>
                  <n-tag size="small">普通图片</n-tag>
                </div>
                <!-- Edit button at bottom -->
                <n-button 
                  class="image-edit-btn" 
                  size="small" 
                  type="primary"
                  ghost
                  block
                  @click.stop="openImagePreview(image)"
                >
                  <template #icon>
                    <n-icon><eye-outline /></n-icon>
                  </template>
                  预览编辑
                </n-button>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <div class="empty-icon">
            <n-icon size="48" color="#999">
              <image-outline />
            </n-icon>
          </div>
          <div class="empty-text">
            <p class="empty-title">暂无可用普通图片</p>
            <p class="empty-description">所有普通图片已被使用，请上传新图片或重置已使用的图片</p>
          </div>
        </div>
      </n-card>
      <div class="step-actions">
        <n-button type="primary" :disabled="selectedRegularImagesSet.size === 0" @click="nextStep">
          下一步
          <template #icon>
            <n-icon><arrow-forward /></n-icon>
          </template>
        </n-button>
      </div>
    </div>

    <!-- Step 2: Select Advertisement Images -->
    <div v-else-if="step === 2" class="step-container">
      <div class="step-header">
        <h2>步骤 2: 选择活动图片 ({{ advertisementImages.length }})</h2>
        <div style="display: flex; gap: 8px;">
          <n-button secondary @click="toggleDebugPanel" size="small">
            {{ showDebugPanel ? '隐藏调试' : '显示调试' }}
          </n-button>
          <n-button secondary @click="testAddImage" size="small" type="warning">
            测试添加
          </n-button>
          <n-button secondary @click="forceReloadImages" size="small" :loading="isReloading">
            <template #icon>
              <n-icon><arrow-forward /></n-icon>
            </template>
            {{ isReloading ? '正在刷新...' : '刷新列表' }}
          </n-button>
        </div>
      </div>
      
      <!-- DEBUG PANEL -->
      <div v-if="showDebugPanel" class="debug-panel">
        <h3>🔍 调试信息</h3>
        <div class="debug-item">
          <strong>API 返回总数:</strong> {{ debugInfo.totalImages }}
        </div>
        <div class="debug-item">
          <strong>活动图片数量:</strong> {{ debugInfo.adImages }}
        </div>
        <div class="debug-item">
          <strong>常规图片数量:</strong> {{ debugInfo.generalImages }}
        </div>
        <div class="debug-item">
          <strong>最后更新时间:</strong> {{ debugInfo.lastUpdate }}
        </div>
        <div v-if="debugInfo.warning" class="debug-warning">
          ⚠️ {{ debugInfo.warning }}
        </div>
        <div class="debug-item">
          <strong>所有活动图片:</strong>
          <div v-for="img in advertisementImages" :key="img.id" style="margin-left: 16px; font-size: 12px;">
            • ID: {{ img.id }} - {{ img.filename }} [{{ img.image_type }}]
          </div>
        </div>
      </div>
      <n-card title="活动图片" class="image-card" :key="'ad-grid-' + renderKey">
        <div v-if="advertisementImages.length === 0" class="empty-state">
          <div class="empty-icon">
            <n-icon size="48" color="#999">
              <image-outline />
            </n-icon>
          </div>
          <div class="empty-text">
            <p class="empty-title">暂无活动图片</p>
            <p class="empty-description">请点击下方按钮添加活动图片</p>
          </div>
        </div>
        <div v-else class="image-grid-container">
          <div class="image-grid">
          <div
            v-for="image in advertisementImages"
            :key="image.id"
            class="image-item"
            :class="{ selected: isAdImageSelected(image.id) }"
            @click="toggleAdvertisementImage(image.id)"
          >
            <img 
              :src="getImageUrl(image)" 
              :alt="image.filename" 
              class="preview-image"
              loading="lazy"
              @error="handleImageError"
            />
            <div class="image-info">
              <span class="image-name">{{ image.filename }}</span>
              <n-tag type="warning" size="small">活动图片</n-tag>
            </div>
          </div>
        </div>
        </div>
        <div class="add-image-action">
          <n-button type="primary" @click="showAddAdvertisementModal = true">
            <template #icon>
              <n-icon><add /></n-icon>
            </template>
            添加活动图片
          </n-button>
        </div>
      </n-card>
      <div class="step-actions">
        <n-button @click="prevStep">
          <template #icon>
            <n-icon><arrow-back /></n-icon>
          </template>
          上一步
        </n-button>
        <n-button type="primary" @click="nextStep">
          下一步
          <template #icon>
            <n-icon><arrow-forward /></n-icon>
          </template>
        </n-button>
      </div>

      <!-- Add Advertisement Image Modal -->
      <n-modal 
        v-model:show="showAddAdvertisementModal" 
        preset="card" 
        title="添加活动图片" 
        :mask-closable="true" 
        @after-enter="focusPasteDiv"
        @after-leave="handleModalClose"
      >
        <template #header-extra>
          <n-button text @click="showAddAdvertisementModal = false">
            <template #icon>
              <n-icon><close-circle /></n-icon>
            </template>
          </n-button>
        </template>
        <div ref="pasteDiv" @paste="handleClipboardPaste" @keydown="handleKeyDown" tabindex="0" class="paste-container">
          <n-upload
            action="/api/images/upload"
            :data="{ image_type: 'advertising_campaign' }"
            @finish="handleUploadFinish"
            accept="image/*"
            class="upload-component"
          >
            <n-button type="primary" size="large" class="upload-button">
              <template #icon>
                <n-icon><upload-cloud /></n-icon>
              </template>
              上传活动图片
            </n-button>
          </n-upload>
          <div class="paste-divider">
            <span class="divider-text">或</span>
          </div>
          <div 
            class="paste-area" 
            :class="{ 'paste-area-active': isPasteAreaActive, 'paste-area-focused': pasteAreaFocused }"
            @click="handlePasteAreaClick"
            @focus="pasteAreaFocused = true"
            @blur="pasteAreaFocused = false"
          >
            <div class="paste-icon">
              <n-icon size="48" color="#165dff">
                <clipboard-outline />
              </n-icon>
            </div>
            <div class="paste-instructions">
              <h3>粘贴图片</h3>
              <p v-if="!pasteAreaFocused" class="click-hint"><strong>👆 点击此区域</strong>，然后按 Ctrl+V 或 Cmd+V</p>
              <p v-else class="paste-ready">✅ 已激活！现在可以粘贴图片</p>
              <p class="paste-hint">支持同时粘贴多张图片 (PNG, JPG, GIF, WebP, BMP)</p>
            </div>
          </div>
          
          <!-- Pasted Images Preview -->
          <div v-if="showPastePreview && pastedImages.length > 0" class="pasted-images-preview">
            <div class="preview-header">
              <h4>粘贴的图片 ({{ pastedImages.length }})</h4>
              <span v-if="uploadingCount > 0" class="uploading-indicator">
                正在上传... ({{ pastedImages.length - uploadingCount }}/{{ pastedImages.length }})
              </span>
            </div>
            <div class="preview-grid">
              <div
                v-for="(img, index) in pastedImages"
                :key="index"
                class="preview-item"
                :class="`status-${img.status}`"
              >
                <div class="preview-image-container">
                  <img :src="img.preview" :alt="img.name" class="preview-image" />
                  <div v-if="img.status === 'uploading'" class="upload-overlay">
                    <n-icon size="24" class="loading-icon">
                      <upload-cloud />
                    </n-icon>
                  </div>
                  <div v-if="img.status === 'success'" class="success-overlay">
                    <n-icon size="24" color="#52c41a">
                      <checkmark-circle />
                    </n-icon>
                  </div>
                  <div v-if="img.status === 'error'" class="error-overlay">
                    <n-icon size="24" color="#ff4d4f">
                      <close-circle />
                    </n-icon>
                  </div>
                </div>
                <div class="preview-info">
                  <span class="preview-name">{{ img.name }}</span>
                  <span v-if="img.status === 'error'" class="error-message">{{ img.error }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <template #footer>
          <div class="modal-footer-actions">
            <n-button @click="showAddAdvertisementModal = false">
              取消
            </n-button>
            <n-button type="primary" @click="showAddAdvertisementModal = false">
              完成
            </n-button>
          </div>
        </template>
      </n-modal>
    </div>

    <!-- Step 3: Write Prompt -->
    <div v-else-if="step === 3" class="step-container">
      <h2>步骤 3: 生成文案</h2>
      <n-card title="文案生成配置" class="prompt-card">
        <n-alert
          v-if="selectedRuleImageIds.length > 0"
          type="info"
          show-icon
          style="margin-bottom: 16px;"
        >
          已关联 {{ selectedRuleImageIds.length }} 张广告规则图片（ID: {{ selectedRuleImageIds.join(', ') }}），生成时会自动附带。
        </n-alert>
        <n-form :model="formData" :rules="rules">
          <n-form-item label="选择模板" path="selectedTemplate">
            <n-select
              v-model:value="selectedTemplate"
              :options="promptTemplateOptions"
              placeholder="选择一个提示词模板（可选）"
              clearable
              @update:value="applyTemplate"
            >
              <template #empty>
                <div style="padding: 12px; text-align: center; color: #999;">
                  <p>暂无可用模板</p>
                  <p style="font-size: 12px; margin-top: 4px;">
                    请在 <router-link to="/prompt-templates" style="color: #165dff;">提示词模板</router-link> 页面创建模板
                  </p>
                </div>
              </template>
            </n-select>
          </n-form-item>

          <n-form-item label="LLM 模型" path="llmModel">
            <n-select
              v-model:value="formData.llmModel"
              :options="llmModelOptions"
              placeholder="请选择 LLM 模型"
              :disabled="llmModelOptions.length === 0"
            />
            <template #feedback v-if="llmModelOptions.length === 0">
              <n-alert type="warning" style="margin-top: 8px;" :showIcon="true">
                暂无已连接的 LLM 模型。请先在 <router-link to="/llm-models" style="color: #f0a020; text-decoration: underline;">LLM 模型管理</router-link> 中配置模型。
              </n-alert>
            </template>
          </n-form-item>

          <n-form-item label="自定义提示词" path="customPrompt">
            <n-input
              v-model:value="formData.customPrompt"
              type="textarea"
              :autosize="{ minRows: 5 }"
              placeholder="请输入自定义提示词..."
            />
          </n-form-item>
        </n-form>
        
        <!-- Preview Info Summary -->
        <div v-if="previewPromptData" class="preview-info-summary">
          <n-alert type="info" :show-icon="true">
            <div style="font-size: 13px;">
              <div style="font-weight: 600; margin-bottom: 8px;">🔍 准备生成的内容预览</div>
              <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                <n-tag type="primary" size="small">普通图片: {{ previewPromptData.regular_images }} 张</n-tag>
                <n-tag type="success" size="small">活动图片: {{ previewPromptData.event_images }} 张</n-tag>
                <n-tag type="info" size="small">模型: {{ previewPromptData.model }}</n-tag>
              </div>
            </div>
          </n-alert>
        </div>
      </n-card>
      <div class="step-actions">
        <n-button @click="prevStep">
          <template #icon>
            <n-icon><arrow-back /></n-icon>
          </template>
          上一步
        </n-button>
        <n-button type="primary" @click="confirmAndGenerate" :loading="generating">
          <template #icon>
            <n-icon><sparkles /></n-icon>
          </template>
          {{ generating ? '生成中...' : '生成文案' }}
        </n-button>
      </div>
    </div>

    <!-- Step 4: Preview & Confirm -->
    <div v-else-if="step === 4" class="step-container">
      <h2>步骤 4: 确认发布内容</h2>
      <n-card title="内容预览" class="preview-card">
        <!-- Data Summary -->
        <n-alert type="success" style="margin-bottom: 16px;" :show-icon="true">
          <div style="font-size: 13px;">
            <div style="font-weight: 600; margin-bottom: 8px;">✅ 文案生成完成</div>
            <div style="display: flex; gap: 12px; flex-wrap: wrap;">
              <n-tag type="primary" size="small">普通图片: {{ selectedRegularImagesSet.size }} 张</n-tag>
              <n-tag type="success" size="small">活动图片: {{ selectedAdvertisementImagesSet.size }} 张</n-tag>
              <n-tag type="info" size="small">总计: {{ selectedRegularImagesSet.size + selectedAdvertisementImagesSet.size }} 张</n-tag>
              <n-tag type="warning" size="small">模型: {{ previewPromptData?.model }}</n-tag>
            </div>
          </div>
        </n-alert>

        <!-- Selected Images Preview -->
        <div class="preview-section">
          <h3>📷 已选图片</h3>
          <div class="image-grid-preview">
            <div 
              v-for="img in getSelectedImages().slice(0, 9)"
              :key="img.id"
              class="preview-image-item"
            >
              <img :src="getImageUrl(img)" :alt="img.filename" />
            </div>
            <div v-if="selectedRegularImagesSet.size + selectedAdvertisementImagesSet.size > 9" class="preview-more">
              +{{ selectedRegularImagesSet.size + selectedAdvertisementImagesSet.size - 9 }}
            </div>
          </div>
        </div>

        <!-- Generated Text -->
        <div class="preview-section">
          <h3>📝 生成的文案</h3>
          <n-input
            v-model:value="generatedPrompt"
            type="textarea"
            :autosize="{ minRows: 8, maxRows: 20 }"
            placeholder="生成的文案将显示在这里..."
            class="generated-text-editor"
          />
        </div>

        <!-- Task Info (if available) -->
        <div class="preview-section" v-if="previewPromptData?.task_info">
          <h3>📋 任务信息</h3>
          <div class="task-info-preview">
            <div v-if="previewPromptData.task_info.task_title"><strong>任务标题:</strong> {{ previewPromptData.task_info.task_title }}</div>
            <div v-if="previewPromptData.task_info.hashtags"><strong>话题标签:</strong> <span style="color: #ff2442;">{{ previewPromptData.task_info.hashtags }}</span></div>
            <div v-if="previewPromptData.task_info.tag_require"><strong>标签要求:</strong> {{ previewPromptData.task_info.tag_require }}</div>
            <div v-if="previewPromptData.task_info.submission_rules"><strong>提交规则:</strong> {{ previewPromptData.task_info.submission_rules }}</div>
          </div>
        </div>
      </n-card>

      <div class="step-actions">
        <n-button @click="prevStep">
          <template #icon>
            <n-icon><arrow-back /></n-icon>
          </template>
          返回修改
        </n-button>
        <n-space>
          <n-button @click="copyGeneratedPrompt">
            <template #icon>
              <n-icon><copy /></n-icon>
            </template>
            复制文案
          </n-button>
          <n-button type="primary" :loading="posting" @click="publishPost">
            <template #icon>
              <n-icon><checkmark-circle /></n-icon>
            </template>
            {{ posting ? '发布中...' : '发布到小红书' }}
          </n-button>
          <n-button type="success" @click="step = 1">
            完成
          </n-button>
        </n-space>
      </div>
    </div>

    <!-- Preview Prompt Modal -->
    <n-modal 
        v-model:show="showPreviewPromptModal" 
        preset="card" 
        title="🔍 预览提示词" 
        :style="{ width: '900px' }"
        :mask-closable="false"
      >
        <div v-if="previewPromptData" class="preview-prompt-content">
          <n-alert type="info" style="margin-bottom: 16px;" :show-icon="true">
            即将使用以下内容生成文案，请确认无误后点击"确认生成"
          </n-alert>
          
          <div class="preview-section">
            <div class="preview-label">📊 数据统计</div>
            <n-space>
              <n-tag type="primary">普通图片: {{ previewPromptData.regular_images }} 张</n-tag>
              <n-tag type="success">活动图片: {{ previewPromptData.event_images }} 张</n-tag>
              <n-tag type="warning" v-if="previewPromptData.rule_images > 0">规则图片: {{ previewPromptData.rule_images }} 张</n-tag>
            </n-space>
          </div>
          
          <div class="preview-section">
            <div class="preview-label">🤖 LLM 模型</div>
            <n-tag type="info">{{ previewPromptData.model }}</n-tag>
          </div>
          
          <div class="preview-section" v-if="previewPromptData.task_info">
            <div class="preview-label">📋 任务信息</div>
            <div style="padding: 12px; background: #f5f5f5; border-radius: 6px; font-size: 13px; line-height: 1.8;">
              <div v-if="previewPromptData.task_info.task_title"><strong>任务标题:</strong> {{ previewPromptData.task_info.task_title }}</div>
              <div v-if="previewPromptData.task_info.hashtags"><strong>话题标签:</strong> {{ previewPromptData.task_info.hashtags }}</div>
              <div v-if="previewPromptData.task_info.tag_require"><strong>标签要求:</strong> {{ previewPromptData.task_info.tag_require }}</div>
              <div v-if="previewPromptData.task_info.submission_rules"><strong>提交规则:</strong> {{ previewPromptData.task_info.submission_rules }}</div>
            </div>
          </div>
          
          <div class="preview-section">
            <div class="preview-label">💬 自定义提示词</div>
            <n-input
              :value="previewPromptData.custom_prompt"
              type="textarea"
              :autosize="{ minRows: 8, maxRows: 15 }"
              readonly
              style="font-family: 'Monaco', 'Menlo', monospace; font-size: 13px;"
            />
          </div>
        </div>
        
        <template #footer>
          <n-space justify="end">
            <n-button @click="cancelPreview">取消</n-button>
            <n-button type="primary" :loading="generating" @click="confirmAndGenerate">
              <template #icon>
                <n-icon><sparkles /></n-icon>
              </template>
              确认生成
            </n-button>
          </n-space>
        </template>
    </n-modal>

    <!-- Generated Prompt Modal -->
    <n-modal v-model:show="showGeneratedPromptModal" preset="card" title="生成的文案" :mask-closable="true">
        <div class="generated-prompt">
          <n-input
            v-model:value="generatedPrompt"
            type="textarea"
            :autosize="{ minRows: 10 }"
            readonly
          />
        </div>
        <div class="modal-actions">
          <n-button @click="showGeneratedPromptModal = false">关闭</n-button>
          <n-button type="primary" @click="copyGeneratedPrompt">
            <template #icon>
              <n-icon><copy /></n-icon>
            </template>
            复制
          </n-button>
        </div>
    </n-modal>
    
    <!-- Full-Screen Image Preview Modal -->
    <n-modal 
      v-model:show="showImagePreviewModal" 
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
            @click="showImagePreviewModal = false"
            aria-label="关闭预览"
          >
            <template #icon>
              <n-icon :component="CloseOutline" size="24" />
            </template>
          </n-button>
        </div>
      </template>
      <div class="preview-content" @click.self="showImagePreviewModal = false">
        <!-- Navigation Arrows -->
        <n-button
          v-if="unusedRegularImages.length > 1"
          class="nav-arrow nav-arrow-left"
          circle
          size="large"
          type="primary"
          ghost
          @click.stop="navigatePreview('prev')"
        >
          <template #icon>
            <n-icon size="28"><arrow-back /></n-icon>
          </template>
        </n-button>
        
        <n-button
          v-if="unusedRegularImages.length > 1"
          class="nav-arrow nav-arrow-right"
          circle
          size="large"
          type="primary"
          ghost
          @click.stop="navigatePreview('next')"
        >
          <template #icon>
            <n-icon size="28"><arrow-forward /></n-icon>
          </template>
        </n-button>
        
        <div class="image-container">
          <template v-if="previewImage">
            <div class="image-wrapper">
              <img 
                :src="getImageUrl(previewImage)" 
                :alt="previewImage.filename" 
                class="preview-image" 
                :style="previewImageStyle"
                @click.stop
                @mousedown="startDragPreview"
                @mousemove="handleDragPreview"
                @mouseup="endDragPreview"
                @mouseleave="endDragPreview"
                @wheel.prevent="handleWheelPreview"
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
              <n-button @click="zoomOut" :disabled="imageZoom <= 0.5" size="small">
                <template #icon>
                  <n-icon><remove-outline /></n-icon>
                </template>
              </n-button>
              <n-button @click="resetZoom" size="small" strong>
                {{ Math.round(imageZoom * 100) }}%
              </n-button>
              <n-button @click="zoomIn" :disabled="imageZoom >= 3" size="small">
                <template #icon>
                  <n-icon><add-outline /></n-icon>
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
                  <n-icon><sync-outline /></n-icon>
                </template>
              </n-button>
              <n-button @click="rotateRight" size="small">
                <template #icon>
                  <n-icon><sync-outline style="transform: scaleX(-1);" /></n-icon>
                </template>
              </n-button>
            </n-button-group>
          </div>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, reactive, onMounted, onActivated, watch, computed, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { ArrowBack, ArrowForward, Add, CloudUploadOutline as UploadCloud, Sparkles, Copy, ClipboardOutline, ImageOutline, CheckmarkCircle, CloseCircle, CloseOutline, EyeOutline, ResizeOutline, SyncOutline, RemoveOutline, AddOutline, ExpandOutline } from '@vicons/ionicons5';
import { NModal, NCard, NButton, NIcon, NTag, NUpload, NForm, NFormItem, NInput, NSelect, NAlert, NDivider, NDynamicTags, NButtonGroup } from 'naive-ui';
import { useMessage } from 'naive-ui';
import { listImages } from '@/api/functions';

interface ImageItem {
  id: number;
  filename: string;
  file_path: string;
  source: string;
  image_type: string;
  participated: boolean;
  used?: boolean;
  created_at: string;
  variables?: Record<string, any>;
  tags?: string[];
  note?: string;
}

interface FormData {
  customPrompt: string;
  llmModel: string;
}

// Environment check for debug logging
const isDev = import.meta.env.DEV;

export default defineComponent({
  name: 'ParticipationProcess',
  props: {
    initialRuleImageId: {
      type: [Number, String],
      default: null,
    },
    advertisementTaskId: {
      type: [Number, String],
      default: null,
    },
    ruleCardId: {
      type: [Number, String],
      default: null,
    },
  },
  components: {
    ArrowBack,
    ArrowForward,
    Add,
    UploadCloud,
    Sparkles,
    Copy,
    ClipboardOutline,
    ImageOutline,
    CheckmarkCircle,
    CloseCircle,
    CloseOutline,
    EyeOutline,
    ResizeOutline,
    SyncOutline,
    RemoveOutline,
    AddOutline,
    ExpandOutline,
    NModal,
    NCard,
    NButton,
    NIcon,
    NTag,
    NUpload,
    NForm,
    NFormItem,
    NInput,
    NSelect,
    NAlert,
    NDivider,
    NDynamicTags,
    NButtonGroup,
  },
  setup(props) {
    const message = useMessage();
    const router = useRouter();
    const step = ref(1);
    // Use Set for O(1) lookups instead of Array O(n)
    const selectedRegularImagesSet = ref(new Set<number>());
    const selectedAdvertisementImagesSet = ref(new Set<number>());
    const selectedRuleImagesSet = ref(new Set<number>());
    
    // Trigger for forcing reactivity updates on Set changes
    const selectionVersion = ref(0);
    
    // Helper function to check if an advertisement image is selected (reactive)
    const isAdImageSelected = (imageId: number): boolean => {
      // Access selectionVersion to create reactivity dependency
      void selectionVersion.value;
      return selectedAdvertisementImagesSet.value.has(imageId);
    };
    const unusedRegularImages = ref<ImageItem[]>([]);
    const advertisementImages = ref<ImageItem[]>([]);
    const showAddAdvertisementModal = ref(false);
    const showGeneratedPromptModal = ref(false);
    const showPreviewPromptModal = ref(false);
    const generatedPrompt = ref('');
    const previewPromptData = ref<any>(null);
    const generating = ref(false);
    const posting = ref(false);
    const isPasteAreaActive = ref(false);
    const pasteAreaFocused = ref(false);
    const pasteDiv = ref<HTMLElement | null>(null);
    
    // Advertisement task support
    const advertisementTask = ref<any>(null);
    const selectedRuleCard = ref<any>(null);  // Selected rule card with its own tags
    const loadingTask = ref(false);
    
    // Clipboard pasting enhancement
    const pastedImages = ref<Array<{ preview: string; name: string; status: 'pending' | 'uploading' | 'success' | 'error'; error?: string }>>([]);
    const uploadingCount = ref(0);
    const showPastePreview = ref(false);
    const isReloading = ref(false);
    const showDebugPanel = ref(false);
    const renderKey = ref(0);
    
    // Image preview modal state
    const showImagePreviewModal = ref(false);
    const previewImage = ref<ImageItem | null>(null);
    const currentPreviewIndex = ref(-1);
    const stickerCategory = ref('emoji');
    const imageStickers = ref<any[]>([]); // Stickers placed on the image
    const imageCanvas = ref<HTMLElement | null>(null);
    const imageZoom = ref(1);
    const imageRotation = ref(0);
    const previewPosition = ref({ x: 0, y: 0 });
    const isPreviewDragging = ref(false);
    const previewDragStart = ref({ x: 0, y: 0 });
    
    // Interaction state
    const dragState = reactive({
      isDragging: false,
      isResizing: false,
      isRotating: false,
      activeIndex: -1,
      startX: 0,
      startY: 0,
      startScale: 1,
      startRotation: 0,
      centerX: 0,
      centerY: 0
    });
    
    // Available stickers by category
    const stickerLibrary = {
      emoji: [
        { id: 'e1', name: '笑脸', icon: '😊', category: 'emoji' },
        { id: 'e2', name: '心形', icon: '❤️', category: 'emoji' },
        { id: 'e3', name: '星星', icon: '⭐', category: 'emoji' },
        { id: 'e4', name: '闪光', icon: '✨', category: 'emoji' },
        { id: 'e5', name: '花朵', icon: '🌸', category: 'emoji' },
        { id: 'e6', name: '蝴蝶', icon: '🦋', category: 'emoji' },
      ],
      shapes: [
        { id: 's1', name: '圆形', icon: '⭕', category: 'shapes' },
        { id: 's2', name: '方形', icon: '⬛', category: 'shapes' },
        { id: 's3', name: '三角', icon: '🔺', category: 'shapes' },
        { id: 's4', name: '爱心', icon: '💗', category: 'shapes' },
      ],
      effects: [
        { id: 'f1', name: '光晕', icon: '🌟', category: 'effects' },
        { id: 'f2', name: '火花', icon: '💥', category: 'effects' },
        { id: 'f3', name: '魔法', icon: '🪄', category: 'effects' },
        { id: 'f4', name: '云朵', icon: '☁️', category: 'effects' },
      ]
    };
    const debugInfo = reactive({
      totalImages: 0,
      adImages: 0,
      generalImages: 0,
      lastUpdate: '',
      warning: ''
    });
    
    // Memoize image URLs
    const imageUrlCache = new Map<number, string>();

    // Upload configuration
    const uploadUrl = '/api/images/upload';

    const formData = reactive<FormData>({
      customPrompt: '',
      llmModel: '',
    });

    const rules = {
      customPrompt: { required: true, message: '请输入自定义提示词', trigger: 'blur' },
    };


    // Dynamic LLM model options (loaded from LLM Models tab)
    const llmModelOptions = ref<Array<{ label: string; value: string }>>([]);
    
    // Prompt template options
    const promptTemplateOptions = ref<Array<{ label: string; value: string }>>([]);
    const selectedTemplate = ref<string | null>(null);
    const promptTemplates = ref<Array<any>>([]);

    // Load prompt templates from localStorage (same as PromptTemplates.vue)
    const loadPromptTemplates = () => {
      try {
        const STORAGE_KEY = 'prompt_templates';
        const data = localStorage.getItem(STORAGE_KEY);
        if (data) {
          const templates = JSON.parse(data);
          promptTemplates.value = templates;
          
          // Create options for the select dropdown
          promptTemplateOptions.value = templates.map((t: any) => ({
            label: `${t.name}${t.category ? ` [${t.category}]` : ''}${t.is_default ? ' (默认)' : ''}`,
            value: t.id
          }));
          
          // Auto-select the default template if it exists
          const defaultTemplate = templates.find((t: any) => t.is_default);
          if (defaultTemplate && !selectedTemplate.value) {
            selectedTemplate.value = defaultTemplate.id;
            // Automatically apply the default template
            applyTemplate(defaultTemplate.id);
            if (isDev) console.log('[Templates] Auto-applied default template:', defaultTemplate.name);
          }
          
          if (isDev) console.log('[Templates] Loaded', templates.length, 'prompt templates');
        } else {
          promptTemplateOptions.value = [];
          if (isDev) console.log('[Templates] No templates found in localStorage');
        }
      } catch (error) {
        console.error('Failed to load prompt templates:', error);
        promptTemplateOptions.value = [];
      }
    };
    
    // Replace placeholders in template with actual task data
    const replacePlaceholders = (content: string): string => {
      if (!advertisementTask.value) {
        return content;
      }
      
      const task = advertisementTask.value;
      const replacements: Record<string, string> = {
        '{task_title}': task.task_title || '',
        '{hashtags}': (task.hashtags || []).join(' ') || '',
        '{tag_require}': task.tag_require || '',
        '{submission_rules}': task.submission_rules || '',
        '{task_id}': task.id?.toString() || ''
      };
      
      let result = content;
      for (const [placeholder, value] of Object.entries(replacements)) {
        // Use split/join for broader TypeScript compatibility
        result = result.split(placeholder).join(value);
      }
      
      return result;
    };

    // Apply a template to customPrompt
    const applyTemplate = (templateId: string | null) => {
      if (!templateId) {
        if (isDev) console.log('[Template] Cleared template selection');
        return;
      }
      
      const template = promptTemplates.value.find(t => t.id === templateId);
      if (!template) {
        message.warning('未找到选中的模板');
        return;
      }
      
      // Apply template content with placeholder replacement
      const processedContent = replacePlaceholders(template.content);
      formData.customPrompt = processedContent;
      
      // Show info message based on whether placeholders were replaced
      const hasPlaceholders = template.content.includes('{task_');
      if (hasPlaceholders && advertisementTask.value) {
        message.success(`已应用模板: ${template.name}（包含任务信息）`);
      } else if (hasPlaceholders && !advertisementTask.value) {
        message.warning(`已应用模板: ${template.name}（未加载任务信息，占位符未替换）`);
      } else {
        message.success(`已应用模板: ${template.name}`);
      }
      
      if (isDev) console.log('[Template] Applied template:', template.name);
    };

    // Load connected LLM models from localStorage (from LLM Models tab)
    const loadLLMModels = () => {
      try {
        const stored = localStorage.getItem('llm_model_configs');
        if (stored) {
          const configs = JSON.parse(stored);
          
          // Only show models that have been configured in LLM Models tab
          const connectedModels = configs.map((config: any) => ({
            label: `${config.name} (${config.model})`,
            value: config.model
          }));
          
          llmModelOptions.value = connectedModels;
          
          // Set default to active model if available
          const activeIndex = localStorage.getItem('llm_active_config_index');
          if (activeIndex !== null && connectedModels.length > 0) {
            const index = parseInt(activeIndex);
            if (index >= 0 && index < connectedModels.length && !formData.llmModel) {
              formData.llmModel = connectedModels[index].value;
            }
          } else if (connectedModels.length > 0 && !formData.llmModel) {
            // Fallback to first model if no active index
            formData.llmModel = connectedModels[0].value;
          }
        } else {
          // No connected models configured
          llmModelOptions.value = [];
          console.warn('No LLM models configured. Please configure models in LLM Models tab.');
        }
      } catch (error) {
        console.error('Failed to load connected LLM models:', error);
        llmModelOptions.value = [];
      }
    };

    const getImageUrl = (image: ImageItem): string => {
      // Check cache first
      if (imageUrlCache.has(image.id)) {
        return imageUrlCache.get(image.id)!;
      }
      
      const path = image.file_path;
      let url: string;
      const backendUrl = 'http://localhost:5001';  // Backend server URL
      
      // Handle uploaded images: /uploads/filename or upload/images/filename
      if (path.startsWith('/uploads/')) {
        const filename = path.substring('/uploads/'.length);
        url = `${backendUrl}/api/images/uploads/${filename}`;
      } else if (path.includes('upload/images/')) {
        const filename = path.split('upload/images/')[1];
        url = `${backendUrl}/api/images/uploads/${filename}`;
      } else if (path.includes('output/images/')) {
        // Handle generated/output images: output/images/filename
        const filename = path.split('output/images/')[1];
        url = `${backendUrl}/api/images/output/${filename}`;
      } else if (path.startsWith('/output/')) {
        const filename = path.substring('/output/'.length);
        url = `${backendUrl}/api/images/output/${filename}`;
      } else {
        // For all other paths (including absolute paths from default locations),
        // use the backend API to serve the image by ID
        url = `${backendUrl}/api/images/${image.id}/file`;
      }
      
      // Cache the result
      imageUrlCache.set(image.id, url);
      return url;
    };

    const toggleRegularImage = (imageId: number) => {
      if (selectedRegularImagesSet.value.has(imageId)) {
        selectedRegularImagesSet.value.delete(imageId);
      } else {
        selectedRegularImagesSet.value.add(imageId);
      }
      // Trigger reactivity
      selectedRegularImagesSet.value = new Set(selectedRegularImagesSet.value);
    };

    const toggleAdvertisementImage = (imageId: number) => {
      if (selectedAdvertisementImagesSet.value.has(imageId)) {
        selectedAdvertisementImagesSet.value.delete(imageId);
      } else {
        selectedAdvertisementImagesSet.value.add(imageId);
      }
      // Trigger reactivity
      selectedAdvertisementImagesSet.value = new Set(selectedAdvertisementImagesSet.value);
    };

    const loadAdvertisementTask = async () => {
      loadingTask.value = true;
      try {
        const response = await fetch(`http://localhost:5001/api/advertisement-tasks/${props.advertisementTaskId}`);
        const data = await response.json();
        
        if (data.success) {
          advertisementTask.value = data.data;
          console.log('[LoadTask] Advertisement task loaded:', advertisementTask.value);
          console.log('[LoadTask] Task will be used as context in step 3');
        } else {
          message.error('加载任务失败: ' + data.message);
        }
      } catch (error) {
        console.error('[LoadTask] Error loading advertisement task:', error);
        message.error('加载任务失败');
      } finally {
        loadingTask.value = false;
      }
    };

    const loadRuleCard = async () => {
      if (!props.ruleCardId) return;
      
      try {
        console.log('[LoadRuleCard] Loading rule card:', props.ruleCardId);
        const response = await fetch(`http://localhost:5001/api/advertisement-tasks/rule-card/${props.ruleCardId}`);
        const data = await response.json();
        
        if (data.success) {
          selectedRuleCard.value = data.data;
          console.log('[LoadRuleCard] Rule card loaded:', selectedRuleCard.value);
          console.log('[LoadRuleCard] Rule card tag_require:', selectedRuleCard.value.tag_require);
        } else {
          console.error('[LoadRuleCard] Failed to load rule card:', data.message);
        }
      } catch (error) {
        console.error('[LoadRuleCard] Error loading rule card:', error);
      }
    };

    const loadImages = async () => {
      try {
        console.log('[LoadImages] ========== STARTING FRESH LOAD ==========');
        console.log('[LoadImages] Timestamp:', new Date().toISOString());
        
        // Fetch all images in multiple requests due to backend pagination limits
        const perPage = 500;
        let allImages: ImageItem[] = [];
        let page = 1;
        let totalPages = 1;

        // First request to get total pages
        console.log(`[LoadImages] Fetching page ${page} with ${perPage} items per page`);
        const firstResponse = await listImages({ page, page_size: perPage });
        
        if (isDev) console.log('[ParticipationProcess] First response:', firstResponse);
        
        if (firstResponse.success) {
          if (isDev) console.log('[ParticipationProcess] First response data:', firstResponse);
          const firstPageImages = firstResponse.data.items || [];
          if (isDev) console.log(`[ParticipationProcess] First page images count: ${firstPageImages.length}`);
          
          allImages = firstResponse.data?.items || [];
          totalPages = firstResponse.data?.pagination?.pages || 1;
        }

        // Fetch remaining pages if any
        if (totalPages > 1) {
          if (isDev) console.log(`[ParticipationProcess] Fetching remaining ${totalPages - 1} pages`);
          const fetchPromises = [];
          for (page = 2; page <= totalPages; page++) {
            fetchPromises.push(listImages({ page, page_size: perPage }));
          }
          const responses = await Promise.all(fetchPromises);
          responses.forEach((response, index) => {
            if (response.success && response.data && response.data.items) {
              const pageImages = response.data.items;
              if (isDev) console.log(`[ParticipationProcess] Page ${index + 2}: ${pageImages.length} images`);
              allImages.push(...pageImages);
            }
          });
        }

        console.log(`[LoadImages] ========== LOADED DATA ==========`);
        console.log(`[LoadImages] Total images from API: ${allImages.length}`);
        
        // Show breakdown by type
        const typeBreakdown = allImages.reduce((acc, img) => {
          acc[img.image_type] = (acc[img.image_type] || 0) + 1;
          return acc;
        }, {} as Record<string, number>);
        console.log('[LoadImages] Image type breakdown:', typeBreakdown);
        
        // Show all images
        console.log('[LoadImages] All images:', allImages.map(img => ({
          id: img.id,
          filename: img.filename,
          type: img.image_type,
          participated: img.participated
        })));

        // Filter regular images (exclude participated and used ones)
        unusedRegularImages.value = allImages.filter((img: ImageItem) => 
          img.image_type === 'general' && !img.participated && !img.used
        );
        
        console.log(`[LoadImages] Filtered regular images: ${unusedRegularImages.value.length}`);

        // Filter advertisement images (exclude participated and used ones)
        const oldAdCount = advertisementImages.value.length;
        const oldIds = advertisementImages.value.map(img => img.id);
        
        const newAdImages = allImages.filter((img: ImageItem) => 
          img.image_type === 'advertising_campaign' && !img.participated && !img.used
        );
        
        // Force Vue reactivity by creating new array reference
        advertisementImages.value = [...newAdImages];
        
        // Force re-render by changing key
        renderKey.value++;
        
        console.log(`[LoadImages] ========== ADVERTISEMENT IMAGES ==========`);
        console.log(`[LoadImages] Advertisement count BEFORE filter: ${oldAdCount}`);
        console.log(`[LoadImages] Old image IDs:`, oldIds);
        console.log(`[LoadImages] Advertisement count AFTER filter: ${advertisementImages.value.length}`);
        console.log(`[LoadImages] New image IDs:`, advertisementImages.value.map(img => img.id));
        
        // Detect if images were replaced
        const addedIds = advertisementImages.value.map(img => img.id).filter(id => !oldIds.includes(id));
        const removedIds = oldIds.filter(id => !advertisementImages.value.map(img => img.id).includes(id));
        
        if (addedIds.length > 0) {
          console.log(`[LoadImages] ✅ ADDED image IDs:`, addedIds);
        }
        if (removedIds.length > 0) {
          console.warn(`[LoadImages] ⚠️ REMOVED/LOST image IDs:`, removedIds);
          console.warn(`[LoadImages] ^ These images disappeared from the database!`);
        }
        
        if (advertisementImages.value.length === oldAdCount) {
          console.warn(`[LoadImages] ⚠️ WARNING: Count did NOT increase!`);
          console.warn(`[LoadImages] This means either:`);
          console.warn(`[LoadImages]   1. Backend didn't save the new image`);
          console.warn(`[LoadImages]   2. Image was saved with wrong type`);
          console.warn(`[LoadImages]   3. API response is cached`);
        } else if (advertisementImages.value.length > oldAdCount) {
          console.log(`[LoadImages] ✅ SUCCESS: Found ${advertisementImages.value.length - oldAdCount} new images!`);
        }
        
        console.log(`[LoadImages] Advertisement images:`, advertisementImages.value.map(img => ({
          id: img.id,
          filename: img.filename,
          type: img.image_type
        })));
        // Update debug info
        const adCount = advertisementImages.value.length;
        const genCount = allImages.filter(i => i.image_type === 'general').length;
        debugInfo.totalImages = allImages.length;
        debugInfo.adImages = adCount;
        debugInfo.generalImages = genCount;
        debugInfo.lastUpdate = new Date().toLocaleTimeString();
        
        if (adCount === oldAdCount && allImages.length > oldAdCount) {
          debugInfo.warning = `新上传的图片可能被保存为 'general' 类型而不是 'advertising_campaign'`;
        } else if (adCount > oldAdCount) {
          debugInfo.warning = '';
        }
        
        console.log(`[LoadImages] ========== LOAD COMPLETE ==========`);
        
      } catch (err) {
        console.error('[ParticipationProcess] Failed to load images:', err);
        message.error('加载图片失败,请检查网络连接或联系技术支持');
      }
    };

    const nextStep = () => {
      if (step.value < 3) {
        step.value++;
      }
    };

    const prevStep = () => {
      if (step.value > 1) {
        step.value--;
      }
    };

    const handleUploadFinish = (options: any) => {
      console.log('[UPLOAD FINISH] ============ UPLOAD COMPLETED ============');
      console.log('[UPLOAD FINISH] Upload response:', options);
      
      // Extract image ID from response and auto-select
      let uploadedImageId: number | null = null;
      try {
        const response = options.event?.target?.response;
        if (response) {
          const result = typeof response === 'string' ? JSON.parse(response) : response;
          if (result.success && result.data && result.data.id) {
            uploadedImageId = typeof result.data.id === 'string' ? parseInt(result.data.id, 10) : result.data.id;
            if (uploadedImageId && !isNaN(uploadedImageId)) {
              selectedAdvertisementImagesSet.value.add(uploadedImageId);
              // Trigger reactivity
              selectedAdvertisementImagesSet.value = new Set(selectedAdvertisementImagesSet.value);
              console.log(`[UPLOAD FINISH] Auto-selected uploaded image ID: ${uploadedImageId}`);
              message.success(`图片上传成功并已选中`);
            } else {
              message.success('图片上传成功');
            }
          } else {
            message.success('图片上传成功');
          }
        } else {
          message.success('图片上传成功');
        }
      } catch (error) {
        console.error('[UPLOAD FINISH] Error parsing response:', error);
        message.success('图片上传成功');
      }
      
      // Fire-and-forget async reload
      (async () => {
        // Capture existing image IDs BEFORE reload
        const existingImageIds = new Set(advertisementImages.value.map(img => img.id));
        console.log('[UPLOAD FINISH] Existing image IDs before reload:', Array.from(existingImageIds));
        
        // Also capture current selections (ensure all are numbers)
        const currentSelections = new Set<number>();
        selectedAdvertisementImagesSet.value.forEach(id => {
          const numId = typeof id === 'string' ? parseInt(id as any, 10) : id;
          if (!isNaN(numId)) currentSelections.add(numId);
        });
        // Also capture the newly uploaded image ID
        if (uploadedImageId && !isNaN(uploadedImageId)) {
          currentSelections.add(uploadedImageId);
        }
        
        console.log('[UPLOAD FINISH] Waiting 2 seconds for backend to save...');
        console.log('[UPLOAD FINISH] Selections to preserve:', Array.from(currentSelections));
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        console.log('[UPLOAD FINISH] Now calling loadImages()...');
        await loadImages();
        
        // Wait for Vue to update
        await nextTick();
        
        // Find ALL newly added images (images that didn't exist before the upload)
        const newImageIds = advertisementImages.value
          .filter(img => !existingImageIds.has(img.id))
          .map(img => img.id);
        
        console.log('[UPLOAD FINISH] Newly added image IDs:', newImageIds);
        
        // Create new selection with all existing selections + all new images
        const newSelection = new Set<number>(currentSelections);
        
        // Add all newly uploaded images to selection
        newImageIds.forEach(id => {
          newSelection.add(id);
          console.log(`[UPLOAD FINISH] Auto-selecting new image ID: ${id}`);
        });
        
        // Log what we're selecting
        console.log('[UPLOAD FINISH] Preserving selections:', Array.from(currentSelections));
        
        // Replace the Set to trigger reactivity
        selectedAdvertisementImagesSet.value = newSelection;
        
        // Increment version to force template re-render
        selectionVersion.value++;
        
        // Wait for Vue to render
        await nextTick();
        
        console.log('[UPLOAD FINISH] After loadImages(), advertisement count:', advertisementImages.value.length);
        console.log('[UPLOAD FINISH] Advertisement IDs:', advertisementImages.value.map(img => img.id));
        console.log('[UPLOAD FINISH] Final selected IDs:', Array.from(selectedAdvertisementImagesSet.value));
        console.log('[UPLOAD FINISH] Selection version:', selectionVersion.value);
        console.log('[UPLOAD FINISH] ============ COMPLETE ============');
      })();
    };
    
    const handleImageError = (event: Event) => {
      const img = event.target as HTMLImageElement;
      if (isDev) console.error('[Image Error] Failed to load:', img.src);
      // Set a placeholder or retry
      img.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="150" height="130" viewBox="0 0 150 130"%3E%3Crect fill="%23f0f0f0" width="150" height="130"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" fill="%23999" font-family="sans-serif" font-size="12"%3E图片加载失败%3C/text%3E%3C/svg%3E';
    };

    const handleClipboardPaste = async (event: ClipboardEvent) => {
      event.preventDefault();
      
      if (isDev) console.log('[Paste] Event triggered:', event);
      
      // Try legacy clipboardData first
      if (event.clipboardData && event.clipboardData.items.length > 0) {
        if (isDev) console.log('[Paste] Using clipboardData API');
        const items = Array.from(event.clipboardData.items);
        if (isDev) console.log('[Paste] Items found:', items.length, items.map(i => i.type));
        
        // Filter for image items and supported formats
        const imageItems = items.filter(item => {
          const supportedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp', 'image/bmp'];
          return supportedTypes.includes(item.type);
        });

        if (imageItems.length === 0) {
          if (isDev) console.log('[Paste] No image items found in clipboard');
          // Check if there's any data at all
          if (items.length > 0) {
            const types = items.map(i => i.type).join(', ');
            message.warning(`剪贴板内容类型不支持: ${types}\n支持的格式: PNG, JPG, GIF, WebP, BMP`);
          } else {
            message.warning('剪贴板为空');
          }
          return;
        }
        
        // Process images from clipboardData
        await processClipboardImages(imageItems);
        return;
      }
      
      // Fallback to modern Clipboard API
      if (isDev) console.log('[Paste] Trying Clipboard API fallback');
      try {
        if (!navigator.clipboard) {
          message.error('此浏览器不支持剪贴板 API');
          return;
        }
        
        const clipboardItems = await navigator.clipboard.read();
        if (isDev) console.log('[Paste] Clipboard API items:', clipboardItems);
        
        const imageFiles: File[] = [];
        
        for (const clipboardItem of clipboardItems) {
          for (const type of clipboardItem.types) {
            if (type.startsWith('image/')) {
              const blob = await clipboardItem.getType(type);
              const file = new File([blob], `pasted-image.${type.split('/')[1]}`, { type });
              imageFiles.push(file);
            }
          }
        }
        
        if (imageFiles.length === 0) {
          message.warning('剪贴板中没有图片数据');
          return;
        }
        
        // Process images from Clipboard API
        const mockItems = imageFiles.map(file => ({
          type: file.type,
          getAsFile: () => file
        }));
        
        await processClipboardImages(mockItems as any);
      } catch (err: any) {
        console.error('[Paste] Clipboard API error:', err);
        if (err.name === 'NotAllowedError') {
          message.error('没有访问剪贴板的权限。请允许此网站访问剪贴板。');
        } else {
          message.error('无法访问剪贴板，请重试或使用上传功能');
        }
      }
    };
    
    const processClipboardImages = async (imageItems: any[]) => {

      console.log('============ PASTE START ============');
      console.log('[Paste] Processing', imageItems.length, 'new images');
      console.log('[Paste] Current pastedImages array:', pastedImages.value);
      console.log('[Paste] Array length BEFORE:', pastedImages.value.length);
      
      isPasteAreaActive.value = true;
      showPastePreview.value = true;
      
      // Don't reset - keep existing pasted images and append new ones
      const existingCount = pastedImages.value.length;
      console.log('[Paste] Existing count:', existingCount);
      console.log('[Paste] Will add', imageItems.length, 'new images');
      
      try {
        // Create preview entries for all images
        const previewPromises = imageItems.map(async (item, index) => {
          const file = item.getAsFile ? item.getAsFile() : item;
          if (!file) {
            if (isDev) console.warn('[Paste] Failed to get file for item', index);
            return null;
          }

          const preview = URL.createObjectURL(file);
          const name = file.name || `pasted-image-${index + 1}.${file.type.split('/')[1]}`;
          
          if (isDev) console.log('[Paste] Created preview for:', name);
          
          return {
            preview,
            name,
            file,
            status: 'pending' as const
          };
        });

        const previews = (await Promise.all(previewPromises)).filter(Boolean);
        
        console.log('[Paste] Created', previews.length, 'preview objects');
        console.log('[Paste] Preview objects:', previews);
        
        // Append new images to existing ones instead of replacing
        pastedImages.value = [...pastedImages.value, ...previews as any];
        
        console.log('[Paste] Array length AFTER append:', pastedImages.value.length);
        console.log('[Paste] Full array after append:', pastedImages.value.map(img => img.name));
        console.log('============ PASTE END ============');

        if (previews.length === 0) {
          message.error('无法读取剪贴板中的图片');
          return;
        }

        message.info(`检测到 ${previews.length} 张图片,开始上传...`);
        uploadingCount.value = previews.length;

        // Calculate the starting index for the new batch in the full array
        const startIndex = existingCount;
        
        // Upload all images with progress tracking
        const uploadPromises = previews.map(async (previewData: any, batchIndex) => {
          try {
            if (!previewData || !previewData.file) {
              return { success: false, error: 'Invalid file data' };
            }
            
            // Use correct index in the full pastedImages array
            const fullIndex = startIndex + batchIndex;
            pastedImages.value[fullIndex].status = 'uploading';
            
            const formData = new FormData();
            // Create a new Blob with empty filename to force backend UUID generation
            const blob = new Blob([previewData.file], { type: previewData.file.type });
            formData.append('file', blob, ''); // Empty filename triggers backend UUID logic
            formData.append('image_type', 'advertising_campaign');

            const uploadResponse = await fetch('/api/images/upload', {
              method: 'POST',
              body: formData
            });

            if (!uploadResponse.ok) {
              throw new Error(`HTTP ${uploadResponse.status}: ${uploadResponse.statusText}`);
            }

            const result = await uploadResponse.json();
            if (!result.success) {
              throw new Error(result.message || '上传失败');
            }

            pastedImages.value[fullIndex].status = 'success';
            uploadingCount.value--;
            
            // Auto-select the uploaded image in advertisement images
            if (result.data && result.data.id) {
              selectedAdvertisementImagesSet.value.add(result.data.id);
              // Trigger reactivity
              selectedAdvertisementImagesSet.value = new Set(selectedAdvertisementImagesSet.value);
              console.log(`[Upload] Auto-selected image ID: ${result.data.id}`);
            }
            
            return { success: true, result };
          } catch (error: any) {
            const fullIndex = startIndex + batchIndex;
            pastedImages.value[fullIndex].status = 'error';
            pastedImages.value[fullIndex].error = error.message || '上传失败';
            uploadingCount.value--;
            return { success: false, error: error.message };
          }
        });

        const results = await Promise.all(uploadPromises);
        
        const successfulUploads = results.filter(r => r.success).length;
        const failedUploads = results.filter(r => !r.success).length;
        
        // Collect all successfully uploaded image IDs for auto-selection
        const uploadedImageIds: number[] = results
          .filter(r => r.success && r.result?.data?.id)
          .map(r => r.result.data.id);

        // Reload images FIRST to show newly uploaded ones
        if (successfulUploads > 0) {
          console.log('[Upload] Starting grid refresh...');
          console.log('[Upload] Uploaded image IDs to auto-select:', uploadedImageIds);
          
          // Capture existing image IDs BEFORE reload
          const existingImageIds = new Set(advertisementImages.value.map(img => img.id));
          console.log('[Upload] Existing image IDs before reload:', Array.from(existingImageIds));
          
          // Wait longer for backend to save images
          await new Promise(resolve => setTimeout(resolve, 1500));
          
          // Try multiple times to ensure images are loaded
          for (let attempt = 1; attempt <= 3; attempt++) {
            console.log(`[Upload] Refresh attempt ${attempt}/3`);
            
            await loadImages();
            
            console.log('[Upload] Advertisement images count:', advertisementImages.value.length);
            
            // If we got new images, stop trying
            if (advertisementImages.value.length > existingImageIds.size) {
              console.log('[Upload] ✅ Grid refreshed successfully!');
              break;
            }
            
            // Wait before retry
            if (attempt < 3) {
              console.log('[Upload] Not all images loaded, retrying in 1s...');
              await new Promise(resolve => setTimeout(resolve, 1000));
            }
          }
          
          // Wait for Vue to update the DOM
          await nextTick();
          
          // Find ALL newly added images (images that didn't exist before the upload)
          const newImageIds = advertisementImages.value
            .filter(img => !existingImageIds.has(img.id))
            .map(img => img.id);
          
          console.log('[Upload] Newly added image IDs:', newImageIds);
          
          // Create new selection with all existing selections + all new images
          const newSelection = new Set<number>(selectedAdvertisementImagesSet.value);
          
          // Add all newly uploaded images to selection
          newImageIds.forEach(id => {
            newSelection.add(id);
            console.log(`[Upload] Auto-selecting new image ID: ${id}`);
          });
          
          // Also add IDs from upload response (in case they're different)
          uploadedImageIds.forEach(id => {
            const numId = typeof id === 'string' ? parseInt(id, 10) : id;
            if (!isNaN(numId)) {
              newSelection.add(numId);
            }
          });
          
          // Replace the entire Set to trigger reactivity
          selectedAdvertisementImagesSet.value = newSelection;
          
          // Increment version to force template re-render
          selectionVersion.value++;
          
          console.log('[Upload] Final selected IDs:', Array.from(selectedAdvertisementImagesSet.value));
          console.log('[Upload] Advertisement image IDs:', advertisementImages.value.map(img => img.id));
          console.log('[Upload] Selection version:', selectionVersion.value);
          
          // Force another nextTick to ensure selection is rendered
          await nextTick();
        }

        // Show results with detailed feedback AFTER grid updates
        if (successfulUploads > 0 && failedUploads === 0) {
          message.success(`✅ 成功添加 ${successfulUploads} 张图片！已添加到上方活动图片区域 ↑`);
        } else if (successfulUploads > 0 && failedUploads > 0) {
          message.warning(`⚠️ 成功 ${successfulUploads} 张, 失败 ${failedUploads} 张。成功的图片已添加到上方 ↑`);
        } else {
          message.error(`❌ 全部上传失败 (${failedUploads} 张)`);
        }

        // Keep preview visible - do NOT auto-clear
        // Images will remain visible in modal until user closes it manually
        // Refocus for additional pastes
        setTimeout(() => {
          focusPasteDiv();
        }, 500);

      } catch (error) {
        console.error('粘贴上传失败:', error);
        message.error('图片处理失败,请重试');
      } finally {
        isPasteAreaActive.value = false;
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key === 'v') {
        event.preventDefault();
        handleClipboardPaste(event as any);
      }
    };

    const focusPasteDiv = () => {
      if (pasteDiv.value) {
        if (isDev) console.log('[Focus] Focusing paste area');
        pasteDiv.value.focus();
        // Add visible focus indicator
        isPasteAreaActive.value = false;
        pasteAreaFocused.value = true;
      } else {
        if (isDev) console.warn('[Focus] Paste div not found');
      }
    };
    
    const handlePasteAreaClick = () => {
      if (isDev) console.log('[Click] Paste area clicked');
      focusPasteDiv();
      // Try to request clipboard permission proactively (Chrome)
      if (navigator.clipboard && 'readText' in navigator.clipboard) {
        navigator.clipboard.readText().catch(() => {
          // Permission request, ignore errors
          if (isDev) console.log('[Permission] Clipboard permission requested');
        });
      }
    };
    
    const forceReloadImages = async () => {
      console.log('[FORCE RELOAD] User clicked refresh button');
      isReloading.value = true;
      
      try {
        // Clear everything first
        advertisementImages.value = [];
        unusedRegularImages.value = [];
        
        // Force a complete reload
        await loadImages();
        
        console.log('[FORCE RELOAD] Complete! Advertisement count:', advertisementImages.value.length);
        message.success(`刷新完成！当前有 ${advertisementImages.value.length} 张活动图片`);
      } catch (error) {
        console.error('[FORCE RELOAD] Error:', error);
        message.error('刷新失败，请重试');
      } finally {
        isReloading.value = false;
      }
    };
    
    const toggleDebugPanel = () => {
      showDebugPanel.value = !showDebugPanel.value;
    };
    
    const testAddImage = () => {
      console.log('[TEST] Adding fake image to test Vue reactivity...');
      const fakeImage: ImageItem = {
        id: Date.now(),
        filename: `test-image-${Date.now()}.jpg`,
        file_path: '/test/path.jpg',
        source: 'test',
        image_type: 'advertising_campaign',
        created_at: new Date().toISOString(),
        participated: false,
        variables: { test: true }
      };
      
      console.log('[TEST] Current count:', advertisementImages.value.length);
      advertisementImages.value = [...advertisementImages.value, fakeImage];
      renderKey.value++; // Force re-render
      console.log('[TEST] New count:', advertisementImages.value.length);
      console.log('[TEST] Forced re-render with renderKey:', renderKey.value);
      console.log('[TEST] If count increased and grid updates, Vue reactivity works!');
      
      message.success(`测试添加成功！当前 ${advertisementImages.value.length} 张`);
    };
    
    const handleModalClose = async () => {
      console.log('[Modal] ========== MODAL CLOSING ==========');
      
      // Show count of pasted images if any
      const pastedCount = pastedImages.value.length;
      const successCount = pastedImages.value.filter(img => img.status === 'success').length;
      
      console.log(`[Modal] Total pasted: ${pastedCount}, Successful: ${successCount}`);
      
      if (successCount > 0) {
        // Store current count to verify increase
        const beforeCount = advertisementImages.value.length;
        console.log(`[Modal] Current advertisement count: ${beforeCount}`);
        console.log(`[Modal] Expected after reload: ${beforeCount + successCount}`);
        
        // Wait longer for backend to save all images
        console.log('[Modal] Waiting 2 seconds for backend to save...');
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Try multiple times to load the new images
        for (let attempt = 1; attempt <= 5; attempt++) {
          console.log(`[Modal] Load attempt ${attempt}/5...`);
          
          await loadImages();
          
          const afterCount = advertisementImages.value.length;
          console.log(`[Modal] After load: ${afterCount} images`);
          
          // If we got all new images, stop trying
          if (afterCount >= beforeCount + successCount) {
            console.log('[Modal] ✅ All new images loaded successfully!');
            break;
          }
          
          // Wait before retry
          if (attempt < 5) {
            console.log(`[Modal] Only got ${afterCount - beforeCount}/${successCount} new images, retrying in 1s...`);
            await new Promise(resolve => setTimeout(resolve, 1000));
          } else {
            console.warn(`[Modal] ⚠️ Could not load all images after 5 attempts`);
            console.warn(`[Modal] Expected ${beforeCount + successCount}, got ${afterCount}`);
          }
        }
      } else {
        // No successful uploads, just do a simple reload
        await loadImages();
      }
      
      console.log('[Modal] ========== MODAL CLOSE COMPLETE ==========');
      
      // Clear preview state only when modal closes
      showPastePreview.value = false;
      pastedImages.value = [];
      isPasteAreaActive.value = false;
      pasteAreaFocused.value = false;
    };

    const selectedRuleImageIds = computed(() => Array.from(selectedRuleImagesSet.value));

    const addRuleImageId = (value: string | number | null | undefined) => {
      if (value === null || value === undefined) return;
      const parsed = Number(value);
      if (Number.isNaN(parsed) || parsed <= 0) return;
      selectedRuleImagesSet.value.add(parsed);
      selectedRuleImagesSet.value = new Set(selectedRuleImagesSet.value);
    };

    watch(
      () => props.initialRuleImageId,
      (newVal) => {
        addRuleImageId(newVal as string | number | null | undefined);
      },
      { immediate: true }
    );

    // Show preview before generating
    const generatePrompt = async () => {
      if (selectedRegularImagesSet.value.size === 0 || selectedAdvertisementImagesSet.value.size === 0) {
        message.error('请选择普通图片和活动图片');
        return;
      }
      
      // Check if LLM model is configured
      if (!formData.llmModel || !formData.llmModel.trim()) {
        message.error('请先在 LLM 模型管理中配置模型');
        return;
      }
      
      // Prepare preview data - use rule card data when available
      const ruleCardTagRequire = selectedRuleCard.value?.tag_require || '';
      const taskHashtags = (advertisementTask.value?.hashtags || []).map((tag: string) => tag.startsWith('#') ? tag : `#${tag}`).join(' ');
      
      previewPromptData.value = {
        regular_images: Array.from(selectedRegularImagesSet.value).length,
        event_images: Array.from(selectedAdvertisementImagesSet.value).length,
        rule_images: selectedRuleImageIds.value.length,
        custom_prompt: formData.customPrompt,
        model: formData.llmModel,
        task_info: advertisementTask.value ? {
          task_title: selectedRuleCard.value?.rule_name || advertisementTask.value.task_title,
          hashtags: ruleCardTagRequire || taskHashtags,
          tag_require: ruleCardTagRequire || advertisementTask.value.tag_require,
          submission_rules: selectedRuleCard.value?.submission_rules || advertisementTask.value.submission_rules
        } : null
      };
      
      // Go to Step 4 instead of showing modal
      step.value = 4;
    };
    
    // Generate prompt directly
    const confirmAndGenerate = async () => {
      if (selectedRegularImagesSet.value.size === 0 || selectedAdvertisementImagesSet.value.size === 0) {
        message.error('请选择普通图片和活动图片');
        return;
      }
      
      // Check if LLM model is configured
      if (!formData.llmModel || !formData.llmModel.trim()) {
        message.error('请先在 LLM 模型管理中配置模型');
        return;
      }

      // Force sync LLM config before generating
      console.log('[Generate] Force syncing LLM config before generation...');
      try {
        const llmConfigs = localStorage.getItem('llm_model_configs');
        const activeIndex = localStorage.getItem('llm_active_config_index');
        
        if (llmConfigs) {
          const configs = JSON.parse(llmConfigs);
          const index = activeIndex ? parseInt(activeIndex) : 0;
          const activeConfig = configs[index];
          
          if (activeConfig) {
            console.log('[Generate] Syncing active config:', activeConfig);
            
            const syncPayload: any = {
              enhance_model: activeConfig.model,
              caption_model: activeConfig.model,
            };
            
            if (activeConfig.apiBase && activeConfig.apiBase.trim()) {
              syncPayload.api_base = activeConfig.apiBase.trim();
            } else if (activeConfig.apiHost && activeConfig.apiPort) {
              syncPayload.api_host = activeConfig.apiHost.trim();
              syncPayload.api_port = activeConfig.apiPort.trim();
            }
            
            await fetch('/api/prompt/models', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(syncPayload)
            });
            console.log('[Generate] LLM config synced successfully');
          }
        }
      } catch (e) {
        console.error('[Generate] Failed to sync LLM config:', e);
      }

      generating.value = true;
      
      try {
        // Build request payload
        const requestPayload: any = {
          regular_image_ids: Array.from(selectedRegularImagesSet.value),
          event_image_ids: Array.from(selectedAdvertisementImagesSet.value),
          rule_image_ids: selectedRuleImageIds.value,
          custom_prompt: formData.customPrompt,
          model: formData.llmModel,
        };
        
        // If advertisement task is loaded, include its context
        // Use rule card data when available (priority over task data)
        if (advertisementTask.value) {
          console.log('[Generate] Including advertisement task context');
          
          // Parse rule card's tag_require into array for hashtags
          let ruleCardHashtags: string[] = [];
          if (selectedRuleCard.value && selectedRuleCard.value.tag_require) {
            const tagMatches = selectedRuleCard.value.tag_require.match(/#[^\s#]+/g);
            if (tagMatches) {
              ruleCardHashtags = tagMatches;
            }
          }
          
          requestPayload.advertisement_task = {
            task_id: advertisementTask.value.id,
            task_title: selectedRuleCard.value?.rule_name || advertisementTask.value.task_title,
            hashtags: ruleCardHashtags.length > 0 ? ruleCardHashtags : (advertisementTask.value.hashtags || []),
            tag_require: selectedRuleCard.value?.tag_require || advertisementTask.value.tag_require || '',
            submission_rules: selectedRuleCard.value?.submission_rules || advertisementTask.value.submission_rules || ''
          };
          
          console.log('[Generate] Using context:', requestPayload.advertisement_task);
        }
        
        const response = await fetch('/api/prompt/participation', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestPayload)
        });

        const result = await response.json();
        if (result.success) {
          let finalPrompt = result.data.prompt;
          
          // Automatically append required tags/hashtags to LLM-generated result
          // Priority: rule card's tag_require > task's hashtags
          let hashtags = '';
          if (selectedRuleCard.value && selectedRuleCard.value.tag_require) {
            // Use rule card's tag_require (it's already a string with hashtags)
            hashtags = selectedRuleCard.value.tag_require;
            console.log('[Generate] Using rule card tags:', hashtags);
          } else if (advertisementTask.value && advertisementTask.value.hashtags && advertisementTask.value.hashtags.length > 0) {
            // Fall back to task's hashtags
            hashtags = advertisementTask.value.hashtags
              .map((tag: string) => tag.startsWith('#') ? tag : `#${tag}`)
              .join(' ');
            console.log('[Generate] Using task hashtags:', hashtags);
          }
          
          // Check if hashtags are not already in the generated content
          if (hashtags && !finalPrompt.includes(hashtags)) {
            finalPrompt = finalPrompt.trim() + '\n\n' + hashtags;
            if (isDev) console.log('[Generate] Appended required tags to generated prompt:', hashtags);
          }
          
          generatedPrompt.value = finalPrompt;
          
          // Prepare preview data for Step 4
          // Use rule card data when available
          const ruleCardTagRequire = selectedRuleCard.value?.tag_require || '';
          const taskHashtags = (advertisementTask.value?.hashtags || []).map((tag: string) => tag.startsWith('#') ? tag : `#${tag}`).join(' ');
          
          previewPromptData.value = {
            regular_images: Array.from(selectedRegularImagesSet.value).length,
            event_images: Array.from(selectedAdvertisementImagesSet.value).length,
            rule_images: selectedRuleImageIds.value.length,
            custom_prompt: formData.customPrompt,
            model: formData.llmModel,
            generated_text: finalPrompt,
            task_info: advertisementTask.value ? {
              task_title: selectedRuleCard.value?.rule_name || advertisementTask.value.task_title,
              hashtags: ruleCardTagRequire || taskHashtags,
              tag_require: ruleCardTagRequire || advertisementTask.value.tag_require,
              submission_rules: selectedRuleCard.value?.submission_rules || advertisementTask.value.submission_rules
            } : null
          };
          
          message.success('文案生成成功！');
          step.value = 4; // Go to confirmation step
        } else {
          message.error(result.message || '文案生成失败');
        }
      } catch (error) {
        console.error('生成文案失败:', error);
        message.error('文案生成失败');
      } finally {
        generating.value = false;
      }
    };
    
    // Cancel preview
    const cancelPreview = () => {
      showPreviewPromptModal.value = false;
      previewPromptData.value = null;
    };

    // Get all selected images for preview (regular images first)
    const getSelectedImages = () => {
      const selected: ImageItem[] = [];
      // Add regular images first
      selectedRegularImagesSet.value.forEach(id => {
        const img = unusedRegularImages.value.find(i => i.id === id);
        if (img) selected.push(img);
      });
      // Then add advertisement images
      selectedAdvertisementImagesSet.value.forEach(id => {
        const img = advertisementImages.value.find(i => i.id === id);
        if (img) selected.push(img);
      });
      return selected;
    };
    
    const copyGeneratedPrompt = () => {
      navigator.clipboard.writeText(generatedPrompt.value).then(() => {
        message.success('文案已复制到剪贴板');
      }).catch(() => {
        message.error('复制失败');
      });
    };
    
    // Publish the post to XHS
    const publishPost = async () => {
      if (!generatedPrompt.value || !generatedPrompt.value.trim()) {
        message.error('请先生成文案内容');
        return;
      }
      
      if (selectedRegularImagesSet.value.size === 0 && selectedAdvertisementImagesSet.value.size === 0) {
        message.error('请至少选择一张图片');
        return;
      }
      
      posting.value = true;
      
      try {
        // Get all selected images
        const allImages = getSelectedImages();
        const imageUrls = allImages.map(img => `/images/${img.source}/${img.filename}`);
        
        // Extract title from first line or use task title
        const lines = generatedPrompt.value.trim().split('\n');
        const title = selectedRuleCard.value?.rule_name || advertisementTask.value?.task_title || lines[0].replace(/^[#标题：]+/, '').trim() || '小红书笔记';
        
        // Get hashtags - priority: rule card's tag_require > task's hashtags > content extraction
        let topics: string[] = [];
        if (selectedRuleCard.value && selectedRuleCard.value.tag_require) {
          // Parse rule card's tag_require string into array
          const tagMatches = selectedRuleCard.value.tag_require.match(/#[^\s#]+/g);
          if (tagMatches) {
            topics = tagMatches;
          }
          console.log('[Publish] Using rule card topics:', topics);
        } else if (advertisementTask.value?.hashtags && advertisementTask.value.hashtags.length > 0) {
          topics = advertisementTask.value.hashtags;
          console.log('[Publish] Using task hashtags:', topics);
        }
        
        if (topics.length === 0) {
          // Extract hashtags from content as fallback
          const hashtagMatches = generatedPrompt.value.match(/#[^\s#]+/g);
          if (hashtagMatches) {
            topics = hashtagMatches;
            console.log('[Publish] Extracted topics from content:', topics);
          }
        }
        
        // Get user ID from localStorage (assuming it's stored)
        const userId = localStorage.getItem('user_id') || '1';
        
        const postData = {
          title: title,
          description: generatedPrompt.value,
          images: imageUrls,
          topics: topics,
          is_private: false,
          userId: parseInt(userId),
          task_id: advertisementTask.value?.id,  // Include task ID for marking as participated
          rule_card_id: props.ruleCardId ? parseInt(String(props.ruleCardId)) : null  // Include rule card ID
        };
        
        console.log('[Publish] Props ruleCardId:', props.ruleCardId);
        console.log('[Publish] Task ID:', advertisementTask.value?.id);
        console.log('[Publish] Rule Card ID being sent:', postData.rule_card_id);
        if (isDev) console.log('[Publish] Publishing to XHS:', postData);
        
        const response = await fetch('/api/publish', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(postData)
        });
        
        const result = await response.json();
        
        if (result.success) {
          message.success('笔记发布到小红书成功！');
          if (isDev) console.log('[Publish] XHS response:', result.data);
          
          // Mark images as participated
          try {
            const imageIds = [...Array.from(selectedRegularImagesSet.value), ...Array.from(selectedAdvertisementImagesSet.value)];
            for (const id of imageIds) {
              await fetch(`/api/images/${id}/participated`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' }
              });
            }
          } catch (e) {
            console.warn('[Publish] Failed to mark images as participated:', e);
          }
          
          // Navigate back to advertisement tasks after successful posting
          // This ensures the updated rule card status is shown
          message.info('即将返回任务列表...');
          setTimeout(() => {
            if (props.advertisementTaskId) {
              // Navigate back to advertisement tasks page
              router.push('/advertisement-tasks');
            } else {
              // Reset to step 1 if not from advertisement task
              step.value = 1;
              generatedPrompt.value = '';
              selectedRegularImagesSet.value.clear();
              selectedAdvertisementImagesSet.value.clear();
              selectedRuleImagesSet.value.clear();
              loadImages();
            }
          }, 1500);
        } else {
          message.error(result.message || '发布失败，请重试');
          if (isDev) console.error('[Publish] Failed:', result);
        }
      } catch (error) {
        console.error('[Publish] Error posting to XHS:', error);
        message.error('发布失败，请检查网络连接和用户登录状态');
      } finally {
        posting.value = false;
      }
    };
    
    // Computed property for available stickers based on category
    const availableStickers = computed(() => {
      return stickerLibrary[stickerCategory.value as keyof typeof stickerLibrary] || [];
    });
    
    // Image Preview functions
    const openImagePreview = (image: ImageItem) => {
      // Find the index of the image in unusedRegularImages
      const index = unusedRegularImages.value.findIndex(img => img.id === image.id);
      currentPreviewIndex.value = index;
      
      previewImage.value = image;
      imageZoom.value = 1;
      imageRotation.value = 0;
      previewPosition.value = { x: 0, y: 0 };
      showImagePreviewModal.value = true;
    };
    
    // Navigate to previous/next image
    const navigatePreview = (direction: 'prev' | 'next') => {
      if (unusedRegularImages.value.length === 0 || currentPreviewIndex.value === -1) return;
      
      let newIndex = currentPreviewIndex.value;
      if (direction === 'prev') {
        newIndex = currentPreviewIndex.value > 0 ? currentPreviewIndex.value - 1 : unusedRegularImages.value.length - 1;
      } else {
        newIndex = currentPreviewIndex.value < unusedRegularImages.value.length - 1 ? currentPreviewIndex.value + 1 : 0;
      }
      
      const newImage = unusedRegularImages.value[newIndex];
      if (newImage) {
        openImagePreview(newImage);
      }
    };
    
    // Reset preview state
    const resetPreview = () => {
      previewImage.value = null;
      currentPreviewIndex.value = -1;
      imageZoom.value = 1;
      imageRotation.value = 0;
      previewPosition.value = { x: 0, y: 0 };
      isPreviewDragging.value = false;
      previewDragStart.value = { x: 0, y: 0 };
    };
    
    // Computed style for preview image
    const previewImageStyle = computed(() => ({
      transform: `translate(${previewPosition.value.x}px, ${previewPosition.value.y}px) scale(${imageZoom.value}) rotate(${imageRotation.value}deg)`,
      cursor: isPreviewDragging.value ? 'grabbing' : 'grab',
      transition: isPreviewDragging.value ? 'none' : 'transform 0.3s ease',
      userSelect: 'none',
      'user-drag': 'none',
      '-webkit-user-drag': 'none',
      '-moz-user-select': 'none',
      '-webkit-user-select': 'none',
      '-ms-user-select': 'none'
    }));
    
    // Drag functions
    const startDragPreview = (e: MouseEvent) => {
      isPreviewDragging.value = true;
      previewDragStart.value = { x: e.clientX - previewPosition.value.x, y: e.clientY - previewPosition.value.y };
    };

    const handleDragPreview = (e: MouseEvent) => {
      if (!isPreviewDragging.value) return;
      previewPosition.value = {
        x: e.clientX - previewDragStart.value.x,
        y: e.clientY - previewDragStart.value.y
      };
    };

    const endDragPreview = () => {
      isPreviewDragging.value = false;
    };
    
    // Wheel zoom
    const handleWheelPreview = (e: WheelEvent) => {
      e.preventDefault();
      const delta = e.deltaY > 0 ? -0.1 : 0.1;
      const newZoom = Math.max(0.5, Math.min(3, imageZoom.value + delta));
      imageZoom.value = newZoom;
    };
    
    const addStickerToImage = (sticker: any) => {
      // Deselect all stickers first
      imageStickers.value.forEach(s => s.selected = false);
      
      // Add sticker to center of image
      const newSticker = {
        ...sticker,
        x: 50, // Center position percentage
        y: 50,
        size: 48, // Default size in pixels
        scale: 1, // Scale multiplier
        rotation: 0,
        selected: true // Auto-select new sticker
      };
      imageStickers.value.push(newSticker);
      message.success(`已添加 ${sticker.name}`);
    };
    
    // Select a sticker and enable dragging
    const selectSticker = (index: number, event: MouseEvent) => {
      event.preventDefault();
      event.stopPropagation();
      
      // Deselect all other stickers
      imageStickers.value.forEach((s, i) => s.selected = i === index);
      
      // Start dragging
      dragState.isDragging = true;
      dragState.activeIndex = index;
      dragState.startX = event.clientX;
      dragState.startY = event.clientY;
      
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    };
    
    // Remove a sticker
    const removeSticker = (index: number) => {
      imageStickers.value.splice(index, 1);
      message.success('贴纸已删除');
    };
    
    // Start resizing a sticker
    const startResize = (index: number, event: MouseEvent) => {
      event.preventDefault();
      event.stopPropagation();
      
      const sticker = imageStickers.value[index];
      dragState.isResizing = true;
      dragState.activeIndex = index;
      dragState.startX = event.clientX;
      dragState.startY = event.clientY;
      dragState.startScale = sticker.scale || 1;
      
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    };
    
    // Start rotating a sticker
    const startRotate = (index: number, event: MouseEvent) => {
      event.preventDefault();
      event.stopPropagation();
      
      const sticker = imageStickers.value[index];
      if (!imageCanvas.value) return;
      
      const canvasRect = imageCanvas.value.getBoundingClientRect();
      const centerX = canvasRect.left + (sticker.x / 100) * canvasRect.width;
      const centerY = canvasRect.top + (sticker.y / 100) * canvasRect.height;
      
      dragState.isRotating = true;
      dragState.activeIndex = index;
      dragState.startRotation = sticker.rotation || 0;
      dragState.centerX = centerX;
      dragState.centerY = centerY;
      
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    };
    
    // Handle mouse move for drag, resize, rotate
    const handleMouseMove = (event: MouseEvent) => {
      if (dragState.activeIndex === -1) return;
      const sticker = imageStickers.value[dragState.activeIndex];
      if (!sticker || !imageCanvas.value) return;
      
      if (dragState.isDragging) {
        // Calculate movement as percentage of canvas
        const canvasRect = imageCanvas.value.getBoundingClientRect();
        const deltaX = event.clientX - dragState.startX;
        const deltaY = event.clientY - dragState.startY;
        
        sticker.x += (deltaX / canvasRect.width) * 100;
        sticker.y += (deltaY / canvasRect.height) * 100;
        
        // Clamp to canvas bounds
        sticker.x = Math.max(0, Math.min(100, sticker.x));
        sticker.y = Math.max(0, Math.min(100, sticker.y));
        
        dragState.startX = event.clientX;
        dragState.startY = event.clientY;
      } else if (dragState.isResizing) {
        // Calculate scale based on vertical movement
        const deltaY = event.clientY - dragState.startY;
        const scaleDelta = -deltaY / 100; // Negative because moving up = bigger
        sticker.scale = Math.max(0.3, Math.min(3, dragState.startScale + scaleDelta));
      } else if (dragState.isRotating) {
        // Calculate angle from center
        const angle = Math.atan2(
          event.clientY - dragState.centerY,
          event.clientX - dragState.centerX
        );
        sticker.rotation = (angle * 180 / Math.PI);
      }
    };
    
    // Handle mouse up to end drag/resize/rotate
    const handleMouseUp = () => {
      dragState.isDragging = false;
      dragState.isResizing = false;
      dragState.isRotating = false;
      dragState.activeIndex = -1;
      
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
    
    // Zoom functions
    const zoomIn = () => {
      imageZoom.value = Math.min(imageZoom.value + 0.25, 5);
    };
    
    const zoomOut = () => {
      imageZoom.value = Math.max(imageZoom.value - 0.25, 0.25);
    };
    
    const resetZoom = () => {
      imageZoom.value = 1;
    };
    
    const fitToScreen = () => {
      imageZoom.value = 1;
    };
    
    const rotateLeft = () => {
      imageRotation.value = (imageRotation.value - 90) % 360;
    };
    
    const rotateRight = () => {
      imageRotation.value = (imageRotation.value + 90) % 360;
    };
    
    const handleWheel = (event: WheelEvent) => {
      event.preventDefault();
      if (event.deltaY < 0) {
        zoomIn();
      } else {
        zoomOut();
      }
    };
    
    const clearAllStickers = () => {
      imageStickers.value = [];
      message.info('已清除所有贴纸');
    };
    
    const saveImageWithStickers = () => {
      if (previewImage.value) {
        // Save stickers to image
        // In a full implementation, you would:
        // 1. Render stickers onto the image using canvas
        // 2. Upload the modified image to backend
        // 3. Update the image record
        message.success(`已保存 ${imageStickers.value.length} 个贴纸`);
        showImagePreviewModal.value = false;
        
        // TODO: Implement canvas rendering and save logic
      }
    };

    // Watch for changes to advertisementImages array
    watch(advertisementImages, (newVal, oldVal) => {
      console.log('[WATCH] ========== advertisementImages CHANGED ==========');
      console.log('[WATCH] Old length:', oldVal?.length || 0);
      console.log('[WATCH] New length:', newVal.length);
      console.log('[WATCH] New images:', newVal.map(img => ({ id: img.id, filename: img.filename })));
      console.log('[WATCH] ========================================');
    }, { deep: true });

    // Initialize lazy loading for images
    onMounted(async () => {
      console.log('[MOUNTED] Component mounted, loading images...');
      console.log('[MOUNTED] Props - advertisementTaskId:', props.advertisementTaskId, 'ruleCardId:', props.ruleCardId);
      
      // If advertisementTaskId prop is provided, load task data as context
      if (props.advertisementTaskId) {
        console.log('[MOUNTED] Advertisement task mode, loading task:', props.advertisementTaskId);
        await loadAdvertisementTask();
        // Do NOT skip steps - let user go through normal flow
        // Task data will be available when they reach step 3
      }
      
      // If ruleCardId prop is provided, load the specific rule card data
      if (props.ruleCardId) {
        console.log('[MOUNTED] Loading rule card:', props.ruleCardId);
        await loadRuleCard();
      }
      
      // Always load images for normal participation flow
      await loadImages();
      
      loadLLMModels(); // Load connected models from localStorage
      loadPromptTemplates(); // Load prompt templates from localStorage
      console.log('[MOUNTED] Initial load complete, advertisement count:', advertisementImages.value.length);
      
      // Setup Intersection Observer for lazy loading
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              const img = entry.target as HTMLImageElement;
              const src = img.getAttribute('data-src');
              if (src) {
                img.src = src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
              }
            }
          });
        },
        {
          rootMargin: '50px',
        }
      );

      // Observe all lazy images
      setTimeout(() => {
        document.querySelectorAll('.lazy-image').forEach((img) => {
          observer.observe(img);
        });
      }, 100);
    });

    // Reload models when component is reactivated (e.g., navigating back from LLM Models page)
    onActivated(() => {
      console.log('[ACTIVATED] Component reactivated, reloading LLM models...');
      loadLLMModels(); // Refresh models from localStorage
    });

    return {
      step,
      selectedRegularImagesSet,
      selectedAdvertisementImagesSet,
      selectedRuleImagesSet,
      selectedRuleImageIds,
      unusedRegularImages,
      advertisementImages,
      isAdImageSelected,
      showAddAdvertisementModal,
      showGeneratedPromptModal,
      showPreviewPromptModal,
      generatedPrompt,
      previewPromptData,
      generating,
      posting,
      confirmAndGenerate,
      cancelPreview,
      publishPost,
      isPasteAreaActive,
      pasteAreaFocused,
      pastedImages,
      uploadingCount,
      showPastePreview,
      isReloading,
      showDebugPanel,
      renderKey,
      debugInfo,
      formData,
      rules,
      llmModelOptions,
      promptTemplateOptions,
      selectedTemplate,
      applyTemplate,
      advertisementTask,
      uploadUrl,
      pasteDiv,
      // Image preview/edit modal
      showImagePreviewModal,
      previewImage,
      previewImageStyle,
      currentPreviewIndex,
      stickerCategory,
      availableStickers,
      imageStickers,
      imageCanvas,
      imageZoom,
      imageRotation,
      zoomIn,
      zoomOut,
      resetZoom,
      fitToScreen,
      rotateLeft,
      rotateRight,
      getImageUrl,
      toggleRegularImage,
      toggleAdvertisementImage,
      nextStep,
      prevStep,
      loadImages,
      handleUploadFinish,
      generatePrompt,
      getSelectedImages,
      copyGeneratedPrompt,
      openImagePreview,
      navigatePreview,
      resetPreview,
      startDragPreview,
      handleDragPreview,
      endDragPreview,
      handleWheelPreview,
      addStickerToImage,
      selectSticker,
      removeSticker,
      startResize,
      startRotate,
      clearAllStickers,
      saveImageWithStickers,
      handleKeyDown,
      focusPasteDiv,
      handlePasteAreaClick,
      handleModalClose,
      toggleDebugPanel,
      testAddImage,
      forceReloadImages,
      handleClipboardPaste,
      handleImageError,
      // Icons
      CloseOutline,
    };
  },
});
</script>

<style scoped>
.participation-process {
  max-width: 1400px; /* Increased max width for more content */
  margin: 0 auto;
  padding: 20px;
}

/* Responsive container width */
@media (min-width: 1600px) {
  .participation-process {
    max-width: 1600px; /* Even wider on large screens */
  }
}

@media (min-width: 1920px) {
  .participation-process {
    max-width: 1800px; /* Maximum width for ultra-wide screens */
  }
}

.step-container {
  margin-bottom: 40px;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.step-header h2 {
  margin: 0;
}

.debug-panel {
  background: #f0f9ff;
  border: 2px solid #3b82f6;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
  font-family: monospace;
}

.debug-panel h3 {
  margin: 0 0 12px 0;
  color: #1e40af;
  font-size: 16px;
}

.debug-item {
  margin-bottom: 8px;
  line-height: 1.6;
}

.debug-warning {
  background: #fef3c7;
  border: 1px solid #f59e0b;
  border-radius: 4px;
  padding: 8px;
  margin: 12px 0;
  color: #92400e;
}

.image-card {
  margin-bottom: 20px;
  min-height: 300px;
}

.image-card :deep(.n-card__content) {
  padding: 0px !important;
}

/* Optimized scrolling container with increased visible area */
.image-grid-container {
  max-height: calc(100vh - 280px); /* Dynamic height based on viewport */
  min-height: 650px; /* Minimum height to show more images */
  overflow-y: auto;
  overflow-x: hidden;
  /* Enable GPU acceleration for smooth scrolling */
  will-change: scroll-position;
  -webkit-overflow-scrolling: touch;
  /* Optimize scrollbar rendering */
  scrollbar-width: thin;
  scrollbar-color: #888 #f1f1f1;
  /* Account for scrollbar by using border-box */
  box-sizing: border-box;
  width: 100%;
}

/* Responsive height adjustments */
@media (min-height: 900px) {
  .image-grid-container {
    min-height: 750px; /* More space on tall screens */
  }
}

@media (min-height: 1080px) {
  .image-grid-container {
    min-height: 850px; /* Even more space on very tall screens */
  }
}

.image-grid-container::-webkit-scrollbar {
  width: 8px;
}

.image-grid-container::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.image-grid-container::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

.image-grid-container::-webkit-scrollbar-thumb:hover {
  background: #555;
}

.image-grid {
  display: grid;
  /* Fixed 2 columns for better image display */
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  padding: 4px;
  /* Optimize grid rendering */
  contain: layout style paint;
  width: 100%;
  box-sizing: border-box;
}

/* Responsive grid columns - adjust for smaller screens */
@media (max-width: 767px) {
  .image-grid {
    grid-template-columns: repeat(1, 1fr);
    gap: 8px;
    padding: 4px;
  }
}

@media (min-width: 768px) and (max-width: 1023px) {
  .image-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    padding: 4px;
  }
}

@media (min-width: 1024px) {
  .image-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    padding: 4px;
  }
}

.image-item {
  cursor: pointer;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  will-change: transform;
  contain: layout style paint;
  position: relative;
}

.image-item:hover {
  border-color: #165dff;
  box-shadow: 0 4px 12px rgba(22, 93, 255, 0.15);
}

.image-item.selected {
  border-color: #165dff;
  box-shadow: 0 4px 12px rgba(22, 93, 255, 0.25);
}

.preview-image {
  width: 100%;
  height: auto;
  max-width: 100%;
  max-height: 400px;
  object-fit: contain; /* Contain to show full image without cropping */
  object-position: center;
  display: block;
  background: #f0f0f0;
}

/* No responsive height changes needed - aspect ratio handles it */

/* Lazy loading images */
.lazy-image {
  opacity: 0;
  transition: opacity 0.3s ease-in;
}

.lazy-image[src] {
  opacity: 1;
}

.image-info {
  padding: 8px;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.image-info-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.image-name {
  font-size: 12px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.image-edit-btn {
  margin-top: 4px;
  font-size: 12px;
  transition: all 0.2s;
}

.image-edit-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(22, 93, 255, 0.3);
}

.two-column {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.add-image-action {
  text-align: center;
  margin-top: 16px;
}

.prompt-card {
  margin-bottom: 20px;
}

.step-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.generated-prompt {
  margin-bottom: 20px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.modal-footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  width: 100%;
}

/* 粘贴区域样式 */
.paste-container {
  padding: 20px;
  outline: none;
}

.upload-button {
  width: 100%;
  margin-bottom: 20px;
}

.paste-divider {
  display: flex;
  align-items: center;
  margin: 20px 0;
}

.paste-divider::before,
.paste-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #e5e5e5;
}

.divider-text {
  padding: 0 16px;
  color: #666;
  font-size: 14px;
}

.paste-area {
  border: 2px dashed #e5e5e5;
  border-radius: 12px;
  padding: 40px 20px;
  text-align: center;
  background: #fafafa;
  transition: all 0.3s ease;
  cursor: pointer;
}

.paste-area:hover {
  border-color: #165dff;
  background: #f0f6ff;
}

.paste-area-active {
  border-color: #165dff;
  background: #e6f7ff;
  box-shadow: 0 0 0 4px rgba(22, 93, 255, 0.1);
}

.paste-area-focused {
  border-color: #165dff;
  background: #f0f6ff;
  box-shadow: 0 0 0 4px rgba(22, 93, 255, 0.15);
  outline: none;
}

.click-hint {
  color: #165dff;
  font-weight: 500;
  font-size: 15px !important;
  margin-top: 8px !important;
}

.paste-ready {
  color: #52c41a;
  font-weight: 600;
  font-size: 15px !important;
  margin-top: 8px !important;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.paste-icon {
  margin-bottom: 16px;
}

.paste-instructions h3 {
  margin: 0 0 8px 0;
  color: #1f2937;
  font-size: 18px;
  font-weight: 600;
}

.paste-instructions p {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
  line-height: 1.5;
}

.paste-hint {
  font-size: 12px !important;
  color: #999 !important;
  margin-top: 8px !important;
}

/* Pasted Images Preview */
.pasted-images-preview {
  margin-top: 24px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.preview-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.uploading-indicator {
  font-size: 14px;
  color: #165dff;
  font-weight: 500;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
}

.preview-item {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid #e5e7eb;
  transition: all 0.3s ease;
}

.preview-item.status-uploading {
  border-color: #165dff;
  box-shadow: 0 0 0 3px rgba(22, 93, 255, 0.1);
}

.preview-item.status-success {
  border-color: #52c41a;
  box-shadow: 0 0 0 3px rgba(82, 196, 26, 0.1);
}

.preview-item.status-error {
  border-color: #ff4d4f;
  box-shadow: 0 0 0 3px rgba(255, 77, 79, 0.1);
}

.preview-item.fading-out {
  animation: fadeOutUp 0.4s ease-out forwards;
}

@keyframes fadeOutUp {
  0% {
    opacity: 1;
    transform: translateY(0);
  }
  100% {
    opacity: 0;
    transform: translateY(-20px);
  }
}

.preview-image-container {
  position: relative;
  width: 100%;
  height: 100px;
  overflow: hidden;
}

.preview-image-container img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.upload-overlay,
.success-overlay,
.error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
}

.loading-icon {
  animation: spin 1s linear infinite;
  color: white;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.preview-info {
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.preview-name {
  font-size: 12px;
  color: #374151;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.error-message {
  font-size: 11px;
  color: #ff4d4f;
  line-height: 1.3;
}

/* 空状态样式 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  background: #fafafa;
  border-radius: 8px;
  border: 1px dashed #e5e5e5;
}

.empty-icon {
  margin-bottom: 16px;
}

.empty-text {
  color: #666;
}

.empty-title {
  font-size: 16px;
  font-weight: 500;
  margin: 0 0 8px 0;
  color: #333;
}

.empty-description {
  font-size: 14px;
  margin: 0;
  color: #666;
  line-height: 1.5;
}

/* Mobile and tablet responsive adjustments */
@media (max-width: 768px) {
  .participation-process {
    max-width: 100%;
    padding: 12px;
  }
  
  .image-grid-container {
    max-height: calc(100vh - 320px); /* Adjust for mobile header/footer */
    min-height: 450px; /* Smaller minimum on mobile */
  }
  
  .image-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 10px;
    padding: 8px;
  }
  
  .preview-image {
    height: 110px; /* Smaller images on mobile */
  }
  
  .two-column {
    grid-template-columns: 1fr;
  }
  
  .step-actions {
    flex-direction: column;
  }
  
  .paste-area {
    padding: 30px 15px;
  }
  
  .paste-instructions h3 {
    font-size: 16px;
  }
  
  .paste-instructions p {
    font-size: 13px;
  }
  
  .empty-state {
    padding: 40px 16px;
  }
  
  .empty-title {
    font-size: 15px;
  }
  
  .empty-description {
    font-size: 13px;
  }
}

/* Tablet landscape adjustments */
@media (min-width: 769px) and (max-width: 1023px) {
  .image-grid-container {
    max-height: calc(100vh - 300px);
    min-height: 550px;
  }
  
  .participation-process {
    max-width: 95%;
  }
}

/* Small mobile devices */
@media (max-width: 480px) {
  .image-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 8px;
  }
  
  .preview-image {
    height: 90px;
  }
  
  .image-grid-container {
    min-height: 400px;
  }
}

/* Simple Preview Modal Styles */
.simple-preview-content {
  display: flex;
  flex-direction: column;
  height: calc(90vh - 140px);
  gap: 16px;
}

.simple-preview-content .preview-image-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: #f5f5f5;
  border-radius: 8px;
  height: auto !important;
  min-height: 0;
}

.simple-preview-content .preview-image-container img {
  width: auto !important;
  height: auto !important;
  max-width: 100%;
  max-height: 100%;
  object-fit: contain !important;
  display: block;
}

.preview-large-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  cursor: grab;
}

.preview-large-image:active {
  cursor: grabbing;
}

.simple-preview-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
}

.control-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.control-label {
  font-size: 14px;
  font-weight: 500;
  color: #666;
}

.control-divider {
  width: 1px;
  height: 24px;
  background: #e5e7eb;
}

/* Old Editor Styles (keep for compatibility) */
.image-editor-content {
  padding: 0;
  height: calc(95vh - 140px);
  min-height: 600px;
}

.editor-layout {
  display: flex;
  gap: 16px;
  height: 100%;
  padding: 12px;
}

.sticker-panel {
  flex-shrink: 0;
  width: 200px;
}

.sticker-panel h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #333;
}

.sticker-categories {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.stickers-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  max-height: calc(100% - 200px);
  overflow-y: auto;
  padding: 4px;
}

.sticker-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px 8px;
  background: #f5f7fa;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.sticker-item:hover {
  background: #e5e7eb;
  border-color: #165dff;
  transform: scale(1.05);
}

.sticker-icon {
  font-size: 32px;
  margin-bottom: 4px;
}

.sticker-name {
  font-size: 11px;
  color: #666;
}

.editor-note {
  margin-top: 16px;
  padding: 12px;
  background: #f0f9ff;
  border-radius: 6px;
}

.editor-note p {
  margin: 0 0 8px 0;
}

.image-canvas-wrapper {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

.image-canvas {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.canvas-image {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
  display: block;
}

.stickers-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

/* Zoom Controls */
.zoom-controls {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 100;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 6px;
  padding: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
}

/* Placed Stickers */
.placed-sticker {
  position: absolute;
  pointer-events: all;
  cursor: move;
  user-select: none;
  transition: filter 0.2s;
}

.placed-sticker:hover {
  filter: drop-shadow(0 0 8px rgba(22, 93, 255, 0.5));
}

.placed-sticker.selected {
  filter: drop-shadow(0 0 12px rgba(22, 93, 255, 0.8));
}

.sticker-emoji {
  display: block;
  line-height: 1;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

/* Sticker Controls */
.sticker-controls {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 120%;
  height: 120%;
  pointer-events: none;
}

.control-btn,
.control-handle {
  position: absolute;
  pointer-events: all;
  width: 24px;
  height: 24px;
  background: white;
  border: 2px solid #165dff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.control-btn:hover,
.control-handle:hover {
  background: #165dff;
  color: white;
  transform: scale(1.2);
}

/* Delete button - top left */
.delete-btn {
  top: -12px;
  left: -12px;
  background: #ff4d4f;
  border-color: #ff4d4f;
  color: white;
}

.delete-btn:hover {
  background: #cf1322;
  border-color: #cf1322;
}

/* Resize handle - bottom right */
.resize-handle {
  bottom: -12px;
  right: -12px;
  cursor: nwse-resize;
}

/* Rotate handle - top right */
.rotate-handle {
  top: -12px;
  right: -12px;
  cursor: grab;
}

.rotate-handle:active {
  cursor: grabbing;
}

/* Mobile Responsive Styles */
@media (max-width: 1024px) {
  .step-indicator {
    gap: 16px;
  }
  
  .step-item {
    font-size: 13px;
  }
}

@media (max-width: 768px) {
  .participation-header h2 {
    font-size: 20px;
  }
  
  .step-indicator {
    gap: 12px;
    padding: 12px 8px;
  }
  
  .step-item {
    font-size: 12px;
  }
  
  .step-number {
    width: 24px;
    height: 24px;
    font-size: 12px;
  }
  
  .image-grid-container {
    padding: 8px;
    gap: 12px;
  }
  
  .image-card {
    gap: 8px;
  }
  
  .image-preview-section {
    height: 250px;
  }
  
  .image-info {
    padding: 8px;
  }
  
  .filename {
    font-size: 12px;
  }
  
  .image-tag {
    font-size: 11px;
    padding: 2px 6px;
  }
  
  .edit-button {
    padding: 6px 10px;
    font-size: 12px;
  }
  
  /* Modal adjustments for mobile */
  .simple-preview-content {
    height: calc(90vh - 120px);
  }
  
  .simple-preview-controls {
    flex-direction: column;
    gap: 8px;
  }
  
  .control-section {
    width: 100%;
    justify-content: center;
  }
  
  /* Touch-friendly buttons */
  .n-button {
    min-height: 44px !important;
  }
}

/* Extra small devices (phones in portrait) */
@media (max-width: 480px) {
  .participation-header h2 {
    font-size: 18px;
  }
  
  .step-indicator {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .step-item {
    font-size: 11px;
    min-width: 100px;
  }
  
  .image-grid-container {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    padding: 4px;
  }
  
  .image-preview-section {
    height: 180px;
  }
  
  .image-info {
    padding: 6px;
  }
  
  .filename {
    font-size: 11px;
  }
  
  .edit-button {
    width: 100%;
    justify-content: center;
  }
  
  /* Prompt editor adjustments */
  .prompt-editor textarea {
    font-size: 14px;
  }
  
  .actions {
    flex-direction: column;
    gap: 8px;
  }
  
  .actions .n-button {
    width: 100%;
  }
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

.image-wrapper {
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

/* Preview Prompt Modal Styles */
.preview-prompt-content {
  max-height: 70vh;
  overflow-y: auto;
}

.preview-section {
  margin-bottom: 20px;
}

.preview-label {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 10px;
  color: #333;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* XHS-Style Preview */
.xhs-preview-container {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

.xhs-preview-card {
  width: 100%;
  max-width: 500px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.xhs-image-gallery {
  position: relative;
  width: 100%;
  padding-top: 100%; /* 1:1 aspect ratio */
  background: #f5f5f5;
  overflow: hidden;
}

.xhs-main-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.xhs-main-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.xhs-placeholder-image {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #999;
  background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%);
}

.xhs-image-count {
  position: absolute;
  bottom: 12px;
  right: 12px;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

.xhs-content-section {
  padding: 16px 20px;
}

.xhs-prompt-text {
  font-size: 15px;
  line-height: 1.8;
  color: #333;
  margin-bottom: 12px;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.xhs-hashtags {
  font-size: 14px;
  color: #ff2442;
  font-weight: 500;
  margin-top: 8px;
  line-height: 1.6;
}

.xhs-actions {
  padding: 12px 20px;
  border-top: 1px solid #f0f0f0;
  background: #fafafa;
}

/* Step 4 Preview Layout */
.preview-section {
  margin-bottom: 24px;
}

.preview-section h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #333;
}

.image-grid-preview {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
}

.preview-image-item {
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid #e0e0e6;
}

.preview-image-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-more {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  border-radius: 8px;
  border: 2px dashed #d0d0d6;
  font-size: 16px;
  font-weight: 600;
  color: #666;
}

.generated-text-preview {
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #e0e0e6;
  font-size: 14px;
  line-height: 1.8;
  color: #333;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 400px;
  overflow-y: auto;
}

.generated-text-editor :deep(textarea) {
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 14px;
  line-height: 1.8;
  color: #333;
}

.task-info-preview {
  padding: 12px 16px;
  background: #f5f8ff;
  border-radius: 8px;
  border-left: 3px solid #18a058;
  font-size: 13px;
  line-height: 1.8;
}

.task-info-preview > div {
  margin-bottom: 8px;
}

.task-info-preview > div:last-child {
  margin-bottom: 0;
}

</style>