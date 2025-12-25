# 基于 Streamlit + Neo4j 的实时词云设计方案

## 1. 总体架构

将原有的 Node.js + Socket.IO 架构迁移为 Python 生态的 Streamlit + Neo4j 架构。

*   **前端 (展示层)**: Streamlit Web 应用
    *   负责接收学生输入。
    *   负责展示实时词云。
    *   利用 `streamlit-autorefresh` 实现前端的定时轮询更新（模拟实时性）。
*   **后端 (逻辑层)**: Streamlit Python 脚本
    *   处理业务逻辑。
    *   与数据库交互。
*   **数据库 (数据层)**: Neo4j 图数据库
    *   存储学生发送的关键词。
    *   利用图数据库特性，未来可扩展存储词与词之间的关联（如共现关系）。
*   **代码托管**: GitHub
    *   用于版本控制和协作。
    *   可直接连接 Streamlit Cloud 进行自动化部署。

## 2. 核心模块设计

### 2.1 数据存储 (Neo4j)

使用 Neo4j 存储关键词及其出现频率。

*   **节点 (Node)**: `Keyword`
    *   属性: `text` (内容), `count` (频次), `last_updated` (最后更新时间)
*   **Cypher 查询示例**:
    *   **插入/更新**:
        ```cypher
        MERGE (k:Keyword {text: $text})
        ON CREATE SET k.count = 1, k.last_updated = timestamp()
        ON MATCH SET k.count = k.count + 1, k.last_updated = timestamp()
        ```
    *   **查询**:
        ```cypher
        MATCH (k:Keyword)
        RETURN k.text as name, k.count as value
        ORDER BY k.count DESC
        LIMIT 100
        ```

### 2.2 前端交互 (Streamlit)

Streamlit 的运行机制是基于脚本重运行的，为了实现“多人实时”效果，需要引入自动刷新机制。

*   **输入区**:
    *   使用 `st.text_input` 或 `st.form` 接收学生输入。
    *   提交后调用 Neo4j 驱动写入数据。
*   **展示区**:
    *   **方案 A (推荐 - 保持动态效果)**: 使用 `streamlit-echarts` 或自定义 HTML 组件 (iframe) 嵌入类似 `ciyun.html` 的前端代码。Streamlit 将数据转换为 JSON 传递给组件。
    *   **方案 B (原生)**: 使用 Python `wordcloud` 库生成静态图片，通过 `st.image` 展示（刷新时图片会闪烁，体验稍差）。
*   **实时同步**:
    *   使用 `streamlit_autorefresh` 插件，每隔 2-5 秒自动刷新页面或特定组件，从 Neo4j 拉取最新数据。

## 3. 目录结构建议

```
project_root/
├── app.py              # Streamlit 主程序
├── db.py               # Neo4j 数据库连接工具类
├── requirements.txt    # Python 依赖 (streamlit, neo4j, streamlit-echarts, etc.)
├── .streamlit/
│   └── secrets.toml    # 数据库账号密码配置 (本地开发用)
└── README.md           # 项目说明
```

## 4. 迁移步骤

1.  **环境准备**: 安装 Python, Streamlit, Neo4j Driver。
2.  **数据库连接**: 编写 `db.py` 封装 Neo4j 的连接和查询。
3.  **界面开发**: 编写 `app.py`，实现输入框和提交逻辑。
4.  **词云集成**: 将 Neo4j 数据转换为词云组件需要的格式并渲染。
5.  **部署**: 推送到 GitHub，在 Streamlit Cloud 上连接仓库并配置 Secrets。

## 5. 优缺点分析

*   **优点**:
    *   **持久化**: 数据存储在 Neo4j，重启服务数据不丢失。
    *   **分析能力**: Neo4j 方便后续进行复杂的关联分析（如哪些词经常一起出现）。
    *   **开发效率**: Streamlit 极低代码量即可完成全栈开发。
*   **注意点**:
    *   **实时性**: Streamlit 的实时性不如 Socket.IO 原生 WebSocket 强，依赖轮询，会有秒级延迟。
    *   **并发**: Streamlit Cloud 免费版资源有限，大规模并发写入可能需要优化。
