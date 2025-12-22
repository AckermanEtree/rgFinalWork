<template>
    <div v-if="!isLoggedIn" class="login-container">
        <div class="login-box">
            <h2>🔐 校园圈 (联机版)</h2>
            <p>请输入后端数据库中的账号</p>
            <input type="text" v-model="loginForm.username" placeholder="用户名 (如: admin)" />
            <input type="password" v-model="loginForm.password" placeholder="密码 (如: 123456)" />
            <button @click="handleLogin" :disabled="isLoading">
                {{ isLoading ? '登录中...' : '登录' }}
            </button>
            <p v-if="errorMsg" class="error-text">{{ errorMsg }}</p>
        </div>
    </div>

    <div v-else class="app-container">
        <div class="header">
            <div class="title">📌 校园生活圈</div>
            <div class="user-info">
                <span>当前用户: {{ currentUser.nickname || currentUser.username }}</span>
                <span @click="logout" class="logout-btn">退出</span>
            </div>
        </div>

        <div class="search-bar">
            <input v-model="searchQuery" @keyup.enter="handleSearch" placeholder="🔍 搜内容/标签，回车搜索..." />
            <button @click="handleSearch">搜索</button>
        </div>

        <div class="post-box">
            <div class="box-title">{{ isEditing ? '✏️ 修改动态' : '📝 发布新动态' }}</div>
            <textarea v-model="inputContent" placeholder="分享你的新鲜事..." rows="3"></textarea>

            <div class="tools">
                <label class="file-btn">
                    <span v-if="isUploading">⏳ 上传中...</span>
                    <span v-else>📷/📹 上传文件</span>
                    <input type="file" @change="handleFileUpload" accept="image/*,video/*" style="display: none" :disabled="isUploading" />
                </label>

                <input v-model="inputTag" placeholder="#标签" class="tag-input" />

                <button @click="savePost" class="pub-btn" :class="{ 'edit-mode': isEditing }" :disabled="isUploading">
                    {{ isEditing ? '保存修改' : '发布' }}
                </button>
                <button v-if="isEditing" @click="cancelEdit" class="cancel-btn">取消</button>
            </div>

            <div v-if="previewUrl" class="preview-area">
                <video v-if="previewType === 'video'" :src="previewUrl" controls></video>
                <img v-else :src="previewUrl" />
                <span @click="clearPreview" class="close-btn">×</span>
            </div>
        </div>

        <div class="feed-list">
            <div v-if="isLoading" class="loading-tip">加载中...</div>
            <div v-else-if="postList.length === 0" class="empty-tip">暂无内容，快来发布第一条吧！</div>

            <div v-for="item in postList" :key="item.id" class="card">
                <div class="card-header">
                    <div class="user-meta">
                        <div class="avatar"></div>
                        <div>
                            <div class="name">{{ item.author }}</div>
                            <div class="time">{{ formatDate(item.createTime) }}</div>
                        </div>
                    </div>
                    <div class="ops" v-if="canOperate(item)">
                        <button @click="editPost(item)">修改</button>
                        <button @click="deletePost(item.id)" style="color:red">删除</button>
                    </div>
                </div>

                <div class="card-content">{{ item.content }}</div>

                <div v-if="item.mediaUrl" class="media-display">
                    <video v-if="item.mediaType === 'video'" :src="item.mediaUrl" controls></video>
                    <img v-else :src="item.mediaUrl" />
                </div>

                <div class="tags-row">
                    <span class="tag">{{ item.tags }}</span>
                </div>

                <hr style="border:0; border-top:1px solid #eee; margin: 10px 0;" />

                <div class="interaction-area">
                    <div class="rating-box">
                        <span>评分: </span>
                        <span v-for="star in 5" :key="star"
                              class="star"
                              :class="{ active: star <= (item.tempRating || item.score) }"
                              @click="ratePost(item, star)">★</span>
                    </div>

                    <div class="comments-list">
                        <div v-for="comment in item.comments" :key="comment.id" class="comment-item">
                            <span class="c-user">{{ comment.username || '匿名' }}:</span> {{ comment.content }}
                        </div>
                    </div>

                    <div class="comment-input">
                        <input v-model="item.newComment" placeholder="写评论..." @keyup.enter="submitComment(item)" />
                        <button @click="submitComment(item)">发送</button>
                    </div>
                </div>

            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

// ================= 配置区 =================
// 后端地址，如果后端端口改了这里也要改
const API_BASE = 'http://localhost:8080/api'
// ==========================================

// 状态变量
const isLoggedIn = ref(false)
const isLoading = ref(false)
const isUploading = ref(false)
const errorMsg = ref('')
const currentUser = ref({}) // 存登录后的用户信息
const loginForm = ref({ username: '', password: '' })

const postList = ref([])
const searchQuery = ref('')

// 编辑/发布相关
const inputContent = ref('')
const inputTag = ref('')
const previewUrl = ref('')
const previewType = ref('image')
const isEditing = ref(false)
const editingId = ref(null)

