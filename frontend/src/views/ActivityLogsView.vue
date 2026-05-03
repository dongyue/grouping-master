<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getActivityLogs, getActivity } from '../api/activities'
import { formatDate, formatDateTime } from '../utils/date'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref('')
const logs = ref([])
const activity = ref(null)
const expandedIds = ref({})

onMounted(async () => {
  try {
    const [activityRes, logsRes] = await Promise.all([
      getActivity(route.params.slug),
      getActivityLogs(route.params.slug),
    ])
    activity.value = activityRes.data
    logs.value = logsRes.data
  } catch (err) {
    if (err.response?.status === 403) {
      router.replace({ name: 'activity-detail', params: { slug: route.params.slug } })
      return
    }
    if (err.response?.status === 404) {
      error.value = '活动不存在'
    } else {
      error.value = err.response?.data?.detail || '加载日志失败'
    }
  } finally {
    loading.value = false
  }
})

function toggleExpand(logId) {
  expandedIds.value = {
    ...expandedIds.value,
    [logId]: !expandedIds.value[logId],
  }
}

const actionLabels = {
  create: '创建活动',
  edit: '编辑活动',
  join: '加入活动',
  leave: '退出活动',
  kick: '踢出成员',
  group: '执行分组',
  ungroup: '解除分组',
}
</script>

<template>
  <div class="page-card">
    <div class="header">
      <button class="btn-back" @click="router.push({ name: 'activity-detail', params: { slug: route.params.slug } })">
        ← 返回活动
      </button>
      <h1 class="page-title">操作日志</h1>
      <p v-if="activity" class="subtitle">{{ activity.title }}</p>
    </div>

    <div v-if="loading" style="text-align: center; color: #999; padding: 40px;">加载中...</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>

    <div v-else-if="logs.length === 0" class="empty">暂无操作日志</div>

    <div v-else class="log-list">
      <div v-for="log in logs" :key="log.id" class="log-item">
        <div class="log-header">
          <span class="log-type" :class="'type-' + log.action_type">
            {{ actionLabels[log.action_type] || log.action_type }}
          </span>
          <span class="log-time">{{ formatDateTime(log.created_at) }}</span>
        </div>
        <p class="log-content">{{ log.content }}</p>
        <div v-if="log.action_type === 'group' && log.detail" class="log-detail-wrapper">
          <button class="btn-expand" @click="toggleExpand(log.id)">
            {{ expandedIds[log.id] ? '收起详情 ▲' : '展开详情 ▼' }}
          </button>
          <div v-if="expandedIds[log.id]" class="log-detail">
            <div class="detail-section">
              <h5>分组规则快照</h5>
              <div class="detail-line">
                策略：{{ log.detail.activity_snapshot.group_strategy === 'fixed_group_count' ? '固定总组数' : '固定每组人数' }}
                ，参数：{{ log.detail.activity_snapshot.group_param }}
              </div>
              <div v-if="log.detail.activity_snapshot.constraints?.length" class="detail-line">
                约束规则：
                <span v-for="(c, i) in log.detail.activity_snapshot.constraints" :key="i" class="constraint-tag">
                  {{ c.attribute_name }}({{ c.allowed_values.join('、') }}){{ c.constraint_type === 'min_diversity' ? '至少' : '最多' }}{{ c.constraint_value }}种
                </span>
              </div>
              <div class="detail-line">随机种子：{{ log.detail.seed }}</div>
            </div>
            <div class="detail-section">
              <h5>分组时成员及属性 ({{ log.detail.members.length }} 人)</h5>
              <div v-for="m in log.detail.members" :key="m.user_id" class="detail-line">
                {{ m.nickname }}<span v-if="m.attributes && Object.keys(m.attributes).length">
                  ：{{ Object.entries(m.attributes).map(([k, v]) => k + '=' + v).join('，') }}
                </span>
              </div>
            </div>
            <div v-if="log.detail.shuffle_order" class="detail-section">
              <h5>打乱前顺序</h5>
              <div class="detail-line">
                {{ log.detail.shuffle_order.map(uid => log.detail.members.find(m => m.user_id === uid)?.nickname || uid).join(' → ') }}
              </div>
            </div>
            <div class="detail-section">
              <h5>分组结果 ({{ log.detail.groups.length }} 组)</h5>
              <div v-for="g in log.detail.groups" :key="g.group_number" class="group-result">
                第 {{ g.group_number }} 组：{{ g.members.map(m => m.nickname).join('、') }}
              </div>
              <div v-if="log.detail.ungrouped?.length" class="group-result ungrouped">
                落单：{{ log.detail.ungrouped.map(m => m.nickname).join('、') }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.header {
  margin-bottom: 24px;
}

.btn-back {
  font-size: 13px;
  color: #4f46e5;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  margin-bottom: 12px;
}

.btn-back:hover {
  text-decoration: underline;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 4px 0;
}

.subtitle {
  font-size: 13px;
  color: #999;
  margin: 0;
}

.empty {
  text-align: center;
  color: #bbb;
  padding: 40px;
  font-size: 14px;
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.log-item {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 14px 16px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.log-type {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  background: #f0f0f0;
  color: #666;
}

.log-type.type-create { background: #e6f7e6; color: #389e0d; }
.log-type.type-edit { background: #e6f0ff; color: #2f54eb; }
.log-type.type-join { background: #e6fffb; color: #08979c; }
.log-type.type-leave { background: #fff7e6; color: #d48806; }
.log-type.type-kick { background: #fff1f0; color: #cf1322; }
.log-type.type-group { background: #f9f0ff; color: #722ed1; }
.log-type.type-ungroup { background: #fff7e6; color: #d48806; }

.log-time {
  font-size: 12px;
  color: #bbb;
}

.log-content {
  margin: 6px 0 0 0;
  font-size: 13px;
  color: #555;
  line-height: 1.6;
}

.log-detail-wrapper {
  margin-top: 10px;
}

.btn-expand {
  font-size: 12px;
  color: #4f46e5;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}

.btn-expand:hover {
  text-decoration: underline;
}

.log-detail {
  margin-top: 10px;
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
  border: 1px solid #f0f0f0;
}

.detail-section {
  margin-bottom: 10px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-section h5 {
  font-size: 12px;
  font-weight: 600;
  color: #888;
  margin: 0 0 4px 0;
}

.detail-line {
  font-size: 13px;
  color: #555;
  line-height: 1.8;
}

.constraint-tag {
  display: inline-block;
  margin-right: 6px;
  font-size: 12px;
  padding: 1px 6px;
  background: #f0eefc;
  color: #4f46e5;
  border-radius: 3px;
}

.group-result {
  font-size: 13px;
  color: #333;
  line-height: 1.8;
}

.group-result.ungrouped {
  color: #999;
}
</style>
