<template>
  <el-container class="layout">
    <el-header class="header">
      <div class="logo">📈 网格交易管理系统</div>
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
      </el-menu>
    </el-header>

    <el-main class="main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = computed(() => {
  if (route.path.startsWith('/plans')) return '/plans'
  return route.path
})
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

.main { padding: 24px; max-width: 1200px; margin: 0 auto; }
</style>
