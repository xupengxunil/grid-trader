<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>个人中心</span>
      </div>
    </template>
    <el-form :model="form" label-width="120px" v-loading="loading">
      <el-form-item label="企业微信机器人地址" prop="wechatWebhook">
        <el-input v-model="form.wechatWebhook" placeholder="请输入企业微信机器人Webhook URL" />
        <div style="font-size: 12px; color: #999; margin-top: 5px;">用于每日早上7点钟推送当前可以做网格的股票列表</div>
      </el-form-item>
      
      <el-form-item>
        <el-button type="primary" @click="onSubmit" :loading="saving">保存设置</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import http from '../api/index'
import { user } from '../store/auth'

const form = ref({
  wechatWebhook: ''
})

const loading = ref(false)
const saving = ref(false)

const loadProfile = async () => {
  loading.value = true
  try {
    const res = await http.get('/auth/me/')
    form.value.wechatWebhook = res.data.wechat_webhook || ''
  } catch (error) {
    ElMessage.error('获取个人信息失败')
  } finally {
    loading.value = false
  }
}

const onSubmit = async () => {
  saving.value = true
  try {
    await http.post('/auth/me/', {
      wechat_webhook: form.value.wechatWebhook
    })
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadProfile()
})
</script>