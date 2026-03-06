<template>
  <div class="pond-detail-page">
    <page-content>
      <el-card shadow="never">
        <template #header>
          <div class="flex-cb">
            <span>试验池详情</span>
            <el-button icon="ri:arrow-left-line" @click="router.back()">返回列表</el-button>
          </div>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="池子名称">试验池 A</el-descriptions-item>
          <el-descriptions-item label="池子编号">P001</el-descriptions-item>
          <el-descriptions-item label="养殖鱼类">大西洋鲑</el-descriptions-item>
          <el-descriptions-item label="鱼数量">1200 尾</el-descriptions-item>
          <el-descriptions-item label="容积">50 m³</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag type="success">运行中</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">工厂化循环水养殖试验池</el-descriptions-item>
        </el-descriptions>
      </el-card>
    </page-content>
  </div>
</template>

<script setup lang="ts">
  const router = useRouter()
</script>
