<template>
  <n-modal 
    :show="internalShow"
    @update:show="handleShowChange"
    preset="card"
    title="选择服务器目录"
    :mask-closable="true"
    :bordered="false"
    style="width: 600px;"
  >
    <div class="directory-picker">
      <!-- Common Directories Quick Access -->
      <div class="quick-access">
        <div class="quick-access-label">快速访问:</div>
        <n-space>
          <n-button 
            v-for="dir in commonDirectories" 
            :key="dir.path"
            size="small"
            @click="navigateTo(dir.path)"
          >
            {{ dir.name }}
          </n-button>
        </n-space>
      </div>

      <!-- Current Path Display -->
      <div class="current-path">
        <n-input 
          v-model:value="currentPath" 
          readonly
          :placeholder="currentPath || '选择目录'"
        >
          <template #prefix>
            <n-icon><FolderOpenOutline /></n-icon>
          </template>
        </n-input>
      </div>

      <!-- Navigation -->
      <div class="navigation">
        <n-button 
          :disabled="!parentPath" 
          @click="navigateUp"
          size="small"
        >
          <template #icon>
            <n-icon><ArrowUpOutline /></n-icon>
          </template>
          上级目录
        </n-button>
        <n-button 
          @click="refresh"
          size="small"
        >
          <template #icon>
            <n-icon><RefreshOutline /></n-icon>
          </template>
          刷新
        </n-button>
        <n-button 
          @click="showCreateDialog = true"
          size="small"
          type="primary"
          ghost
        >
          <template #icon>
            <n-icon><AddOutline /></n-icon>
          </template>
          新建文件夹
        </n-button>
      </div>

      <!-- Directory List -->
      <div class="directory-list">
        <n-spin :show="loading">
          <n-empty 
            v-if="!loading && directories.length === 0" 
            description="此目录下没有子文件夹"
          />
          <div v-else class="directory-items">
            <div 
              v-for="dir in directories" 
              :key="dir.path"
              class="directory-item"
              :class="{ selected: selectedPath === dir.path }"
              @click="selectDirectory(dir)"
              @dblclick="navigateTo(dir.path)"
            >
              <n-icon size="20"><FolderOutline /></n-icon>
              <span class="directory-name">{{ dir.name }}</span>
            </div>
          </div>
        </n-spin>
      </div>

      <!-- Selected Path Display -->
      <div v-if="selectedPath" class="selected-path">
        <strong>已选择:</strong> {{ selectedPath }}
      </div>

      <!-- Actions -->
      <div class="actions">
        <n-space justify="end">
          <n-button @click="cancel">取消</n-button>
          <n-button type="primary" @click="confirm" :disabled="!selectedPath">
            确定
          </n-button>
        </n-space>
      </div>

      <!-- Error Display -->
      <n-alert 
        v-if="error" 
        type="error" 
        :title="error"
        closable
        @close="error = ''"
        style="margin-top: 12px;"
      />
    </div>

    <!-- Create Directory Dialog -->
    <n-modal
      :show="showCreateDialog"
      @update:show="showCreateDialog = $event"
      preset="dialog"
      title="新建文件夹"
      positive-text="创建"
      negative-text="取消"
      @positive-click="createDirectory"
    >
      <n-input 
        v-model:value="newDirectoryName" 
        placeholder="输入文件夹名称"
        @keyup.enter="createDirectory"
      />
    </n-modal>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { NModal, NInput, NButton, NIcon, NSpace, NSpin, NEmpty, NAlert, useMessage } from 'naive-ui';
import { 
  FolderOpenOutline, 
  FolderOutline,
  ArrowUpOutline,
  RefreshOutline,
  AddOutline
} from '@vicons/ionicons5';
import api from '@/api';

interface Directory {
  name: string;
  path: string;
}

interface Props {
  show: boolean;
  initialPath?: string;
}

