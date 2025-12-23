  <template>
  <div class="crawler-management">
    <n-card title="小红书广告任务爬虫" class="main-card">
      <template #header-extra>
        <n-space>
          <n-tag :type="statusType" size="small">
            {{ statusText }}
          </n-tag>
        </n-space>
      </template>

      <n-tabs type="line" animated>
        <!-- Configuration Tab -->
        <n-tab-pane name="config" tab="爬虫配置">
          <n-form
            ref="formRef"
            :model="config"
            label-placement="left"
            label-width="140"
            class="config-form"
          >
            <!-- Account Selection Section -->
            <n-divider title-placement="left">账户选择</n-divider>
            
            <n-form-item label="小红书账户" path="selectedUserId">
              <n-select
                v-model:value="config.selectedUserId"
                :options="userOptions"
                placeholder="请选择已配置的小红书账户"
                :loading="loadingUsers"
                filterable
                clearable
                style="width: 100%"
              >
                <template #empty>
                  <div style="padding: 12px; text-align: center; color: #999;">
                    暂无账户，请先在"小红书账户"页面添加
                  </div>
                </template>
              </n-select>
              <template #feedback>
                <n-space v-if="selectedUser" align="center" style="margin-top: 4px;">
                  <n-tag :type="selectedUser.status ? 'success' : 'warning'" size="small">
                    {{ selectedUser.status ? '正常' : '异常' }}
                  </n-tag>
                  <span style="color: #999; font-size: 12px;">
                    {{ selectedUser.nickname || selectedUser.username }}
                  </span>
                </n-space>
              </template>
            </n-form-item>

            <n-alert v-if="!config.selectedUserId" type="info" style="margin-bottom: 16px;">
              请选择一个小红书账户，系统将自动使用该账户的认证信息进行爬取
            </n-alert>

            <!-- Crawl Settings Section -->
            <n-divider title-placement="left">爬取设置</n-divider>

            <n-form-item label="任务类型" path="taskType">
              <n-radio-group v-model:value="config.taskType">
                <n-radio-button value="submission">投稿活动</n-radio-button>
                <n-radio-button value="buyer">买手任务</n-radio-button>
              </n-radio-group>
            </n-form-item>

            <n-grid :cols="2" :x-gap="24">
              <n-gi>
                <n-form-item label="每页数量" path="pageSize">
                  <n-input-number
                    v-model:value="config.pageSize"
                    :min="1"
                    :max="50"
                    style="width: 100%"
                  />
                </n-form-item>
              </n-gi>
              <n-gi>
                <n-form-item label="最大页数" path="maxPages">
                  <n-input-number
                    v-model:value="config.maxPages"
                    :min="1"
                    :max="100"
                    placeholder="不限制"
                    style="width: 100%"
                  />
                </n-form-item>
              </n-gi>
            </n-grid>

            <n-grid :cols="2" :x-gap="24">
              <n-gi>
                <n-form-item label="列表页延迟(秒)" path="delay">
                  <div class="slider-with-hint">
                    <n-slider
                      v-model:value="config.delayRange"
                      range
                      :min="0.5"
                      :max="15"
                      :step="0.5"
                      :format-tooltip="(v) => `${v}s`"
                    />
                    <span class="range-hint">随机延迟: {{ config.delayRange[0] }}s - {{ config.delayRange[1] }}s</span>
                  </div>
                </n-form-item>
              </n-gi>
              <n-gi>
                <n-form-item label="详情页延迟(秒)" path="detailDelay">
                  <div class="slider-with-hint">
                    <n-slider
                      v-model:value="config.detailDelayRange"
                      range
                      :min="0.5"
                      :max="15"
                      :step="0.5"
                      :format-tooltip="(v) => `${v}s`"
                    />
                    <span class="range-hint">随机延迟: {{ config.detailDelayRange[0] }}s - {{ config.detailDelayRange[1] }}s</span>
                  </div>
                </n-form-item>
              </n-gi>
            </n-grid>

            <!-- Detail Page Options -->
            <n-divider title-placement="left">详情页选项</n-divider>

            <n-form-item label="详情页模式" path="detailFetchMode">
              <n-radio-group v-model:value="config.detailFetchMode">
                <n-radio-button value="none">不抓取</n-radio-button>
                <n-radio-button value="requests">快速(Requests)</n-radio-button>
                <n-radio-button value="browser">浏览器(Playwright)</n-radio-button>
              </n-radio-group>
            </n-form-item>

            <n-form-item label="功能选项">
              <n-space>
                <n-checkbox v-model:checked="config.extractRules">
                  提取规则卡片
                </n-checkbox>
                <n-checkbox v-model:checked="config.saveScreenshots">
                  保存截图
                </n-checkbox>
                <n-checkbox v-model:checked="config.saveToDatabase">
                  存入数据库
                </n-checkbox>
                <n-checkbox v-model:checked="config.cleanOutput">
                  清理存量数据
                </n-checkbox>
                <n-checkbox v-model:checked="config.includeParticipated">
                  包含已参与任务
                </n-checkbox>
                <n-checkbox v-model:checked="config.includeRecruit">
                  包含招募类任务
                </n-checkbox>
                <n-checkbox v-model:checked="config.verbose">
                  详细日志
                </n-checkbox>
              </n-space>
            </n-form-item>

            <!-- Action Buttons -->
            <div class="action-buttons">
              <n-space>
                <n-button type="primary" size="large" :loading="isRunning" @click="startCrawl">
                  <template #icon>
                    <n-icon><play-circle /></n-icon>
                  </template>
                  {{ isRunning ? '爬取中...' : '开始爬取' }}
                </n-button>
                <n-button v-if="isRunning" type="error" size="large" @click="stopCrawl">
                  <template #icon>
                    <n-icon><stop-circle /></n-icon>
                  </template>
                  停止
                </n-button>
                <n-button size="large" @click="saveConfig">
                  <template #icon>
                    <n-icon><save /></n-icon>
                  </template>
                  保存配置
                </n-button>
                <n-button size="large" @click="loadConfig">
                  <template #icon>
                    <n-icon><refresh /></n-icon>
                  </template>
                  重置
                </n-button>
              </n-space>
            </div>
          </n-form>
        </n-tab-pane>

        <!-- Execution Log Tab -->
        <n-tab-pane name="logs" tab="执行日志">
          <div class="log-container">
            <div class="log-toolbar">
              <n-space>
                <n-button size="small" @click="clearLogs">
                  <template #icon>
                    <n-icon><trash /></n-icon>
                  </template>
                  清空日志
                </n-button>
                <n-button size="small" @click="copyLogs">
                  <template #icon>
                    <n-icon><copy /></n-icon>
                  </template>
                  复制日志
                </n-button>
                <n-checkbox v-model:checked="autoScroll">自动滚动</n-checkbox>
              </n-space>
            </div>
            <div ref="logPanel" class="log-panel">
              <div
                v-for="(log, index) in logs"
                :key="index"
                :class="['log-entry', `log-${log.level}`]"
              >
                <span class="log-time">{{ log.time }}</span>
                <span class="log-level">{{ log.level.toUpperCase() }}</span>
                <span class="log-message">{{ log.message }}</span>
              </div>
              <div v-if="logs.length === 0" class="log-empty">
                暂无日志，点击"开始爬取"启动爬虫
              </div>
            </div>
          </div>
        </n-tab-pane>

        <!-- Results Tab -->
        <n-tab-pane name="results" tab="爬取结果">
          <div class="results-container">
            <!-- Statistics Cards -->
            <n-grid :cols="4" :x-gap="16" :y-gap="16" class="stats-grid">
              <n-gi>
                <n-card class="stat-card">
                  <n-statistic label="发现任务" :value="stats.tasksFound" />
                </n-card>
              </n-gi>
              <n-gi>
                <n-card class="stat-card">
                  <n-statistic label="有效任务" :value="stats.tasksFiltered" />
                </n-card>
              </n-gi>
              <n-gi>
                <n-card class="stat-card">
                  <n-statistic label="规则卡片" :value="stats.ruleCards" />
                </n-card>
              </n-gi>
              <n-gi>
                <n-card class="stat-card">
                  <n-statistic label="截图保存" :value="stats.screenshots" />
                </n-card>
              </n-gi>
            </n-grid>

            <!-- Last Crawl Info -->
            <n-card v-if="lastCrawlTime" title="上次爬取" size="small" class="last-crawl-card">
              <n-descriptions :column="3" label-placement="left">
                <n-descriptions-item label="时间">{{ lastCrawlTime }}</n-descriptions-item>
                <n-descriptions-item label="耗时">{{ lastCrawlDuration }}</n-descriptions-item>
                <n-descriptions-item label="状态">
                  <n-tag :type="lastCrawlSuccess ? 'success' : 'error'">
                    {{ lastCrawlSuccess ? '成功' : '失败' }}
                  </n-tag>
                </n-descriptions-item>
              </n-descriptions>
            </n-card>

            <!-- Recent Tasks Preview -->
            <n-card title="最近爬取的任务" size="small" class="tasks-preview-card">
              <n-data-table
                :columns="taskColumns"
                :data="recentTasks"
                :max-height="400"
                size="small"
                :pagination="{ pageSize: 5 }"
                :row-key="(row: any) => row.id || row.task_id"
                :expand-row-render="expandRowRender"
              />
            </n-card>
          </div>
        </n-tab-pane>
      </n-tabs>
    </n-card>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, reactive, computed, onMounted, onUnmounted, nextTick, h } from 'vue';
