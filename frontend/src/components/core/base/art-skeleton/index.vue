<script setup lang="ts">
  defineOptions({ name: 'ArtSkeleton' })

  interface Props {
    // 骨架屏类型: 'card' | 'list' | 'table' | 'dashboard'
    type?: 'card' | 'list' | 'table' | 'dashboard'
    // 是否显示动画
    animated?: boolean
    // 行数（用于列表和表格）
    rows?: number
    // 自定义类名
    customClass?: string
  }

  withDefaults(defineProps<Props>(), {
    type: 'card',
    animated: true,
    rows: 5,
    customClass: ''
  })
</script>

<template>
  <div
    class="art-skeleton"
    :class="[`art-skeleton--${type}`, { 'art-skeleton--animated': animated }, customClass]"
  >
    <!-- 卡片骨架屏 -->
    <template v-if="type === 'card'">
      <div class="skeleton-header">
        <div class="skeleton-avatar"></div>
        <div class="skeleton-title-wrapper">
          <div class="skeleton-title"></div>
          <div class="skeleton-subtitle"></div>
        </div>
      </div>
      <div class="skeleton-content">
        <div v-for="i in 3" :key="i" class="skeleton-line"></div>
      </div>
      <div class="skeleton-footer">
        <div class="skeleton-button"></div>
        <div class="skeleton-button"></div>
      </div>
    </template>

    <!-- 列表骨架屏 -->
    <template v-else-if="type === 'list'">
      <div v-for="i in rows" :key="i" class="skeleton-list-item">
        <div class="skeleton-icon"></div>
        <div class="skeleton-text-wrapper">
          <div class="skeleton-line short"></div>
          <div class="skeleton-line"></div>
        </div>
      </div>
    </template>

    <!-- 表格骨架屏 -->
    <template v-else-if="type === 'table'">
      <div class="skeleton-table-header">
        <div v-for="i in 4" :key="i" class="skeleton-th"></div>
      </div>
      <div v-for="row in rows" :key="row" class="skeleton-table-row">
        <div v-for="col in 4" :key="col" class="skeleton-td">
          <div class="skeleton-cell"></div>
        </div>
      </div>
    </template>

    <!-- 仪表盘骨架屏 -->
    <template v-else-if="type === 'dashboard'">
      <div class="skeleton-dashboard">
        <!-- 顶部统计卡片 -->
        <div class="skeleton-stats-row">
          <div v-for="i in 4" :key="i" class="skeleton-stat-card">
            <div class="skeleton-stat-icon"></div>
            <div class="skeleton-stat-content">
              <div class="skeleton-stat-value"></div>
              <div class="skeleton-stat-label"></div>
            </div>
          </div>
        </div>
        <!-- 图表区域 -->
        <div class="skeleton-charts-row">
          <div class="skeleton-chart-main">
            <div class="skeleton-chart-header">
              <div class="skeleton-chart-title"></div>
            </div>
            <div class="skeleton-chart-body">
              <div class="skeleton-chart-line"></div>
              <div class="skeleton-chart-bars">
                <div v-for="i in 7" :key="i" class="skeleton-bar"></div>
              </div>
            </div>
          </div>
          <div class="skeleton-chart-side">
            <div class="skeleton-chart-header">
              <div class="skeleton-chart-title"></div>
            </div>
            <div class="skeleton-donut">
              <div class="skeleton-donut-ring"></div>
              <div class="skeleton-donut-center"></div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
  /* 基础骨架屏样式 */
  .art-skeleton {
    width: 100%;
    padding: 20px;
    background: var(--skeleton-bg, #fff);
    border-radius: 8px;
  }

  /* 暗色模式背景 */
  :global(html.dark) .art-skeleton {
    --skeleton-bg: #1e293b;
  }

  /* 骨架元素基础样式 */
  .skeleton-header,
  .skeleton-content,
  .skeleton-footer,
  .skeleton-list-item,
  .skeleton-table-header,
  .skeleton-table-row,
  .skeleton-stats-row,
  .skeleton-charts-row {
    display: flex;
    align-items: center;
  }

  /* 通用骨架块 */
  .skeleton-avatar,
  .skeleton-title,
  .skeleton-subtitle,
  .skeleton-line,
  .skeleton-button,
  .skeleton-icon,
  .skeleton-th,
  .skeleton-cell,
  .skeleton-stat-icon,
  .skeleton-stat-value,
  .skeleton-stat-label,
  .skeleton-chart-title,
  .skeleton-bar,
  .skeleton-donut-ring,
  .skeleton-donut-center {
    background: var(--skeleton-block-bg, #e2e8f0);
    border-radius: 4px;
  }

  /* 暗色模式骨架块 */
  :global(html.dark) .skeleton-avatar,
  :global(html.dark) .skeleton-title,
  :global(html.dark) .skeleton-subtitle,
  :global(html.dark) .skeleton-line,
  :global(html.dark) .skeleton-button,
  :global(html.dark) .skeleton-icon,
  :global(html.dark) .skeleton-th,
  :global(html.dark) .skeleton-cell,
  :global(html.dark) .skeleton-stat-icon,
  :global(html.dark) .skeleton-stat-value,
  :global(html.dark) .skeleton-stat-label,
  :global(html.dark) .skeleton-chart-title,
  :global(html.dark) .skeleton-bar,
  :global(html.dark) .skeleton-donut-ring,
  :global(html.dark) .skeleton-donut-center {
    --skeleton-block-bg: #334155;
  }

  /* 动画效果 */
  .art-skeleton--animated .skeleton-avatar,
  .art-skeleton--animated .skeleton-title,
  .art-skeleton--animated .skeleton-subtitle,
  .art-skeleton--animated .skeleton-line,
  .art-skeleton--animated .skeleton-button,
  .art-skeleton--animated .skeleton-icon,
  .art-skeleton--animated .skeleton-th,
  .art-skeleton--animated .skeleton-cell,
  .art-skeleton--animated .skeleton-stat-icon,
  .art-skeleton--animated .skeleton-stat-value,
  .art-skeleton--animated .skeleton-stat-label,
  .art-skeleton--animated .skeleton-chart-title,
  .art-skeleton--animated .skeleton-bar,
  .art-skeleton--animated .skeleton-donut-ring,
  .art-skeleton--animated .skeleton-donut-center {
    background: linear-gradient(
      90deg,
      var(--skeleton-block-bg, #e2e8f0) 25%,
      var(--skeleton-shine, #f1f5f9) 50%,
      var(--skeleton-block-bg, #e2e8f0) 75%
    );
    background-size: 200% 100%;
    animation: skeleton-shine 1.5s ease-in-out infinite;
  }

  :global(html.dark) .art-skeleton--animated .skeleton-avatar,
  :global(html.dark) .art-skeleton--animated .skeleton-title,
  :global(html.dark) .art-skeleton--animated .skeleton-subtitle,
  :global(html.dark) .art-skeleton--animated .skeleton-line,
  :global(html.dark) .art-skeleton--animated .skeleton-button,
  :global(html.dark) .art-skeleton--animated .skeleton-icon,
  :global(html.dark) .art-skeleton--animated .skeleton-th,
  :global(html.dark) .art-skeleton--animated .skeleton-cell,
  :global(html.dark) .art-skeleton--animated .skeleton-stat-icon,
  :global(html.dark) .art-skeleton--animated .skeleton-stat-value,
  :global(html.dark) .art-skeleton--animated .skeleton-stat-label,
  :global(html.dark) .art-skeleton--animated .skeleton-chart-title,
  :global(html.dark) .art-skeleton--animated .skeleton-bar,
  :global(html.dark) .art-skeleton--animated .skeleton-donut-ring,
  :global(html.dark) .art-skeleton--animated .skeleton-donut-center {
    --skeleton-shine: #475569;
  }

  @keyframes skeleton-shine {
    0% {
      background-position: 200% 0;
    }
    100% {
      background-position: -200% 0;
    }
  }

  /* 卡片骨架屏 */
  .art-skeleton--card {
    max-width: 400px;
  }

  .art-skeleton--card .skeleton-header {
    margin-bottom: 20px;
  }

  .art-skeleton--card .skeleton-avatar {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    margin-right: 16px;
  }

  .art-skeleton--card .skeleton-title-wrapper {
    flex: 1;
  }

  .art-skeleton--card .skeleton-title {
    width: 60%;
    height: 20px;
    margin-bottom: 8px;
  }

  .art-skeleton--card .skeleton-subtitle {
    width: 40%;
    height: 14px;
  }

  .art-skeleton--card .skeleton-content {
    flex-direction: column;
    align-items: stretch;
    margin-bottom: 20px;
  }

  .art-skeleton--card .skeleton-line {
    height: 16px;
    margin-bottom: 12px;
  }

  .art-skeleton--card .skeleton-line:last-child {
    width: 80%;
  }

  .art-skeleton--card .skeleton-footer {
    justify-content: flex-end;
    gap: 12px;
  }

  .art-skeleton--card .skeleton-button {
    width: 80px;
    height: 36px;
    border-radius: 6px;
  }

  /* 列表骨架屏 */
  .art-skeleton--list {
    flex-direction: column;
  }

  .skeleton-list-item {
    width: 100%;
    padding: 16px 0;
    border-bottom: 1px solid var(--skeleton-border, #e2e8f0);
  }

  :global(html.dark) .skeleton-list-item {
    --skeleton-border: #334155;
  }

  .skeleton-list-item:last-child {
    border-bottom: none;
  }

  .skeleton-list-item .skeleton-icon {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    margin-right: 16px;
  }

  .skeleton-list-item .skeleton-text-wrapper {
    flex: 1;
  }

  .skeleton-list-item .skeleton-line {
    height: 16px;
    margin-bottom: 8px;
  }

  .skeleton-list-item .skeleton-line.short {
    width: 40%;
  }

  /* 表格骨架屏 */
  .art-skeleton--table {
    flex-direction: column;
  }

  .skeleton-table-header {
    width: 100%;
    padding: 16px;
    background: var(--skeleton-header-bg, #f8fafc);
    border-radius: 8px 8px 0 0;
  }

  :global(html.dark) .skeleton-table-header {
    --skeleton-header-bg: #0f172a;
  }

  .skeleton-table-header .skeleton-th {
    flex: 1;
    height: 20px;
    margin-right: 16px;
  }

  .skeleton-table-header .skeleton-th:last-child {
    margin-right: 0;
  }

  .skeleton-table-row {
    width: 100%;
    padding: 16px;
    border-bottom: 1px solid var(--skeleton-border, #e2e8f0);
  }

  .skeleton-table-row:last-child {
    border-bottom: none;
    border-radius: 0 0 8px 8px;
  }

  .skeleton-table-row .skeleton-td {
    flex: 1;
    margin-right: 16px;
  }

  .skeleton-table-row .skeleton-td:last-child {
    margin-right: 0;
  }

  .skeleton-table-row .skeleton-cell {
    height: 16px;
  }

  /* 仪表盘骨架屏 */
  .art-skeleton--dashboard {
    flex-direction: column;
  }

  .skeleton-dashboard {
    width: 100%;
  }

  .skeleton-stats-row {
    justify-content: space-between;
    margin-bottom: 24px;
    gap: 16px;
  }

  .skeleton-stat-card {
    flex: 1;
    display: flex;
    align-items: center;
    padding: 20px;
    background: var(--skeleton-card-bg, #f8fafc);
    border-radius: 12px;
  }

  :global(html.dark) .skeleton-stat-card {
    --skeleton-card-bg: #0f172a;
  }

  .skeleton-stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    margin-right: 16px;
  }

  .skeleton-stat-content {
    flex: 1;
  }

  .skeleton-stat-value {
    width: 60%;
    height: 28px;
    margin-bottom: 8px;
  }

  .skeleton-stat-label {
    width: 40%;
    height: 16px;
  }

  .skeleton-charts-row {
    gap: 24px;
  }

  .skeleton-chart-main,
  .skeleton-chart-side {
    flex: 1;
    padding: 20px;
    background: var(--skeleton-card-bg, #f8fafc);
    border-radius: 12px;
  }

  .skeleton-chart-side {
    max-width: 350px;
  }

  .skeleton-chart-header {
    margin-bottom: 20px;
  }

  .skeleton-chart-title {
    width: 40%;
    height: 20px;
  }

  .skeleton-chart-body {
    position: relative;
    height: 200px;
  }

  .skeleton-chart-line {
    position: absolute;
    top: 50%;
    left: 0;
    right: 0;
    height: 2px;
    background: var(--skeleton-block-bg, #e2e8f0);
    transform: translateY(-50%);
  }

  .skeleton-chart-bars {
    display: flex;
    align-items: flex-end;
    justify-content: space-around;
    height: 100%;
    padding: 0 20px;
  }

  .skeleton-bar {
    width: 32px;
    border-radius: 4px 4px 0 0;
  }

  .skeleton-bar:nth-child(1) {
    height: 60%;
  }
  .skeleton-bar:nth-child(2) {
    height: 80%;
  }
  .skeleton-bar:nth-child(3) {
    height: 45%;
  }
  .skeleton-bar:nth-child(4) {
    height: 90%;
  }
  .skeleton-bar:nth-child(5) {
    height: 70%;
  }
  .skeleton-bar:nth-child(6) {
    height: 55%;
  }
  .skeleton-bar:nth-child(7) {
    height: 85%;
  }

  .skeleton-donut {
    position: relative;
    width: 150px;
    height: 150px;
    margin: 0 auto;
  }

  .skeleton-donut-ring {
    width: 100%;
    height: 100%;
    border-radius: 50%;
  }

  .skeleton-donut-center {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 60%;
    height: 60%;
    background: var(--skeleton-card-bg, #f8fafc);
    border-radius: 50%;
  }

  :global(html.dark) .skeleton-donut-center {
    background: var(--default-bg-color);
  }

  /* 响应式适配 */
  @media (max-width: 768px) {
    .skeleton-stats-row {
      flex-wrap: wrap;
    }

    .skeleton-stat-card {
      flex: 1 1 calc(50% - 8px);
      min-width: 140px;
    }

    .skeleton-charts-row {
      flex-direction: column;
    }

    .skeleton-chart-side {
      max-width: 100%;
    }
  }
</style>
