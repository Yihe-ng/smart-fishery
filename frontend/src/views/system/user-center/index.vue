<script setup lang="ts">
  import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
  import { fetchChangePassword } from '@/api/auth'
  import { fetchUpdateUser } from '@/api/system-manage'
  import { useUserStore } from '@/store/modules/user'

  defineOptions({ name: 'UserCenter' })

  const userStore = useUserStore()
  const userInfo = computed(() => userStore.getUserInfo)

  const profileFormRef = ref<FormInstance>()
  const passwordFormRef = ref<FormInstance>()
  const profileLoading = ref(false)
  const passwordLoading = ref(false)

  const profileForm = reactive({
    userName: '',
    userPhone: '',
    email: ''
  })

  const passwordForm = reactive({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  })

  const profileRules: FormRules = {
    userPhone: [
      { required: true, message: '请输入手机号', trigger: 'blur' },
      { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号格式', trigger: 'blur' }
    ],
    email: [
      { required: true, message: '请输入邮箱', trigger: 'blur' },
      { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
    ]
  }

  const passwordRules: FormRules = {
    currentPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
    newPassword: [
      { required: true, message: '请输入新密码', trigger: 'blur' },
      { min: 6, message: '新密码至少 6 位', trigger: 'blur' }
    ],
    confirmPassword: [
      { required: true, message: '请确认新密码', trigger: 'blur' },
      {
        validator: (_rule, value, callback) => {
          if (!value) {
            callback(new Error('请确认新密码'))
            return
          }
          if (value !== passwordForm.newPassword) {
            callback(new Error('两次输入的密码不一致'))
            return
          }
          callback()
        },
        trigger: 'blur'
      }
    ]
  }

  const syncProfileForm = () => {
    profileForm.userName = userInfo.value.userName ?? ''
    profileForm.userPhone = userInfo.value.userPhone ?? ''
    profileForm.email = userInfo.value.email ?? ''
  }

  onMounted(() => {
    syncProfileForm()
  })

  watch(
    () => [userInfo.value.userName, userInfo.value.userPhone, userInfo.value.email],
    () => {
      syncProfileForm()
    }
  )

  const handleSaveProfile = async () => {
    if (!userInfo.value.userId) {
      ElMessage.error('未获取到当前用户信息')
      return
    }

    const valid = await profileFormRef.value?.validate().catch(() => false)
    if (!valid) {
      return
    }

    profileLoading.value = true
    try {
      const payload: Api.SystemManage.UserUpdateParams = {
        userPhone: profileForm.userPhone,
        userEmail: profileForm.email
      }
      const updated = await fetchUpdateUser(userInfo.value.userId, payload)
      userStore.updateUserProfile({
        email: updated.userEmail || profileForm.email,
        userPhone: updated.userPhone || profileForm.userPhone
      })
      ElMessage.success('账号信息保存成功')
    } catch (error) {
      console.error('Failed to update profile:', error)
      ElMessage.error('账号信息保存失败')
    } finally {
      profileLoading.value = false
    }
  }

  const handleChangePassword = async () => {
    const valid = await passwordFormRef.value?.validate().catch(() => false)
    if (!valid) {
      return
    }

    passwordLoading.value = true
    try {
      await fetchChangePassword(passwordForm)
      passwordForm.currentPassword = ''
      passwordForm.newPassword = ''
      passwordForm.confirmPassword = ''
      passwordFormRef.value?.clearValidate()
      ElMessage.success('密码修改成功')
    } catch (error) {
      console.error('Failed to change password:', error)
      ElMessage.error('密码修改失败')
    } finally {
      passwordLoading.value = false
    }
  }
</script>

<template>
  <div class="page-container user-center-page">
    <div class="art-card-sm">
      <h1 class="p-4 text-xl font-normal border-b border-g-300">账号信息</h1>

      <ElForm
        ref="profileFormRef"
        :model="profileForm"
        :rules="profileRules"
        class="box-border p-5"
        label-position="top"
      >
        <ElRow :gutter="20">
          <ElCol :xs="24" :md="12">
            <ElFormItem label="用户名">
              <ElInput v-model="profileForm.userName" disabled />
            </ElFormItem>
          </ElCol>
          <ElCol :xs="24" :md="12">
            <ElFormItem label="手机号" prop="userPhone">
              <ElInput v-model="profileForm.userPhone" placeholder="请输入手机号" />
            </ElFormItem>
          </ElCol>
        </ElRow>

        <ElRow :gutter="20">
          <ElCol :xs="24" :md="12">
            <ElFormItem label="邮箱" prop="email">
              <ElInput v-model="profileForm.email" placeholder="请输入邮箱" />
            </ElFormItem>
          </ElCol>
        </ElRow>

        <div class="flex justify-end">
          <ElButton type="primary" :loading="profileLoading" @click="handleSaveProfile">
            保存
          </ElButton>
        </div>
      </ElForm>
    </div>

    <div class="art-card-sm mt-5">
      <h1 class="p-4 text-xl font-normal border-b border-g-300">修改密码</h1>

      <ElForm
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        class="box-border p-5"
        label-position="top"
      >
        <ElRow :gutter="20">
          <ElCol :xs="24" :md="12">
            <ElFormItem label="当前密码" prop="currentPassword">
              <ElInput
                v-model="passwordForm.currentPassword"
                type="password"
                show-password
                placeholder="请输入当前密码"
              />
            </ElFormItem>
          </ElCol>
          <ElCol :xs="24" :md="12">
            <ElFormItem label="新密码" prop="newPassword">
              <ElInput
                v-model="passwordForm.newPassword"
                type="password"
                show-password
                placeholder="请输入新密码"
              />
            </ElFormItem>
          </ElCol>
        </ElRow>

        <ElRow :gutter="20">
          <ElCol :xs="24" :md="12">
            <ElFormItem label="确认新密码" prop="confirmPassword">
              <ElInput
                v-model="passwordForm.confirmPassword"
                type="password"
                show-password
                placeholder="请再次输入新密码"
              />
            </ElFormItem>
          </ElCol>
        </ElRow>

        <div class="flex justify-end">
          <ElButton type="primary" :loading="passwordLoading" @click="handleChangePassword">
            保存
          </ElButton>
        </div>
      </ElForm>
    </div>
  </div>
</template>
