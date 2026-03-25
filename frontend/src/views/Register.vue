<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <template #header>
        <div class="auth-header">
          <span class="logo">📈 网格交易管理系统</span>
          <h2>注册账号</h2>
        </div>
      </template>

      <el-alert
        v-if="success"
        type="success"
        title="注册成功！"
        description="您的账号已提交，请等待管理员审批通过后方可登录。"
        show-icon
        :closable="false"
        style="margin-bottom:16px"
      />

      <el-form
        v-else
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
        @submit.prevent="submit"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" clearable />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="选填" clearable />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="至少6位" show-password />
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
            注册
          </el-button>
        </el-form-item>
      </el-form>

      <div class="auth-footer">
        已有账号？
        <router-link to="/login">立即登录</router-link>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { authRegister } from '../api/index.js'

const formRef = ref(null)
const loading = ref(false)
const errorMsg = ref('')
const success = ref(false)

const form = ref({ username: '', email: '', password: '' })

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  email: [{ type: 'email', message: '请输入有效邮箱', trigger: 'blur' }],
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  errorMsg.value = ''
  try {
    await authRegister(form.value)
    success.value = true
  } catch (e) {
    const err = e.response?.data
    if (err) {
      const msgs = Object.values(err).flat()
      errorMsg.value = msgs.join(' ')
    } else {
      errorMsg.value = '注册失败，请稍后重试。'
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
