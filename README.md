# 网格交易管理系统 / Grid Trader

一个基于 **Vue 3 + Django + MySQL** 的 A 股网格交易辅助系统，帮助投资者记录和管理网格交易操作。

---

## 功能特性

- 📊 **多股票计划管理**：为每只股票创建独立的网格交易计划
- 🔢 **自动生成网格**：依据用户输入的建仓基准价，以 3% 间距自动生成 5 档买卖价格
- 💰 **资金自动拆分**：总资金均分 5 份（每份约 1 万元），按档位自动计算可买手数（A股每手100股）
- 📝 **交易记录管理**：记录每档的实际买入/卖出价格，支持一键标记清仓
- 📈 **收益统计**：按时间段统计累计收益和操作次数，支持按股票分组查看

---

## 技术栈

| 层次   | 技术                                |
|--------|-------------------------------------|
| 前端   | Vue 3 + Vue Router + Element Plus   |
| 后端   | Django 4.2 + Django REST Framework  |
| 数据库 | MySQL 8.0+                          |

---

## 快速开始

### 1. 准备数据库

```sql
CREATE DATABASE grid_trader CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 启动后端

```bash
cd grid_backend

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入真实的数据库密码等配置

# 数据库迁移
python manage.py migrate

# 创建管理员账号（可选）
python manage.py createsuperuser

# 启动开发服务器
python manage.py runserver
```

后端服务地址：http://127.0.0.1:8000

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端页面地址：http://localhost:5173

---

## API 接口说明

| 方法   | 路径                              | 说明                 |
|--------|-----------------------------------|----------------------|
| GET    | /api/plans/                       | 获取所有交易计划     |
| POST   | /api/plans/                       | 创建新交易计划       |
| GET    | /api/plans/{id}/                  | 获取单个计划详情     |
| DELETE | /api/plans/{id}/                  | 删除计划及其记录     |
| GET    | /api/plans/{id}/records/          | 获取计划的网格记录   |
| POST   | /api/records/{id}/buy/            | 记录买入操作         |
| POST   | /api/records/{id}/sell/           | 记录卖出操作（清仓） |
| GET    | /api/statistics/                  | 收益统计查询         |

### 统计接口参数

```
GET /api/statistics/?start_date=2024-01-01&end_date=2024-12-31&plan_id=1
```

---

## 网格计算逻辑

- 第 1 档：以基准价买入，基准价 × 1.03 卖出
- 第 2 档：以基准价 × 0.97 买入，基准价卖出
- 第 3 档：以基准价 × 0.94 买入，基准价 × 0.97 卖出
- ...以此类推，共 5 档
- 每档资金 = 总资金 ÷ 5，买入数量 = floor(每档资金 ÷ 买入价 ÷ 100) × 100 股
- 若某档买入价过高（每档资金不足买1手），则跳过该档

---

## 运行测试

```bash
cd grid_backend
python manage.py test trader --settings=grid_backend.test_settings
```

---

## 目录结构

```
grid-trader/
├── grid_backend/          # Django 后端项目
│   ├── grid_backend/      # 项目配置
│   │   ├── settings.py
│   │   ├── test_settings.py
│   │   └── urls.py
│   ├── trader/            # 主应用
│   │   ├── models.py      # 数据模型
│   │   ├── views.py       # API 视图
│   │   ├── serializers.py # 序列化器
│   │   ├── urls.py        # 路由配置
│   │   └── tests.py       # 单元测试
│   ├── requirements.txt
│   └── manage.py
├── frontend/              # Vue 3 前端项目
│   ├── src/
│   │   ├── components/
│   │   │   ├── PlanList.vue    # 计划列表页
│   │   │   ├── PlanDetail.vue  # 计划详情与操作页
│   │   │   └── Statistics.vue  # 收益统计页
│   │   ├── api/index.js   # API 封装
│   │   ├── router.js      # 路由配置
│   │   ├── App.vue        # 根组件
│   │   └── main.js        # 入口文件
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── README.md
```