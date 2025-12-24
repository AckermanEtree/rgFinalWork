<template>
    <div v-if="!isLoggedIn" class="login-container">
        <div class="login-box">
            <h2>🔐 校园圈 (Flask联调版)</h2>
            <p>请输入后端数据库中的账号</p>
            <input type="text" v-model="loginForm.username" placeholder="用户名" />
            <input type="password" v-model="loginForm.password" placeholder="密码" />
            <!-- <button @click="handleLogin" :disabled="isLoading">
                {{ isLoading ? '登录中...' : '登录' }}
            </button> -->
            <button @click="isRegistering ? handleRegister() : handleLogin()" :disabled="isLoading">
                {{ isLoading ? (isRegistering ? '注册中...' : '登录中...') : (isRegistering ? '注册' : '登录') }}
            </button>

            <button @click="toggleMode" class="switch-btn">
                {{ isRegistering ? '返回登录' : '去注册' }}
            </button>
            <p v-if="errorMsg" class="error-text">{{ errorMsg }}</p>
        </div>
        
    </div>

    <div v-else class="app-container">
        <div class="header">
            <div class="title">📌 校园生活圈</div>
            <div class="user-info">
                <span>当前用户: {{ currentUser.username }}</span>
                <span @click="logout" class="logout-btn">退出</span>
            </div>
        </div>

        <div class="search-bar">
            <input v-model="searchQuery" @keyup.enter="handleSearch" placeholder="🔍 搜索标签 (如: 美食)..." />
            <button @click="handleSearch">搜索</button>
        </div>

        <div class="post-box">
            <div class="box-title">{{ isEditing ? '✏️ 修改动态' : '📝 发布新动态' }}</div>
            <textarea v-model="inputContent" placeholder="分享你的新鲜事..." rows="3"></textarea>

            <div class="tools">
                <label class="file-btn">
                    <span v-if="isUploading">⏳ 处理中...</span>
                    <span v-else>📷/📹 选图(仅预览)</span>
                    <input type="file" @change="handleFileSelect" accept="image/*,video/*" style="display: none" />
                </label>

                <input v-model="inputTag" placeholder="#标签 (空格分隔)" class="tag-input" />

                <button @click="savePost" class="pub-btn" :class="{ 'edit-mode': isEditing }" :disabled="isUploading">
                    {{ isEditing ? '保存修改' : '发布' }}
                </button>
                <button v-if="isEditing" @click="cancelEdit" class="cancel-btn">取消</button>
            </div>

            <div v-if="previewUrl" class="preview-area">
                <video v-if="previewType === 'video'" :src="previewUrl" controls></video>
                <img v-else :src="previewUrl" />
                <span @click="clearPreview" class="close-btn">×</span>
                <div style="font-size:12px; color:orange; margin-top:5px;">⚠️ 提示: 后端未提供上传接口，此图片仅本地可见</div>
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
                            <div class="name">{{ item.authorName || ('用户ID:' + item.authorId) }}</div>
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

                <div class="tags-row" v-if="item.tags && item.tags.length">
                    <span class="tag" v-for="(t, i) in item.tags" :key="i">#{{ t }}</span>
                </div>

                <hr style="border:0; border-top:1px solid #eee; margin: 10px 0;" />

                <div class="interaction-area">
                    <div class="rating-box">
                        <span>评分: </span>
                        <span v-for="star in 5" :key="star"
                              class="star"
                              :class="{ active: star <= (item.myRating || item.avgScore || 0) }"
                              @click="ratePost(item, star)">★</span>
                    </div>

                    <div class="comments-list">
                        <div v-for="(comment, idx) in item.comments" :key="idx" class="comment-item">
                            <span class="c-user">{{ comment.username }}:</span> {{ comment.content }}
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
    import { ref } from 'vue'
    import axios from 'axios'

    // ================= 配置区 =================
    // 🚨 Flask 默认端口 5001
    const API_BASE = 'http://localhost:5001/api'
    // ==========================================

    // 全局状态
    const isLoggedIn = ref(false)
    const isLoading = ref(false)
    const isUploading = ref(false) // 即使不真传，也保留状态变量
    const errorMsg = ref('')
    const currentUser = ref({})
    const loginForm = ref({ username: '', password: '' })

    const postList = ref([])
    const searchQuery = ref('') // 用于搜索标签

    // 编辑/发布相关
    const inputContent = ref('')
    const inputTag = ref('')
    const previewUrl = ref('')
    const previewType = ref('image')
    const isEditing = ref(false)
    const editingId = ref(null)

    // --- 0. 核心：设置 JWT Token ---
    const setAuthToken = (token) => {
        if (token) {
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
        } else {
            delete axios.defaults.headers.common['Authorization']
        }
    }

    // --- 1. 登录 (POST /auth/login) ---
    const handleLogin = async () => {
        if (!loginForm.value.username || !loginForm.value.password) return
        isLoading.value = true
        errorMsg.value = ''

        try {
            const res = await axios.post(`${API_BASE}/auth/login`, loginForm.value)

            //解包结构：{ message: "...", data: { access_token, user } }
            const { access_token, user } = res.data.data

            setAuthToken(access_token)
            currentUser.value = user
            isLoggedIn.value = true

            // 登录成功后拉取数据
            fetchPosts()
        } catch (err) {
            console.error(err)
            errorMsg.value = err.response?.data?.message || '登录失败，请检查账号密码或后端是否启动'
        } finally {
            isLoading.value = false
        }
    }

    // 注册模式标志
    const isRegistering = ref(false)

    // 切换登录/注册模式
    const toggleMode = () => {
        isRegistering.value = !isRegistering.value
        errorMsg.value = ''
    }

    // --- 注册 (POST /auth/register) ---
    const handleRegister = async () => {
        if (!loginForm.value.username || !loginForm.value.password) return
        isLoading.value = true
        errorMsg.value = ''

        try {
            const res = await axios.post(`${API_BASE}/auth/register`, loginForm.value)
            alert("注册成功，请登录")
            isRegistering.value = false
            loginForm.value.password = ''
        } catch (err) {
            console.error(err)
            errorMsg.value = err.response?.data?.message || '注册失败，请检查输入或后端服务'
        } finally {
            isLoading.value = false
        }
    }


    const logout = () => {
        isLoggedIn.value = false
        setAuthToken(null)
        loginForm.value = { username: '', password: '' }
        postList.value = []
        currentUser.value = {}
        //登出时，清除发布框的内容
        inputContent.value = ''
        inputTag.value = ''
        previewUrl.value = ''
        // 清除编辑状态
        isEditing.value = false
        editingId.value = null
    }

    // --- 2. 获取列表 (GET /posts) ---
    const fetchPosts = async () => {
        isLoading.value = true
        try {
            const config = { params: { page: 1, per_page: 50 } }

            // 如果有搜索词，按 tag 搜索 (根据文档说明)
            if (searchQuery.value) {
                config.params.tag = searchQuery.value
            }

            const res = await axios.get(`${API_BASE}/posts`, config)

            //解包：res.data.data.items
            const items = res.data.data.items || []

            //数据清洗映射
            postList.value = items.map(item => ({
                id: item.id,
                // 如果后端没返回 username，暂时显示 ID
                authorName: item.username || item.author || 'User',
                authorId: item.user_id,
                content: item.content,
                // 后端返回的是数组 ["tag1", "tag2"]
                tags: Array.isArray(item.tags) ? item.tags : [],
                createTime: item.created_at,
                // 提取媒体
                mediaUrl: (item.media && item.media.length > 0) ? item.media[0].url : '',
                mediaType: (item.media && item.media.length > 0) ? item.media[0].type : 'image',
                // 列表接口通常不含评论，初始化为空数组
                comments: [],
                newComment: '',
                myRating: 0 // 暂无
            }))
        } catch (err) {
            console.error(err)
            alert("获取列表失败: " + (err.response?.data?.message || "网络错误"))
        } finally {
            isLoading.value = false
        }
    }

    const handleSearch = () => {
        fetchPosts()
    }

    // --- 3. 文件选择 (模拟) ---
    const handleFileSelect = (e) => {
        const file = e.target.files[0]
        if (!file) return
        previewType.value = file.type.startsWith('video') ? 'video' : 'image'
        // 生成本地 Blob URL 预览
        previewUrl.value = URL.createObjectURL(file)
    }

    // --- 4. 发布/修改 (POST/PUT /posts) ---
    const savePost = async () => {
        if (!inputContent.value) return alert("内容不能为空")

        // 构造文档要求的 JSON 格式
        const payload = {
            content: inputContent.value,
            visibility: "public",
            // 字符串转数组 "#a #b" -> ["a", "b"]
            tags: inputTag.value ? inputTag.value.replace(/#/g, '').split(' ').filter(t => t) : [],
            // 构造 media 数组
            media: previewUrl.value ? [{
                type: previewType.value,
                url: previewUrl.value, // 发给后端的是本地地址
                thumbnail_url: ""
            }] : []
        }

        try {
            if (isEditing.value) {
                await axios.put(`${API_BASE}/posts/${editingId.value}`, payload)
                alert("修改成功")
            } else {
                await axios.post(`${API_BASE}/posts`, payload)
                alert("发布成功")
            }
            clearForm()
            fetchPosts()
        } catch (err) {
            console.error(err)
            alert("操作失败: " + (err.response?.data?.message || err.message))
        }
    }

    // --- 5. 删除 (DELETE /posts/:id) ---
    const deletePost = async (id) => {
        if (!confirm("确定删除吗？")) return
        try {
            await axios.delete(`${API_BASE}/posts/${id}`)
            postList.value = postList.value.filter(p => p.id !== id)
        } catch (err) {
            alert("删除失败: " + (err.response?.data?.message || "权限不足"))
        }
    }

    // --- 6. 评论 (POST /posts/:id/comments) ---
    const submitComment = async (item) => {
        if (!item.newComment) return
        try {
            await axios.post(`${API_BASE}/posts/${item.id}/comments`, {
                content: item.newComment
            })

            // 乐观更新：直接推入本地数组显示
            if (!item.comments) item.comments = []
            item.comments.push({
                username: currentUser.value.username || '我',
                content: item.newComment
            })
            item.newComment = ''
        } catch (err) {
            alert("评论失败")
        }
    }

    // --- 7. 评分 (POST /posts/:id/ratings) ---
    const ratePost = async (item, star) => {
        try {
            await axios.post(`${API_BASE}/posts/${item.id}/ratings`, {
                score: star
            })
            item.myRating = star // 更新本地显示
        } catch (err) {
            alert("评分失败")
        }
    }

    // --- 辅助逻辑 ---
    const editPost = (item) => {
        isEditing.value = true
        editingId.value = item.id
        inputContent.value = item.content
        // 数组转字符串回显
        inputTag.value = item.tags ? item.tags.join(' ') : ''
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
    }

    const clearPreview = () => {
        previewUrl.value = ''
    }

    const formatDate = (str) => {
        if (!str) return ''
        return new Date(str).toLocaleString()
    }

    // 简单的权限判断
    const canOperate = (item) => {
        // 如果当前登录的是管理员，或者是作者本人
        if (currentUser.value.role === 'admin') return true
        // Flask 文档返回的 user 里有 id，对比 id 最准确
        if (currentUser.value.id && item.authorId) {
            return currentUser.value.id === item.authorId
        }
        return false
    }
</script>

<style>
    /* CSS 保持不变，可以直接复用之前的样式 */
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
        width: 120px;
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

    .tags-row {
        margin-bottom: 10px;
    }

    .tag {
        background: #eef5fe;
        color: #409eff;
        font-size: 12px;
        padding: 2px 6px;
        border-radius: 4px;
        margin-right: 5px;
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

    .switch-btn {
        width: 100%;
        margin-top: 10px;
        padding: 8px;
        border: none;
        background: none;
        color: #409eff;
        cursor: pointer;
        font-size: 13px;
    }


</style>

