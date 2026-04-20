<template>
  <div v-if="isLoginPage" style="min-height:100vh;background:#f0f2f5;">
    <router-view />
  </div>

  <el-container v-else class="layout">
    <el-header class="header">
      <div class="logo">📈 智能量化交易平台</div>
      <el-menu
        mode="horizontal"
        :default-active="activeMenu"
        router
        background-color="#1d2035"
        text-color="#cdd3e0"
        active-text-color="#409eff"
        class="nav-menu"
      >
        <el-menu-item index="/plans">
          <el-icon><List /></el-icon>
          交易计划
        </el-menu-item>
        <el-menu-item index="/statistics">
          <el-icon><TrendCharts /></el-icon>
          收益统计
        </el-menu-item>
        <el-menu-item index="/analysis">
          <el-icon><DataLine /></el-icon>
          行情诊断
        </el-menu-item>
        <el-menu-item index="/games">
          <el-icon><Monitor /></el-icon>
          摸鱼游戏
        </el-menu-item>
        <el-menu-item index="/profile">
          <el-icon><User /></el-icon>
          个人中心
        </el-menu-item>
      </el-menu>

      <!-- User info area -->
      <div class="user-area">
        <el-tag
          v-if="user"
          :type="statusTagType"
          size="small"
          style="margin-right:8px"
        >
          {{ user.status_display || user.status }}
        </el-tag>
        <span class="username">{{ user?.username }}</span>
        <el-button
          type="danger"
          size="small"
          plain
          style="margin-left:12px"
          @click="handleLogout"
        >
          退出
        </el-button>
      </div>
    </el-header>

    <el-main class="main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { authLogout } from './api/index.js'
import { user, clearAuth } from './store/auth.js'

const route = useRoute()
const router = useRouter()

const isLoginPage = computed(() =>
  route.path === '/login' || route.path === '/register'
)

const activeMenu = computed(() => {
  if (route.path.startsWith('/plans')) return '/plans'
  return route.path
})

const statusTagType = computed(() => {
  const map = { APPROVED: 'success', PENDING: 'warning', REJECTED: 'danger' }
  return map[user.value?.status] ?? 'info'
})

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await authLogout().catch(() => {})
    clearAuth()
    router.push('/login')
  } catch {
    // user cancelled
  }
}
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #f0f2f5; font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; }

.layout { min-height: 100vh; }

.header {
  display: flex;
  align-items: center;
  background: #1d2035;
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,.2);
  position: sticky;
  top: 0;
  z-index: 100;
}

.logo {
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  white-space: nowrap;
  margin-right: 32px;
}

.nav-menu { border-bottom: none; flex: 1; }

.user-area {
  display: flex;
  align-items: center;
  white-space: nowrap;
  margin-left: 16px;
}

.username {
  color: #cdd3e0;
  font-size: 14px;
}

.main { 
  padding: 24px; 
  max-width: 1600px; /* 增加页面最大宽度以容纳更宽的卡片 */
  margin: 0 auto; 
  width: 100%;
}
</style>