interface Emits {
  (e: 'update:show', value: boolean): void;
  (e: 'select', path: string): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const message = useMessage();

// Internal show state
const internalShow = ref(props.show);

const currentPath = ref('');
const parentPath = ref<string | null>(null);
const directories = ref<Directory[]>([]);
const commonDirectories = ref<Directory[]>([]);
const selectedPath = ref('');
const loading = ref(false);
const error = ref('');
const showCreateDialog = ref(false);
const newDirectoryName = ref('');

// Watch for prop changes
watch(() => props.show, (newVal) => {
  internalShow.value = newVal;
  if (newVal) {
    init();
  }
});

// Handle show change from modal
const handleShowChange = (value: boolean) => {
  internalShow.value = value;
  emit('update:show', value);
};

const init = async () => {
  // Load common directories
  await loadCommonDirectories();
  
  // Navigate to initial path or home
  const startPath = props.initialPath || '';
  if (startPath) {
    await navigateTo(startPath);
  } else if (commonDirectories.value.length > 0) {
    await navigateTo(commonDirectories.value[0].path);
  }
};

const loadCommonDirectories = async () => {
  try {
    const response = await api.get('/filesystem/common-directories');
    if (response.data.success) {
      commonDirectories.value = response.data.data.directories;
    }
  } catch (err) {
    console.error('Failed to load common directories:', err);
  }
};

const navigateTo = async (path: string) => {
  loading.value = true;
  error.value = '';
  
  try {
    const response = await api.post('/filesystem/list-directories', { path });
    
    if (response.data.success) {
      const data = response.data.data;
      currentPath.value = data.current_path;
      parentPath.value = data.parent_path;
      directories.value = data.directories;
      selectedPath.value = data.current_path;
    } else {
      error.value = response.data.message || '加载目录失败';
    }
  } catch (err: any) {
    error.value = err?.response?.data?.message || '加载目录失败';
    console.error('Failed to navigate to directory:', err);
  } finally {
    loading.value = false;
  }
};

const navigateUp = () => {
  if (parentPath.value) {
    navigateTo(parentPath.value);
  }
};

const refresh = () => {
  if (currentPath.value) {
    navigateTo(currentPath.value);
  }
};

const selectDirectory = (dir: Directory) => {
  selectedPath.value = dir.path;
};

const createDirectory = async () => {
  if (!newDirectoryName.value.trim()) {
    message.warning('请输入文件夹名称');
    return;
  }
  
  const newPath = `${currentPath.value}/${newDirectoryName.value.trim()}`;
  
  try {
    const response = await api.post('/filesystem/create-directory', { path: newPath });
    
    if (response.data.success) {
      message.success('文件夹创建成功');
      showCreateDialog.value = false;
      newDirectoryName.value = '';
      await refresh();
    } else {
      message.error(response.data.message || '创建失败');
    }
  } catch (err: any) {
    message.error(err?.response?.data?.message || '创建失败');
  }
};

const confirm = () => {
  if (selectedPath.value) {
    emit('select', selectedPath.value);
    emit('update:show', false);
  }
};

const cancel = () => {
  emit('update:show', false);
};
</script>

<style scoped>
.directory-picker {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.quick-access {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 6px;
}

.quick-access-label {
  font-weight: 500;
  color: #666;
  white-space: nowrap;
}

.current-path {
  margin-bottom: 8px;
}

.navigation {
  display: flex;
  gap: 8px;
}

.directory-list {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  min-height: 300px;
  max-height: 400px;
  overflow-y: auto;
  padding: 8px;
}

.directory-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.directory-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s;
}

.directory-item:hover {
  background: #f0f0f0;
}

.directory-item.selected {
  background: #e6f7ff;
  border: 1px solid #91d5ff;
}

.directory-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-path {
  padding: 8px 12px;
  background: #f9f9f9;
  border-radius: 4px;
  font-size: 13px;
  word-break: break-all;
}

.actions {
  border-top: 1px solid #e0e0e0;
  padding-top: 16px;
}
</style>
