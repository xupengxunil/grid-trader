<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <template #header>
        <div class="auth-header">
          <span class="logo">📈 智能量化交易平台</span>
          <h2>登录</h2>
        </div>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px" @submit.prevent="submit">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" clearable />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>

        <el-alert
          v-if="errorMsg"
          type="error"
          :description="errorMsg"
          show-icon
          :closable="false"
          style="margin-bottom:16px"
        />

        <el-form-item>
          <el-button type="primary" :loading="loading" style="width:100%" @click="submit">
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="auth-footer">
        没有账号？
        <router-link to="/register">立即注册</router-link>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authLogin } from '../api/index.js'
import { setAuth } from '../store/auth.js'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const errorMsg = ref('')

const form = ref({ username: '', password: '' })

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  errorMsg.value = ''
  try {
    const { data } = await authLogin(form.value)
    setAuth(data.token, data.user)
    router.push('/plans')
  } catch (e) {
    const err = e.response?.data
    if (err) {
      const msgs = Object.values(err).flat()
      errorMsg.value = msgs.join(' ')
    } else {
      errorMsg.value = '登录失败，请稍后重试。'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
}
.auth-card {
  width: 420px;
}
.auth-header {
  text-align: center;
}
.logo {
  font-size: 18px;
  font-weight: 700;
  display: block;
  margin-bottom: 8px;
  color: #1d2035;
}
.auth-header h2 {
  margin: 0;
  font-size: 20px;
}
.auth-footer {
  text-align: center;
  color: #606266;
  font-size: 14px;
}
</style>
