# 后端 API 文档（草案）

Base URL: `/api`

认证方式：JWT Bearer Token。受保护接口需在请求头携带：
`Authorization: Bearer <access_token>`

## 认证 Auth
### POST /auth/register
注册用户。

请求 JSON：
```
{
  "username": "string",
  "password": "string"
}
```

响应 201：
```
{
  "message": "registered",
  "data": {
    "user": {
      "id": 1,
      "username": "alice",
      "role": "user",
      "avatar": null,
      "created_at": "2025-01-01T00:00:00"
    }
  }
}
```

### POST /auth/login
登录并获取 token。

请求 JSON：
```
{
  "username": "string",
  "password": "string"
}
```

响应 200：
```
{
  "message": "logged in",
  "data": {
    "access_token": "...",
    "user": {
      "id": 1,
      "username": "alice",
      "role": "user",
      "avatar": null,
      "created_at": "2025-01-01T00:00:00"
    }
  }
}
```

## 用户 Users
### GET /users/me
获取当前用户信息。（需 JWT）

响应 200：
```
{
  "message": "ok",
  "data": { "user": { ... } }
}
```

### PUT /users/me
更新当前用户信息。（需 JWT）

请求 JSON（字段可选）：
```
{
  "username": "string",
  "avatar": "string",
  "password": "string"
}
```

响应 200：
```
{
  "message": "updated",
  "data": { "user": { ... } }
}
```

## 帖子 Posts
### POST /upload
上传图片/视频文件。

请求：`multipart/form-data`
- `file`: 图片或视频文件

响应 200：
```
{
  "message": "ok",
  "data": {
    "url": "http://localhost:5001/uploads/xxx.jpg",
    "filename": "xxx.jpg",
    "type": "image"
  }
}
```

### POST /posts
创建帖子。（需 JWT）

请求 JSON：
```
{
  "content": "text",
  "visibility": "public",
  "tags": ["tag1", "tag2"],
  "media": [
    { "type": "image", "url": "/uploads/a.jpg", "thumbnail_url": "/uploads/a_small.jpg" }
  ]
}
```

响应 201：
```
{ "message": "created", "data": { "post": { ... } } }
```

### GET /posts
帖子列表（支持过滤）。

查询参数：
- `page`（默认 1）
- `per_page`（默认 10）
- `user_id`（可选）
- `tag`（可选）
- `start_date`（ISO8601）
- `end_date`（ISO8601）

响应 200：
```
{
  "message": "ok",
  "data": {
    "items": [ { ... } ],
    "page": 1,
    "per_page": 10,
    "total": 100
  }
}
```

### GET /posts/:id
按 ID 获取帖子。

响应 200：
```
{ "message": "ok", "data": { "post": { ... } } }
```

### PUT /posts/:id
更新帖子。（需 JWT，作者本人）

请求 JSON（字段可选）：
```
{
  "content": "text",
  "visibility": "public",
  "tags": ["tag1"],
  "media": [ { "type": "image", "url": "/uploads/a.jpg" } ]
}
```

响应 200：
```
{ "message": "updated", "data": { "post": { ... } } }
```

### DELETE /posts/:id
删除帖子。（需 JWT，作者本人）

响应 200：
```
{ "message": "deleted", "data": { "post_id": 1 } }
```

## 评论 Comments
### POST /posts/:id/comments
创建评论。（需 JWT）

请求 JSON：
```
{ "content": "nice!" }
```

响应 201：
```
{ "message": "created", "data": { "comment": { ... } } }
```

### GET /posts/:id/comments
评论列表。

查询参数：`page`, `per_page`

响应 200：
```
{ "message": "ok", "data": { "items": [ ... ], "page": 1, "per_page": 10, "total": 5 } }
```

## 评分 Ratings
### POST /posts/:id/ratings
创建或更新评分。（需 JWT）

请求 JSON：
```
{ "score": 1 }
```

响应 201：
```
{ "message": "saved", "data": { "rating": { ... } } }
```

## 管理员 Admin（需 JWT，role=admin）
### GET /admin/users
用户列表。

查询参数：`page`, `per_page`

### DELETE /admin/users/:id
删除用户。

### GET /admin/posts
帖子列表。

查询参数：`page`, `per_page`

### DELETE /admin/posts/:id
删除帖子。

### GET /admin/stats
基础统计数据。

响应 200：
```
{
  "message": "ok",
  "data": {
    "users": 0,
    "posts": 0,
    "comments": 0,
    "ratings": 0
  }
}
```

## 说明
- 所有响应格式统一为 `{ "message": "...", "data": { ... } }`。
- 时间字段为 ISO8601 字符串。
- 错误响应为 `{ "message": "..." }`，状态码可能为 400/401/403/404/409。
