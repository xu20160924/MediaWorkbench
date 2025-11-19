<template>
  <div class="image-participation">
    <div class="header">
      <n-button type="primary" @click="goBack" class="back-button">
        <template #icon>
          <n-icon><arrow-back /></n-icon>
        </template>
        返回
      </n-button>
      <h1>参与图片规则</h1>
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
          <n-button @click="loadImage">重试</n-button>
        </template>
      </n-result>
    </div>

    <div class="content" v-else>
      <n-card :title="image?.name || '未命名图片'" class="image-card">
        <div class="image-container">
          <div class="image-type-indicator">
            <n-icon :component="getImageTypeIcon(image?.image_type)" />
            <span>{{ getImageTypeLabel(image?.image_type) }}</span>
          </div>
          <img :src="getImageUrl(image)" alt="参与图片" class="preview-image" />
        </div>
        
        <n-divider />
        
        <n-form ref="formRef" :model="formData" :rules="rules">
          <n-form-item label="规则名称" path="ruleName">
            <n-input v-model:value="formData.ruleName" placeholder="请输入规则名称" />
          </n-form-item>
          
          <n-form-item label="规则描述" path="description">
            <n-input
              v-model:value="formData.description"
              type="textarea"
              :autosize="{ minRows: 3 }"
              placeholder="请输入规则描述"
            />
          </n-form-item>
          
          <n-form-item label="生效时间" path="effectiveTime">
            <n-date-picker
              v-model:value="formData.effectiveTime"
              type="datetime"
              placeholder="请选择生效时间"
              style="width: 100%"
            />
          </n-form-item>
          
          <n-form-item label="过期时间" path="expiryTime">
            <n-date-picker
              v-model:value="formData.expiryTime"
              type="datetime"
              placeholder="请选择过期时间"
              style="width: 100%"
            />
          </n-form-item>
          
          <n-form-item label="优先级" path="priority">
            <n-input-number v-model:value="formData.priority" :min="1" :max="10" />
          </n-form-item>
          
          <n-form-item label="状态" path="enabled">
            <n-switch v-model:value="formData.enabled" />
          </n-form-item>
          
          <div class="form-actions">
            <n-button type="primary" @click="handleSubmit" :loading="submitting">
              {{ submitting ? '提交中...' : '提交' }}
            </n-button>
            <n-button @click="goBack" :disabled="submitting">取消</n-button>
          </div>
        </n-form>
      </n-card>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowBack, ImagesOutline, DocumentTextOutline, MegaphoneOutline } from '@vicons/ionicons5';
import { useMessage } from 'naive-ui';
import api from '@/api';

interface ImageItem {
  id: string | number;
  name: string;
  url?: string;
  local_path?: string;
  image_type?: string;
  participated?: boolean;
  variables?: Record<string, any>;
}

