<template>
    <div v-if="!isLoggedIn" class="login-container">
        <div class="login-box">
            <h2>🔐 欢迎来到校园圈</h2>
            <p>请设置或输入你的密码</p>
            <input type="text" v-model="loginForm.username" placeholder="用户名" />
            <input type="password" v-model="loginForm.password" placeholder="密码 (随便输)" />
            <button @click="handleLogin">登录 / 注册</button>
        </div>
    </div>

    <div v-else class="app-container">
        <div class="header">
            <div class="title">📌 校园生活圈</div>
            <div class="user-info">
                <span>用户: {{ loginForm.username }}</span>
                <span @click="isLoggedIn = false" class="logout-btn">退出</span>
            </div>
        </div>

        <div class="search-bar">
            <input v-model="searchQuery" placeholder="🔍 搜索内容、标签或日期..." />
        </div>

        <div class="post-box">
            <div class="box-title">{{ isEditing ? '✏️ 修改动态' : '📝 发布新动态' }}</div>
            <textarea v-model="inputContent" placeholder="分享你的新鲜事..." rows="3"></textarea>

            <div class="tools">
                <label class="file-btn">
                    📷/📹 图片或视频
                    <input type="file" @change="handleFileSelect" accept="image/*,video/*" style="display: none" />
                </label>

                <input v-model="inputTag" placeholder="#标签" class="tag-input" />

                <button @click="savePost" class="pub-btn" :class="{ 'edit-mode': isEditing }">
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
            <div v-if="filteredPosts.length === 0" class="empty-tip">没有找到相关内容~</div>

            <div v-for="item in filteredPosts" :key="item.id" class="card">
                <div class="card-header">
                    <div class="user-meta">
                        <div class="avatar"></div>
                        <div>
                            <div class="name">{{ item.author }}</div>
                            <div class="time">{{ item.time }}</div>
                        </div>
                    </div>
                    <div class="ops" v-if="item.author === loginForm.username">
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
                    <span class="tag">{{ item.tag }}</span>
                </div>

                <hr style="border:0; border-top:1px solid #eee; margin: 10px 0;" />

                <div class="interaction-area">
                    <div class="rating-box">
                        <span>评分: </span>
                        <span v-for="star in 5" :key="star"
                              class="star"
                              :class="{ active: star <= item.rating }"
                              @click="ratePost(item, star)">★</span>
                        <span style="font-size:12px; color:#888; margin-left:5px;">({{ item.rating }}分)</span>
                    </div>

                    <div class="comments-list">
                        <div v-for="(comment, idx) in item.comments" :key="idx" class="comment-item">
                            <span class="c-user">{{ comment.user }}:</span> {{ comment.text }}
                        </div>
                    </div>

                    <div class="comment-input">
                        <input v-model="item.tempComment" placeholder="写下你的评论..." @keyup.enter="addComment(item)" />
                        <button @click="addComment(item)">发送</button>
                    </div>
                </div>

            </div>
        </div>
    </div>
</template>

<script setup>
    import { ref, computed } from 'vue'

    // --- 1. 登录逻辑 ---
    const isLoggedIn = ref(false)
    const loginForm = ref({ username: '', password: '' })
    const handleLogin = () => {
        if (!loginForm.value.username || !loginForm.value.password) return alert("请输入用户名和密码")
        isLoggedIn.value = true
    }

    // --- 2. 核心数据 ---
    const inputContent = ref('')
    const inputTag = ref('')
    const previewUrl = ref('')
    const previewType = ref('image') // image 或 video

    // 编辑状态控制
    const isEditing = ref(false)
    const editingId = ref(null)

    // 模拟数据库数据
    const postList = ref([
        {
            id: 1,
            author: '测试用户',
            content: '这是我拍的风景视频，大家看看！',
            tag: '#旅行',
            time: '2025-10-01',
            mediaUrl: '',
            mediaType: 'image',
            rating: 4,
            comments: [{ user: '路人甲', text: '真不错！' }],
            tempComment: ''
        },
        {
            id: 2,
            author: 'Admin',
            content: '欢迎大家使用新系统。',
            tag: '#公告',
            time: '20235-9-20',
            mediaUrl: '',
            mediaType: 'image',
            rating: 5,
            comments: [],
            tempComment: ''
        }
    ])

    // --- 3. 检索功能 (Computed) ---
    const searchQuery = ref('')
    const filteredPosts = computed(() => {
        if (!searchQuery.value) return postList.value
        const q = searchQuery.value.toLowerCase()
        return postList.value.filter(post =>
            post.content.toLowerCase().includes(q) ||
            post.tag.toLowerCase().includes(q) ||
            post.time.includes(q)
        )
    })

    // --- 4. 业务逻辑 ---

    // 文件处理 (支持视频)
    const handleFileSelect = (e) => {
        const file = e.target.files[0]
        if (file) {
            previewUrl.value = URL.createObjectURL(file)
            previewType.value = file.type.startsWith('video') ? 'video' : 'image'
        }
    }
    const clearPreview = () => {
        previewUrl.value = ''
        previewType.value = 'image'
    }

    // 发布或保存修改
    const savePost = () => {
        if (!inputContent.value) return alert("内容不能为空")

        if (isEditing.value) {
            // === 修改模式 ===
            const post = postList.value.find(p => p.id === editingId.value)
            if (post) {
                post.content = inputContent.value
                post.tag = inputTag.value
                // 如果重新传了图/视频，就更新，否则保持原样
                if (previewUrl.value) {
                    post.mediaUrl = previewUrl.value
                    post.mediaType = previewType.value
                }
            }
            alert("修改成功！")
            cancelEdit()
        } else {
            // === 新增模式 ===
            const newPost = {
                id: Date.now(),
                author: loginForm.value.username,
                content: inputContent.value,
                tag: inputTag.value || '#日常',
                time: new Date().toLocaleDateString(), // 获取当前日期
                mediaUrl: previewUrl.value,
                mediaType: previewType.value,
                rating: 0,
                comments: [],
                tempComment: ''
            }
            postList.value.unshift(newPost)
        }

        // 重置表单
        clearForm()
    }

    // 进入编辑模式
    const editPost = (item) => {
        isEditing.value = true
        editingId.value = item.id
        inputContent.value = item.content
        inputTag.value = item.tag
        window.scrollTo({ top: 0, behavior: 'smooth' })
    }

    // 取消编辑
    const cancelEdit = () => {
        isEditing.value = false
        editingId.value = null
        clearForm()
    }

    const clearForm = () => {
        inputContent.value = ''
        inputTag.value = ''
        clearPreview()
    }

    // 删除
    const deletePost = (id) => {
        if (confirm("确定删除？")) {
            postList.value = postList.value.filter(p => p.id !== id)
        }
    }

    // 评分
    const ratePost = (item, star) => {
        item.rating = star
    }

    // 评论
    const addComment = (item) => {
        if (!item.tempComment) return
        item.comments.push({
            user: loginForm.value.username, // 默认用当前登录用户发评论
            text: item.tempComment
        })
        item.tempComment = ''
    }
</script>

<style>
    /* 样式部分 */
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
    }

        .login-box input {
            display: block;
            width: 200px;
            margin: 10px auto;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }

        .login-box button {
            padding: 10px 20px;
            background: #409eff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
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
    }

        .search-bar input {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 20px;
            text-align: center;
            box-sizing: border-box;
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
    /* 修改模式变黄色 */
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
</style>