import {
  NCard, NTabs, NTabPane, NForm, NFormItem, NInput, NInputNumber,
  NButton, NSpace, NGrid, NGi, NSlider, NRadioGroup, NRadioButton,
  NCheckbox, NCollapse, NCollapseItem, NTag, NIcon, NDivider,
  NStatistic, NDescriptions, NDescriptionsItem, NDataTable, NSelect, NAlert,
  useMessage
} from 'naive-ui';
import {
  PlayCircle,
  StopCircle,
  Save,
  Refresh,
  Trash,
  Copy
} from '@vicons/ionicons5';

interface LogEntry {
  time: string;
  level: 'info' | 'warn' | 'error' | 'debug' | 'success';
  message: string;
}

interface CrawlerStats {
  tasksFound: number;
  tasksFiltered: number;
  ruleCards: number;
  screenshots: number;
}

export default defineComponent({
  name: 'CrawlerManagement',
  components: {
    NCard, NTabs, NTabPane, NForm, NFormItem, NInput, NInputNumber,
    NButton, NSpace, NGrid, NGi, NSlider, NRadioGroup, NRadioButton,
    NCheckbox, NCollapse, NCollapseItem, NTag, NIcon, NDivider,
    NStatistic, NDescriptions, NDescriptionsItem, NDataTable, NSelect, NAlert,
    PlayCircle, StopCircle, Save, Refresh, Trash, Copy
  },
  setup() {
    const message = useMessage();
    const logPanel = ref<HTMLElement | null>(null);
    const autoScroll = ref(true);

    // XHS Users state
    const users = ref<any[]>([]);
    const loadingUsers = ref(false);

    // Crawler configuration
    const config = reactive({
      selectedUserId: null as number | null,
      taskType: 'submission',
      pageSize: 20,
      maxPages: null as number | null,
      delayRange: [2, 4] as [number, number],  // Random delay range for list pages
      detailDelayRange: [2.5, 5] as [number, number],  // Random delay range for detail pages
      detailFetchMode: 'browser',
      extractRules: true,
      saveScreenshots: true,
      saveToDatabase: true,
      cleanOutput: false,
      includeParticipated: false,
      includeRecruit: false,
      verbose: false
    });

    // User options for dropdown
    const userOptions = computed(() => {
      return users.value.map(user => ({
        label: `${user.nickname || user.username} ${user.status ? '✓' : '⚠'}`,
        value: user.id
      }));
    });

    // Selected user object
    const selectedUser = computed(() => {
      if (!config.selectedUserId) return null;
      return users.value.find(u => u.id === config.selectedUserId) || null;
    });

    // State
    const isRunning = ref(false);
    const crawlStatus = ref<'idle' | 'running' | 'success' | 'error'>('idle');
    const logs = ref<LogEntry[]>([]);
    const stats = reactive<CrawlerStats>({
      tasksFound: 0,
      tasksFiltered: 0,
      ruleCards: 0,
      screenshots: 0
    });
    const lastCrawlTime = ref<string | null>(null);
    const lastCrawlDuration = ref<string | null>(null);
    const lastCrawlSuccess = ref(true);
    const recentTasks = ref<any[]>([]);

    // WebSocket for real-time logs
    let ws: WebSocket | null = null;

    // Computed
    const statusType = computed(() => {
      switch (crawlStatus.value) {
        case 'running': return 'warning';
        case 'success': return 'success';
        case 'error': return 'error';
        default: return 'default';
      }
    });

    const statusText = computed(() => {
      switch (crawlStatus.value) {
        case 'running': return '运行中';
        case 'success': return '已完成';
        case 'error': return '出错';
        default: return '就绪';
      }
    });

    const taskColumns = [
      { title: '任务ID', key: 'task_id', width: 200, ellipsis: { tooltip: true } },
      { title: '任务标题', key: 'task_title', ellipsis: { tooltip: true } },
      { title: '奖金池', key: 'ads_pool_amount', width: 100 },
      { title: '规则卡片', key: 'rule_cards_count', width: 80 },
      {
        title: '状态',
        key: 'status',
        width: 80,
        render: (row: any) => h(NTag, { type: 'success', size: 'small' }, { default: () => row.status })
      }
    ];

    // Mark rule card as participated
    const markRuleCardParticipated = async (ruleCardId: number) => {
      try {
        const response = await fetch(`http://localhost:5001/api/advertisement-tasks/rule-card/${ruleCardId}/participated`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        if (data.success) {
          message.success('已标记为已参与');
          // Refresh tasks to update UI
          fetchRecentTasks();
        } else {
          message.error(data.message || '标记失败');
        }
      } catch (error) {
        message.error('标记失败: ' + (error as Error).message);
      }
    };

    // Fetch recent tasks from backend
    const fetchRecentTasks = async () => {
      try {
        const response = await fetch('http://localhost:5001/api/advertisement-tasks/?page=1&page_size=10');
        const data = await response.json();
        if (data.success) {
          recentTasks.value = data.data.tasks;
        }
      } catch (error) {
        console.error('Failed to fetch tasks:', error);
      }
    };

    // Expand row render for rule cards
    const expandRowRender = (row: any) => {
      const ruleCards = row.rule_cards || [];
      if (ruleCards.length === 0) {
        return h('div', { style: 'padding: 16px; color: #999;' }, '暂无规则卡片');
      }
      
      return h('div', { style: 'padding: 16px; background: #fafafa;' }, [
        h('div', { style: 'font-weight: bold; margin-bottom: 12px;' }, `规则卡片 (${ruleCards.length})`),
        h(NSpace, { vertical: true, size: 'medium' }, {
          default: () => ruleCards.map((card: any) => 
            h(NCard, { size: 'small', style: 'background: white;' }, {
              default: () => h('div', { style: 'display: flex; justify-content: space-between; align-items: center;' }, [
                h('div', { style: 'flex: 1;' }, [
                  h('div', { style: 'font-weight: 500;' }, card.rule_name || '规则卡片'),
                  card.rule_description ? h('div', { style: 'color: #666; font-size: 12px; margin-top: 4px;' }, card.rule_description) : null
                ]),
                h('div', { style: 'display: flex; align-items: center; gap: 8px;' }, [
                  h(NTag, { 
                    type: card.participated ? 'success' : 'default', 
                    size: 'small' 
                  }, { 
                    default: () => card.participated ? '✓ 已参与' : '○ 未参与' 
                  }),
                  h(NButton, {
                    type: card.participated ? 'default' : 'success',
                    size: 'small',
                    disabled: card.participated,
                    onClick: () => markRuleCardParticipated(card.id)
                  }, {
                    default: () => card.participated ? '已参与' : '参与'
                  })
                ])
              ])
            })
          )
        })
      ]);
    };

    // Methods
    const addLog = (level: LogEntry['level'], message: string) => {
      const now = new Date();
      const time = now.toLocaleTimeString('zh-CN', { hour12: false });
      logs.value.push({ time, level, message });
      
      if (autoScroll.value && logPanel.value) {
        nextTick(() => {
          logPanel.value!.scrollTop = logPanel.value!.scrollHeight;
        });
      }
    };

    const clearLogs = () => {
      logs.value = [];
    };

    const copyLogs = async () => {
      try {
        const logText = logs.value
          .map(log => `${log.time} [${log.level.toUpperCase()}] ${log.message}`)
          .join('\n');
        await navigator.clipboard.writeText(logText);
        message.success('日志已复制到剪贴板');
      } catch (error) {
        message.error('复制失败');
      }
    };

    const saveConfig = () => {
      try {
        // Don't save sensitive data like passwords
        const configToSave = { ...config };
        delete (configToSave as any).mysqlPassword;
        localStorage.setItem('crawler_config', JSON.stringify(configToSave));
        message.success('配置已保存');
      } catch (error) {
        message.error('保存配置失败');
      }
    };

    const loadConfig = () => {
      try {
        const saved = localStorage.getItem('crawler_config');
        if (saved) {
          const parsed = JSON.parse(saved);
          Object.assign(config, parsed);
          message.info('配置已加载');
        }
      } catch (error) {
        console.error('Failed to load config:', error);
      }
    };

    // Load XHS users
    const loadUsers = async () => {
      loadingUsers.value = true;
      try {
        const response = await fetch('/api/user/list');
        const result = await response.json();
        if (result.success) {
          users.value = result.data || [];
          console.log('[Crawler] Loaded users:', users.value.length);
          // Auto-select if only one user available
          if (users.value.length === 1 && !config.selectedUserId) {
            config.selectedUserId = users.value[0].id;
            console.log('[Crawler] Auto-selected single user:', users.value[0].nickname || users.value[0].user_id);
          }
        }
      } catch (error) {
        console.error('Failed to load users:', error);
      } finally {
        loadingUsers.value = false;
      }
    };

    const startCrawl = async () => {
      if (!config.selectedUserId) {
        message.error('请选择小红书账户');
        return;
      }

      isRunning.value = true;
      crawlStatus.value = 'running';
      clearLogs();
      addLog('info', '正在启动爬虫...');

      // Reset stats
      stats.tasksFound = 0;
      stats.tasksFiltered = 0;
      stats.ruleCards = 0;
      stats.screenshots = 0;

      const startTime = Date.now();

      try {
        // Connect WebSocket for real-time logs
        connectWebSocket();

        const response = await fetch('/api/crawler/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: config.selectedUserId,
            task_type: config.taskType,
            page_size: config.pageSize,
            max_pages: config.maxPages,
            delay: config.delayRange[0],
            delay_max: config.delayRange[1],
            detail_delay: config.detailDelayRange[0],
            detail_delay_max: config.detailDelayRange[1],
            detail_fetch_mode: config.detailFetchMode,
            extract_rules: config.extractRules,
            save_screenshots: config.saveScreenshots,
            save_to_database: config.saveToDatabase,
            clean_output: config.cleanOutput,
            include_participated: config.includeParticipated,
            include_recruit: config.includeRecruit,
            verbose: config.verbose
          })
        });

        const result = await response.json();

        if (result.success) {
          crawlStatus.value = 'success';
          lastCrawlSuccess.value = true;
          addLog('success', `爬取完成！发现 ${result.data.tasks_found} 个任务，有效 ${result.data.tasks_filtered} 个`);
          
          // Update stats
          stats.tasksFound = result.data.tasks_found || 0;
          stats.tasksFiltered = result.data.tasks_filtered || 0;
          stats.ruleCards = result.data.rule_cards || 0;
          stats.screenshots = result.data.screenshots || 0;

          // Update recent tasks
          if (result.data.recent_tasks) {
            recentTasks.value = result.data.recent_tasks;
          }

          message.success('爬取完成');
        } else {
          crawlStatus.value = 'error';
          lastCrawlSuccess.value = false;
          addLog('error', `爬取失败: ${result.message}`);
          // Display detailed logs from backend if available
          if (result.logs && Array.isArray(result.logs)) {
            result.logs.forEach((log: string) => {
              if (log.toLowerCase().includes('error') || log.toLowerCase().includes('fail')) {
                addLog('error', log);
              } else if (log.toLowerCase().includes('warn')) {
                addLog('warn', log);
              } else {
                addLog('info', log);
              }
            });
          }
          message.error(result.message?.split('\n')[0] || '爬取失败');
        }
      } catch (error: any) {
        crawlStatus.value = 'error';
        lastCrawlSuccess.value = false;
        addLog('error', `爬取出错: ${error.message}`);
        message.error('爬取出错: ' + error.message);
      } finally {
        isRunning.value = false;
        disconnectWebSocket();

        const duration = Math.round((Date.now() - startTime) / 1000);
        lastCrawlTime.value = new Date().toLocaleString('zh-CN');
        lastCrawlDuration.value = `${Math.floor(duration / 60)}分${duration % 60}秒`;
      }
    };

    const stopCrawl = async () => {
      try {
        addLog('warn', '正在停止爬虫...');
        await fetch('/api/crawler/stop', { method: 'POST' });
        addLog('info', '爬虫已停止');
        isRunning.value = false;
        crawlStatus.value = 'idle';
        message.info('爬虫已停止');
      } catch (error: any) {
        addLog('error', `停止失败: ${error.message}`);
        message.error('停止失败');
      }
    };

    const connectWebSocket = () => {
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.hostname}:5001/ws/crawler`;
        ws = new WebSocket(wsUrl);

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'log') {
              addLog(data.level || 'info', data.message);
            } else if (data.type === 'stats') {
              Object.assign(stats, data.stats);
            }
          } catch (e) {
            addLog('info', event.data);
          }
        };

        ws.onerror = () => {
          // WebSocket not available, fall back to polling
        };
      } catch (e) {
        // WebSocket not supported
      }
    };

    const disconnectWebSocket = () => {
      if (ws) {
        ws.close();
        ws = null;
      }
    };

    // Lifecycle
    onMounted(() => {
      loadConfig();
      loadUsers();
      fetchRecentTasks();
    });

    onUnmounted(() => {
      disconnectWebSocket();
    });

    return {
      config,
      users,
      loadingUsers,
      userOptions,
      selectedUser,
      isRunning,
      crawlStatus,
      statusType,
      statusText,
      logs,
      logPanel,
      autoScroll,
      stats,
      lastCrawlTime,
      lastCrawlDuration,
      lastCrawlSuccess,
      recentTasks,
      taskColumns,
      expandRowRender,
      startCrawl,
      stopCrawl,
      clearLogs,
      copyLogs,
      saveConfig,
      loadConfig,
      loadUsers,
      fetchRecentTasks
    };
  }
});
</script>

<style scoped>
.crawler-management {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.main-card {
  min-height: calc(100vh - 100px);
}

.config-form {
  max-width: 800px;
}

.action-buttons {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e8e8e8;
}

.slider-with-hint {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
}

.slider-with-hint .n-slider {
  flex: 1;
}

.range-hint {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
  flex-shrink: 0;
}

.log-container {
  display: flex;
  flex-direction: column;
  height: 500px;
}

.log-toolbar {
  padding: 8px 0;
  border-bottom: 1px solid #e8e8e8;
  margin-bottom: 8px;
}

.log-panel {
  flex: 1;
  overflow-y: auto;
  background: #1e1e1e;
  border-radius: 6px;
  padding: 12px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.log-entry {
  display: flex;
  gap: 12px;
  padding: 2px 0;
}

.log-time {
  color: #666;
  flex-shrink: 0;
}

.log-level {
  flex-shrink: 0;
  width: 50px;
  font-weight: 600;
}

.log-message {
  color: #ccc;
  word-break: break-all;
}

.log-info .log-level { color: #409eff; }
.log-warn .log-level { color: #e6a23c; }
.log-error .log-level { color: #f56c6c; }
.log-debug .log-level { color: #909399; }
.log-success .log-level { color: #67c23a; }

.log-empty {
  color: #666;
  text-align: center;
  padding: 40px;
}

.results-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stats-grid {
  margin-bottom: 8px;
}

.stat-card {
  text-align: center;
}

.last-crawl-card {
  margin-bottom: 8px;
}

.tasks-preview-card {
  margin-top: 8px;
}
</style>
