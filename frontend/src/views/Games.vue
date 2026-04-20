<template>
  <div class="games-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span style="font-weight: bold; font-size: 16px;">🎮 摸鱼游戏中心 - 贪吃蛇</span>
          <div>
            <span class="score">分数: {{ score }}</span>
            <el-button type="primary" size="small" @click="startGame" style="margin-left: 15px;">
              {{ isPlaying ? '重新开始' : '开始游戏' }}
            </el-button>
          </div>
        </div>
      </template>

      <div class="game-area" tabindex="0" @keydown="handleKeydown" ref="gameArea">
        <div v-if="!isPlaying && !isGameOver" class="overlay">
          <span>点击"开始游戏"或按空格键开始</span>
        </div>
        <div v-if="isGameOver" class="overlay">
          <span>游戏结束! <br>得分: {{ score }}<br><br><span style="font-size: 16px;">按空格键重新开始</span></span>
        </div>
        
        <div class="grid">
          <div v-for="row in gridSize" :key="'r' + row" class="row">
            <div v-for="col in gridSize" :key="'c' + col" 
                 class="cell" 
                 :class="{ 
                   'snake': isSnake(col - 1, row - 1),
                   'head': isHead(col - 1, row - 1),
                   'food': isFood(col - 1, row - 1)
                 }">
            </div>
          </div>
        </div>
      </div>
      
      <div class="instructions">
        <p>控制说明：使用键盘的 <strong>↑ ↓ ← →</strong> 或 <strong>W A S D</strong> 来控制蛇的移动。按空格键可以快速开始/重新开始游戏。</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'

const gridSize = 25
const snake = ref([])
const food = ref({ x: 0, y: 0 })
const direction = ref({ x: 1, y: 0 })
const nextDirection = ref({ x: 1, y: 0 })
const score = ref(0)
const isPlaying = ref(false)
const isGameOver = ref(false)
const gameArea = ref(null)

let gameInterval = null
const speed = 120

function generateFood() {
  let newFood
  while (true) {
    newFood = {
      x: Math.floor(Math.random() * gridSize),
      y: Math.floor(Math.random() * gridSize)
    }
    if (!snake.value.some(segment => segment.x === newFood.x && segment.y === newFood.y)) {
      break
    }
  }
  food.value = newFood
}

function startGame() {
  snake.value = [
    { x: 5, y: 12 },
    { x: 4, y: 12 },
    { x: 3, y: 12 }
  ]
  direction.value = { x: 1, y: 0 }
  nextDirection.value = { x: 1, y: 0 }
  score.value = 0
  isGameOver.value = false
  isPlaying.value = true
  generateFood()
  
  if (gameInterval) clearInterval(gameInterval)
  gameInterval = setInterval(gameLoop, speed)
  
  nextTick(() => {
    if (gameArea.value) {
      gameArea.value.focus()
    }
  })
}

function stopGame() {
  isPlaying.value = false
  isGameOver.value = true
  if (gameInterval) clearInterval(gameInterval)
}

function handleKeydown(e) {
  if (e.code === 'Space') {
    e.preventDefault()
    if (!isPlaying.value || isGameOver.value) {
      startGame()
    }
    return
  }

  if (!isPlaying.value) return
  
  // 阻止方向键导致页面滚动
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.code)) {
    e.preventDefault()
  }

  switch (e.code) {
    case 'ArrowUp':
    case 'KeyW':
      if (direction.value.y !== 1) nextDirection.value = { x: 0, y: -1 }
      break
    case 'ArrowDown':
    case 'KeyS':
      if (direction.value.y !== -1) nextDirection.value = { x: 0, y: 1 }
      break
    case 'ArrowLeft':
    case 'KeyA':
      if (direction.value.x !== 1) nextDirection.value = { x: -1, y: 0 }
      break
    case 'ArrowRight':
    case 'KeyD':
      if (direction.value.x !== -1) nextDirection.value = { x: 1, y: 0 }
      break
  }
}

function gameLoop() {
  direction.value = nextDirection.value
  
  const head = { ...snake.value[0] }
  head.x += direction.value.x
  head.y += direction.value.y
  
  // 撞墙检测
  if (head.x < 0 || head.x >= gridSize || head.y < 0 || head.y >= gridSize) {
    stopGame()
    return
  }
  
  // 撞到自己检测
  if (snake.value.some(segment => segment.x === head.x && segment.y === head.y)) {
    stopGame()
    return
  }
  
  snake.value.unshift(head)
  
  // 吃食物检测
  if (head.x === food.value.x && head.y === food.value.y) {
    score.value += 10
    generateFood()
  } else {
    snake.value.pop()
  }
}

function isSnake(x, y) {
  return snake.value.some(segment => segment.x === x && segment.y === y)
}

function isHead(x, y) {
  return snake.value.length > 0 && snake.value[0].x === x && snake.value[0].y === y
}

function isFood(x, y) {
  return food.value.x === x && food.value.y === y
}

onUnmounted(() => {
  if (gameInterval) clearInterval(gameInterval)
})
</script>

<style scoped>
.games-container {
  max-width: 700px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.score {
  font-weight: bold;
  color: #e74c3c;
  font-size: 16px;
}

.game-area {
  position: relative;
  background: #2c3e50;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  justify-content: center;
  outline: none;
  cursor: pointer;
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.5);
}

.game-area:focus {
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.5);
}

.overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  font-weight: bold;
  z-index: 10;
  text-align: center;
  border-radius: 8px;
  line-height: 1.5;
}

.grid {
  display: flex;
  flex-direction: column;
  background: #34495e;
  border: 1px solid #7f8c8d;
}

.row {
  display: flex;
}

.cell {
  width: 20px;
  height: 20px;
  border: 1px solid rgba(255, 255, 255, 0.03);
}

.snake {
  background-color: #2ecc71;
  border-radius: 2px;
}

.head {
  background-color: #27ae60;
  border-radius: 4px;
}

.food {
  background-color: #e74c3c;
  border-radius: 50%;
  transform: scale(0.8);
  box-shadow: 0 0 5px #e74c3c;
}

.instructions {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 4px;
  color: #606266;
  font-size: 14px;
  text-align: center;
}
</style>
