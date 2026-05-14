<template>
  <div class="monitors-page">
    <div class="header-actions">
      <h2>股价监控</h2>
      <el-button type="primary" @click="openDialog()">添加监控</el-button>
    </div>

    <el-table :data="monitors" v-loading="loading" style="width: 100%; margin-top: 16px" border stripe>
      <el-table-column prop="stock_name" label="股票名称" width="150" />
      <el-table-column prop="stock_code" label="股票代码" width="120" />
      <el-table-column prop="condition" label="监控条件" width="120">
        <template #default="{ row }">
          <el-tag :type="row.condition === 'above' ? 'danger' : 'success'">
            {{ row.condition === 'above' ? '达到或高于' : '达到或低于' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="target_price" label="目标价格" width="150" />
      <el-table-column prop="is_active" label="状态" width="100">
        <template #default="{ row }">
          <el-switch v-model="row.is_active" @change="toggleActive(row)" />
        </template>
      </el-table-column>
      <el-table-column label="操作">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="openDialog(row)">编辑</el-button>
          <el-button type="danger" link size="small" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog :title="dialogForm.id ? '编辑监控' : '添加监控'" v-model="dialogVisible" width="500px">
      <el-form :model="dialogForm" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="股票代码" prop="stock_code">
          <el-autocomplete
            v-model="dialogForm.stock_code"
            :fetch-suggestions="querySearchAsync"
            placeholder="搜索或手动输入代码 (港股加hk前缀，如hk00700)"
            @select="handleSelectStock"
            value-key="code"
            style="width: 100%;"
          >
            <template #default="{ item }">
              <div style="display: flex; justify-content: space-between;">
                <span>{{ item.name }}</span>
                <span style="color: #999; font-size: 12px;">{{ item.code }}</span>
              </div>
            </template>
          </el-autocomplete>
        </el-form-item>
        <el-form-item label="股票名称" prop="stock_name">
          <el-input v-model="dialogForm.stock_name" placeholder="如 贵州茅台" />
        </el-form-item>
        <el-form-item label="监控条件" prop="condition">
          <el-select v-model="dialogForm.condition" style="width: 100%;">
            <el-option label="达到或低于" value="below" />
            <el-option label="达到或高于" value="above" />
          </el-select>
        </el-form-item>
        <el-form-item label="监控价格" prop="target_price">
          <el-input-number v-model="dialogForm.target_price" :precision="3" :step="0.01" style="width: 100%;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="saving">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getMonitors, createMonitor, updateMonitor, deleteMonitor, searchStocks } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const monitors = ref([])
const loading = ref(false)

const dialogVisible = ref(false)
const saving = ref(false)
const formRef = ref()

const dialogForm = reactive({
  id: null,
  stock_code: '',
  stock_name: '',
  condition: 'below',
  target_price: 0,
  is_active: true
})

const rules = {
  stock_code: [{ required: true, message: '请输入股票代码', trigger: 'blur' }],
  stock_name: [{ required: true, message: '请输入股票名称', trigger: 'blur' }],
  target_price: [{ required: true, message: '请输入目标价格', trigger: 'blur' }]
}


let searchTimeout = null

const querySearchAsync = (queryString, cb) => {
  if (queryString) {
    if (searchTimeout) {
      clearTimeout(searchTimeout)
    }
    searchTimeout = setTimeout(async () => {
      try {
        const res = await searchStocks(queryString)
        cb(res.data || [])
      } catch (e) {
        cb([])
      }
    }, 300)
  } else {
    cb([])
  }
}

const handleSelectStock = (item) => {
  dialogForm.stock_code = item.code
  dialogForm.stock_name = item.name
}

async function loadMonitors() {
  loading.value = true
  try {
    const res = await getMonitors()
    monitors.value = res.data
  } catch (err) {
    ElMessage.error('加载监控列表失败')
  } finally {
    loading.value = false
  }
}

function openDialog(row = null) {
  if (formRef.value) formRef.value.resetFields()
  if (row) {
    dialogForm.id = row.id
    dialogForm.stock_code = row.stock_code
    dialogForm.stock_name = row.stock_name
    dialogForm.condition = row.condition
    dialogForm.target_price = row.target_price
    dialogForm.is_active = row.is_active
  } else {
    dialogForm.id = null
    dialogForm.stock_code = ''
    dialogForm.stock_name = ''
    dialogForm.condition = 'below'
    dialogForm.target_price = 0
    dialogForm.is_active = true
  }
  dialogVisible.value = true
}

async function submitForm() {
  await formRef.value.validate()
  saving.value = true
  try {
    if (dialogForm.id) {
      await updateMonitor(dialogForm.id, dialogForm)
      ElMessage.success('修改成功')
    } else {
      await createMonitor(dialogForm)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    loadMonitors()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function toggleActive(row) {
  try {
    await updateMonitor(row.id, { is_active: row.is_active })
    ElMessage.success(row.is_active ? '已启用监控' : '已暂停监控')
  } catch (err) {
    row.is_active = !row.is_active
    ElMessage.error('切换状态失败')
  }
}

async function handleDelete(id) {
  try {
    await ElMessageBox.confirm('确定要删除这条监控记录吗？', '提示', { type: 'warning' })
    await deleteMonitor(id)
    ElMessage.success('删除成功')
    loadMonitors()
  } catch {}
}

onMounted(() => {
  loadMonitors()
})
</script>

<style scoped>
.monitors-page {
  background: #fff;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.05);
}
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
