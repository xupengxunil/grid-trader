<template>
  <div>
    <!-- Page header -->
    <div class="page-header">
      <h2>交易计划列表</h2>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
        新建计划
      </el-button>
    </div>

    <!-- Plan cards -->
    <el-empty v-if="!loading && plans.length === 0" description="暂无交易计划，点击右上角新建" />

    <el-row :gutter="16" v-loading="loading">
      <el-col
        v-for="plan in plans"
        :key="plan.id"
        :xs="24" :sm="12" :lg="8"
        class="plan-col"
      >
        <el-card class="plan-card" shadow="hover" @click="goDetail(plan.id)">
          <template #header>
            <div class="card-header">
              <span class="stock-code">{{ plan.stock_code }}</span>
              <span class="stock-name">{{ plan.stock_name }}</span>
              <el-button
                type="danger"
                size="small"
                :icon="Delete"
                circle
                @click.stop="confirmDelete(plan)"
              />
            </div>
          </template>

          <el-descriptions :column="2" size="small">
            <el-descriptions-item label="基准价">
              ¥{{ plan.base_price }}
            </el-descriptions-item>
            <el-descriptions-item label="总资金">
              ¥{{ plan.total_funds }}
            </el-descriptions-item>
            <el-descriptions-item label="网格档位">
              {{ plan.record_count }} 档
            </el-descriptions-item>
            <el-descriptions-item label="持仓中">
              {{ plan.holding_count }} 档
            </el-descriptions-item>
            <el-descriptions-item label="已清仓">
              {{ plan.cleared_count }} 档
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatDate(plan.created_at) }}
            </el-descriptions-item>
          </el-descriptions>

          <div class="card-footer">
            <el-button type="primary" size="small" plain>查看详情 →</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Create plan dialog -->
    <el-dialog v-model="showCreateDialog" title="新建网格交易计划" width="480px" @close="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="股票代码" prop="stock_code">
          <el-input v-model="form.stock_code" placeholder="例如：600000" maxlength="10" />
        </el-form-item>
        <el-form-item label="股票名称" prop="stock_name">
          <el-input v-model="form.stock_name" placeholder="例如：浦发银行" maxlength="20" />
        </el-form-item>
        <el-form-item label="建仓基准价" prop="base_price">
          <el-input-number
            v-model="form.base_price"
            :precision="3"
            :step="0.1"
            :min="0.001"
            style="width:100%"
            placeholder="请输入当前股价作为基准"
          />
        </el-form-item>
        <el-form-item label="总资金(元)" prop="total_funds">
          <el-input-number
            v-model="form.total_funds"
            :precision="2"
            :step="1000"
            :min="1"
            style="width:100%"
          />
        </el-form-item>
        <el-alert
          type="info"
          :closable="false"
          style="margin-top:8px"
          description="系统将按每份约1万元（总资金÷5）和基准价自动生成5档买卖网格（间距3%）。每档需至少可买1手（100股）。"
        />
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="submitCreate">创建计划</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import { getPlans, createPlan, deletePlan } from '../api/index.js'

const router = useRouter()
const plans = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const creating = ref(false)
const formRef = ref(null)

const form = ref({
  stock_code: '',
  stock_name: '',
  base_price: null,
  total_funds: 50000,
})

const rules = {
  stock_code: [{ required: true, message: '请输入股票代码', trigger: 'blur' }],
  stock_name: [{ required: true, message: '请输入股票名称', trigger: 'blur' }],
  base_price: [{ required: true, type: 'number', message: '请输入建仓基准价', trigger: 'change' }],
  total_funds: [{ required: true, type: 'number', message: '请输入总资金', trigger: 'change' }],
}

async function fetchPlans() {
  loading.value = true
  try {
    const { data } = await getPlans()
    plans.value = data
  } catch (e) {
    ElMessage.error('加载计划列表失败')
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.value = { stock_code: '', stock_name: '', base_price: null, total_funds: 50000 }
  formRef.value?.resetFields()
}

async function submitCreate() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  creating.value = true
  try {
    await createPlan(form.value)
    ElMessage.success('网格计划创建成功！')
    showCreateDialog.value = false
    await fetchPlans()
  } catch (e) {
    const msg = e.response?.data?.detail || '创建失败，请重试'
    ElMessage.error(msg)
  } finally {
    creating.value = false
  }
}

async function confirmDelete(plan) {
  try {
    await ElMessageBox.confirm(
      `确定要删除「${plan.stock_name}(${plan.stock_code})」的交易计划吗？此操作将同时删除所有相关记录。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }
    )
    await deletePlan(plan.id)
    ElMessage.success('已删除')
    await fetchPlans()
  } catch {
    // user cancelled or request failed
  }
}

function goDetail(id) {
  router.push(`/plans/${id}`)
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

onMounted(fetchPlans)
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h2 { font-size: 20px; color: #303133; }

.plan-col { margin-bottom: 16px; }

.plan-card { cursor: pointer; transition: transform .15s; }
.plan-card:hover { transform: translateY(-2px); }

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.stock-code {
  background: #409eff;
  color: #fff;
  font-size: 13px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 700;
}
.stock-name { flex: 1; font-weight: 600; font-size: 15px; }

.card-footer { margin-top: 12px; text-align: right; }
</style>