// --- 1. 登录功能 (Login) ---
const handleLogin = async () => {
  if (!loginForm.value.username || !loginForm.value.password) return
  isLoading.value = true
  errorMsg.value = ''

  try {
    // 真实请求：POST /api/login
    // 注意：这里假设后端返回 { code: 200, data: { user... } }
    // 如果后端直接返回 user 对象，请去掉 .data
    const res = await axios.post(`${API_BASE}/login`, loginForm.value)

    // 假设后端返回的数据结构里包含用户信息
    currentUser.value = res.data
    isLoggedIn.value = true

    // 登录成功后，立马获取列表
    fetchPosts()
  } catch (err) {
    console.error(err)
    errorMsg.value = '登录失败，请检查账号密码或后端是否启动'
  } finally {
    isLoading.value = false
  }
}

const logout = () => {
  isLoggedIn.value = false
  loginForm.value = { username: '', password: '' }
  postList.value = []
}

// --- 2. 获取列表 (Read) ---
const fetchPosts = async () => {
  isLoading.value = true
  try {
    // 真实请求：GET /api/posts?keyword=xxx
    const url = searchQuery.value
      ? `${API_BASE}/posts?keyword=${searchQuery.value}`
      : `${API_BASE}/posts`

    const res = await axios.get(url)
    postList.value = res.data
  } catch (err) {
    alert("获取列表失败")
  } finally {
    isLoading.value = false
  }
}

const handleSearch = () => {
  fetchPosts()
}