export default defineComponent({
  name: 'ImageParticipation',
  components: {
    ArrowBack,
    ImagesOutline,
    DocumentTextOutline,
    MegaphoneOutline,
  },
  setup() {
    const route = useRoute();
    const router = useRouter();
    const message = useMessage();
    
    const imageId = ref<string | number>('');
    const image = ref<ImageItem | null>(null);
    const loading = ref(true);
    const error = ref('');
    const submitting = ref(false);
    
    const formRef = ref();
    const formData = ref({
      ruleName: '',
      description: '',
      effectiveTime: Date.now(),
      expiryTime: Date.now() + 30 * 24 * 60 * 60 * 1000, // 默认30天后过期
      priority: 5,
      enabled: true,
    });
    
    const rules = {
      ruleName: [
        { required: true, message: '请输入规则名称', trigger: 'blur' },
        { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' },
      ],
      description: [
        { required: true, message: '请输入规则描述', trigger: 'blur' },
      ],
      effectiveTime: [
        { required: true, message: '请选择生效时间', trigger: 'blur' },
      ],
      expiryTime: [
        { required: true, message: '请选择过期时间', trigger: 'blur' },
        {
          validator: (rule: any, value: number) => {
            return value > formData.value.effectiveTime;
          },
          message: '过期时间必须晚于生效时间',
          trigger: 'blur',
        },
      ],
    };
    
    const getImageTypeIcon = (type: string | undefined): any => {
      if (!type) return ImagesOutline;
      switch (type) {
        case 'advertising_campaign':
          return MegaphoneOutline;
        case 'advertising_rule':
          return DocumentTextOutline;
        default:
          return ImagesOutline;
      }
    };
    
    const getImageTypeLabel = (type: string | undefined): string => {
      if (!type) return '普通图片';
      switch (type) {
        case 'advertising_campaign':
          return '活动配图';
        case 'advertising_rule':
          return '广告规则';
        case 'general':
        default:
          return '普通图片';
      }
    };
    
    const getImageUrl = (img: ImageItem | null): string => {
      if (!img) return '';
      if (img.img_url) return img.img_url;
      if (img.url) return img.url;
      
      const imagePath = img.file_path || img.local_path;
      if (!imagePath) return '';
      
      const devStaticBase = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5002/api';
      
      let normalized = imagePath.replace(/\\/g, '/');
      
      // If it's a backend path starting with 'upload/' or 'output/', strip that part
      if (normalized.startsWith('upload/') || normalized.startsWith('output/')) {
        normalized = normalized.substring(normalized.indexOf('/') + 1);
      }
      
      // Handle upload paths
      const uploadMatch = normalized.match(/^(upload\/images\/|\/uploads\/)(.*)$/);
      if (uploadMatch) {
        const url = `${devStaticBase}/images/uploads/${uploadMatch[2]}`;
        return url;
      }
      
      // Handle output paths
      const outputMatch = normalized.match(/^(output\/images\/|\/output\/)(.*)$/);
      if (outputMatch) {
        const url = `${devStaticBase}/images/output/${outputMatch[2]}`;
        return url;
      }
      
      // Fallback to general images endpoint
      return `${devStaticBase}/images/${normalized}`;
    };
    
    const loadImage = async () => {
      if (!imageId.value) {
        error.value = '无效的图片ID';
        loading.value = false;
        return;
      }
      
      try {
        loading.value = true;
        error.value = '';
        const response = await api.get(`/images/${imageId.value}`);
        image.value = response.data;
        
        // Pre-fill form with existing data if available
        if (image.value?.variables?.participation) {
          formData.value = {
            ...formData.value,
            ...image.value.variables.participation,
          };
        }
      } catch (e: any) {
        console.error('Failed to load image:', e);
        error.value = e.response?.data?.message || '加载图片信息失败';
      } finally {
        loading.value = false;
      }
    };
    
    const handleSubmit = async () => {
      try {
        await formRef.value?.validate();
        
        submitting.value = true;
        
        // Update the image's participation status and data
        await api.post(`/images/participate/${imageId.value}`, {
          participated: true,
          participation: formData.value,
        }, {
          headers: { 'Content-Type': 'application/json' },
        });
        
        message.success('参与成功');
        goBack();
      } catch (e: any) {
        if (e.name !== 'ValidationError') {
          console.error('Failed to submit participation:', e);
          message.error(e.response?.data?.message || '提交失败，请重试');
        }
      } finally {
        submitting.value = false;
      }
    };
    
    const goBack = () => {
      router.push({ name: 'images' });
    };
    
    onMounted(() => {
      imageId.value = route.params.id as string;
      loadImage();
    });
    
    return {
      image,
      loading,
      error,
      formRef,
      formData,
      rules,
      submitting,
      getImageUrl,
      loadImage,
      handleSubmit,
      goBack,
    };
  },
});
</script>

<style scoped>
.image-participation {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

.header h1 {
  margin: 0 0 0 16px;
  flex-grow: 1;
}

.back-button {
  margin-right: 16px;
}

.content {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.image-card {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
}

.image-container {
  display: flex;
  justify-content: center;
  margin: 20px 0;
  position: relative;
}

.image-type-indicator {
  position: absolute;
  top: 10px;
  left: 10px;
  background-color: rgba(255, 255, 255, 0.9);
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  color: #666;
}

.image-type-indicator .n-icon {
  font-size: 16px;
  color: #165dff;
}

.preview-image {
  max-width: 100%;
  max-height: 400px;
  object-fit: contain;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}
</style>