// --- 3. 文件上传 (Upload) ---
const handleFileUpload = async (e) => {
  const file = e.target.files[0]
  if (!file) return

  // 判断类型用于预览
  previewType.value = file.type.startsWith('video') ? 'video' : 'image'
  isUploading.value = true

  const formData = new FormData()
  formData.append('file', file)

  try {
    // 真实请求：POST /api/upload
    // 后端应返回文件的 http 访问地址
    const res = await axios.post(`${API_BASE}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    previewUrl.value = res.data // 把后端返回的 URL 存起来
  } catch (err) {
    alert("文件上传失败")
    previewUrl.value = ''
  } finally {
    isUploading.value = false
  }
}

// --- 4. 发布与修改 (Create & Update) ---
const savePost = async () => {
  if (!inputContent.value) return alert("内容不能为空")

  const postData = {
    content: inputContent.value,
    tags: inputTag.value,
    mediaUrl: previewUrl.value,
    mediaType: previewType.value,
    // 如果是修改，发ID；如果是新增，后端自动生成ID
    // 注意：通常后端需要从 Session 获取当前用户，这里为了简单，显式传一下 author
    author: currentUser.value.username
  }

  try {
    if (isEditing.value) {
      // 修改：PUT /api/posts/{id}
      await axios.put(`${API_BASE}/posts/${editingId.value}`, postData)
      alert("修改成功")
    } else {
      // 新增：POST /api/posts
      await axios.post(`${API_BASE}/posts`, postData)
      alert("发布成功")
    }
    // 成功后刷新列表并清空表单
    clearForm()
    fetchPosts()
  } catch (err) {
    alert("操作失败")
  }
}

// --- 5. 删除 (Delete) ---
const deletePost = async (id) => {
  if (!confirm("确定删除吗？")) return
  try {
    // 真实请求：DELETE /api/posts/{id}
    await axios.delete(`${API_BASE}/posts/${id}`)
    // 从本地列表中移除，或者重新 fetchPosts()
    postList.value = postList.value.filter(p => p.id !== id)
  } catch (err) {
    alert("删除失败")
  }
}

// --- 6. 互动 (Comment & Rate) ---
const submitComment = async (item) => {
  if (!item.newComment) return
  try {
    // 真实请求：POST /api/posts/{id}/interact
    await axios.post(`${API_BASE}/posts/${item.id}/comment`, {
      content: item.newComment,
      username: currentUser.value.username
    })
    // 简单起见，刷新整个列表看到新评论
    fetchPosts()
  } catch (err) {
    alert("评论失败")
  }
}

const ratePost = async (item, star) => {
  item.tempRating = star // 视觉上先亮起来
  try {
    await axios.post(`${API_BASE}/posts/${item.id}/score`, {
      score: star
    })
    // 不需要刷新，假装成功即可，或者 fetchPosts
  } catch (err) {
    alert("评分失败")
  }
}

// --- 辅助函数 ---
const editPost = (item) => {
  isEditing.value = true
  editingId.value = item.id
  inputContent.value = item.content
  inputTag.value = item.tags
  previewUrl.value = item.mediaUrl
  previewType.value = item.mediaType
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const cancelEdit = () => {
  isEditing.value = false
  editingId.value = null
  clearForm()
}

const clearForm = () => {
  inputContent.value = ''
  inputTag.value = ''
  previewUrl.value = ''
  isUploading.value = false
}

const clearPreview = () => {
  previewUrl.value = ''
}

// 简单的日期格式化
const formatDate = (str) => {
  if (!str) return ''
  return new Date(str).toLocaleString()
}

// 判断是否有权限操作 (作者本人或管理员)
const canOperate = (item) => {
  return currentUser.value.role === 'ADMIN' || item.author === currentUser.value.username
}
</script>

<style>
    body {
        background: #f0f2f5;
        margin: 0;
        font-family: sans-serif;
    }

    .login-container {
        height: 100vh;
        display: flex;
        justify-content: center;
        align-items: center;
        background: #eef2f7;
    }

    .login-box {
        background: white;
        padding: 40px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        width: 300px;
    }

        .login-box input {
            display: block;
            width: 100%;
            margin: 10px 0;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-sizing: border-box;
        }

        .login-box button {
            width: 100%;
            padding: 10px;
            background: #409eff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }

    .error-text {
        color: red;
        font-size: 12px;
    }

    .app-container {
        max-width: 600px;
        margin: 0 auto;
        background: white;
        min-height: 100vh;
        padding-bottom: 50px;
    }

    .header {
        padding: 15px 20px;
        background: white;
        border-bottom: 1px solid #eee;
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: sticky;
        top: 0;
        z-index: 99;
    }

    .title {
        font-weight: bold;
        font-size: 18px;
    }

    .logout-btn {
        color: #888;
        font-size: 12px;
        margin-left: 10px;
        cursor: pointer;
    }

    .search-bar {
        padding: 10px 20px;
        background: #fafafa;
        display: flex;
        gap: 10px;
    }

        .search-bar input {
            flex: 1;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 20px;
            text-align: center;
        }

        .search-bar button {
            padding: 5px 15px;
            border-radius: 20px;
            border: none;
            background: #409eff;
            color: white;
            cursor: pointer;
        }

    .post-box {
        padding: 20px;
        border-bottom: 8px solid #f0f2f5;
    }

    .box-title {
        font-weight: bold;
        margin-bottom: 10px;
        color: #333;
    }

    textarea {
        width: 100%;
        border: 1px solid #eee;
        padding: 10px;
        border-radius: 8px;
        resize: none;
        box-sizing: border-box;
    }

    .tools {
        margin-top: 10px;
        display: flex;
        gap: 10px;
        align-items: center;
        flex-wrap: wrap;
    }

    .file-btn {
        color: #409eff;
        cursor: pointer;
        font-size: 14px;
    }

    .tag-input {
        width: 80px;
        padding: 5px;
        border: 1px solid #ddd;
        border-radius: 4px;
    }

    .pub-btn {
        margin-left: auto;
        background: #409eff;
        color: white;
        border: none;
        padding: 6px 20px;
        border-radius: 20px;
        cursor: pointer;
    }

    .edit-mode {
        background: #e6a23c;
    }

    .cancel-btn {
        background: #909399;
        color: white;
        border: none;
        padding: 6px 15px;
        border-radius: 20px;
        cursor: pointer;
    }

    .preview-area {
        margin-top: 10px;
        position: relative;
        max-width: 100%;
    }

        .preview-area img, .preview-area video {
            max-width: 100%;
            max-height: 200px;
            border-radius: 8px;
        }

    .close-btn {
        position: absolute;
        top: 0;
        right: 0;
        background: red;
        color: white;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        text-align: center;
        line-height: 20px;
        cursor: pointer;
    }

    .card {
        padding: 20px;
        border-bottom: 1px solid #eee;
    }

    .card-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 10px;
    }

    .user-meta {
        display: flex;
        align-items: center;
    }

    .avatar {
        width: 36px;
        height: 36px;
        background: #ddd;
        border-radius: 50%;
        margin-right: 10px;
    }

    .name {
        font-weight: bold;
        font-size: 14px;
        color: #333;
    }

    .time {
        font-size: 12px;
        color: #999;
    }

    .ops button {
        font-size: 12px;
        background: none;
        border: none;
        color: #409eff;
        cursor: pointer;
        margin-left: 5px;
    }

    .card-content {
        font-size: 15px;
        margin-bottom: 10px;
        line-height: 1.5;
    }

    .media-display img, .media-display video {
        max-width: 100%;
        border-radius: 8px;
        margin-bottom: 10px;
    }

    .tag {
        background: #eef5fe;
        color: #409eff;
        font-size: 12px;
        padding: 2px 6px;
        border-radius: 4px;
    }

    .interaction-area {
        background: #fafafa;
        padding: 10px;
        border-radius: 8px;
        margin-top: 10px;
    }

    .rating-box {
        margin-bottom: 8px;
        font-size: 14px;
    }

    .star {
        cursor: pointer;
        color: #ddd;
        font-size: 18px;
        margin-right: 2px;
    }

        .star.active {
            color: #f7ba2a;
        }

    .comments-list {
        font-size: 13px;
        color: #666;
        margin-bottom: 8px;
    }

    .comment-item {
        margin-bottom: 4px;
    }

    .c-user {
        color: #333;
        font-weight: bold;
    }

    .comment-input {
        display: flex;
        gap: 5px;
    }

        .comment-input input {
            flex: 1;
            border: 1px solid #ddd;
            padding: 5px;
            border-radius: 4px;
        }

        .comment-input button {
            background: #67c23a;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            padding: 0 10px;
        }

    .loading-tip, .empty-tip {
        text-align: center;
        padding: 20px;
        color: #999;
    }
</style>