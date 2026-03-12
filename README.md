# AIRT — AI 红队学院

一门免费的开源课程，涵盖 AI 系统的攻击性安全测试 — 从 Prompt Injection 到供应链攻击。60+ 小时的内容，包含实践 Docker 实验室。

🌐 **[查看课程 →](https://0x4d31.github.io/airt/)**

## 模块

| # | 模块 | 主题 |
|---|--------|--------|
| 1 | AI 红队基础 | MITRE ATLAS、OWASP LLM Top 10、威胁建模 |
| 2 | Prompt Injection 攻击 | 直接/间接注入、越狱、过滤器绕过 |
| 3 | RAG 利用与向量数据库攻击 | 知识库投毒、嵌入攻击 |
| 4 | 多代理系统利用 | 代理劫持、工具滥用、内存投毒 |
| 5 | AI 供应链与基础设施攻击 | 模型后门、pickle 利用、依赖攻击 |
| 6 | 模型提取与推理攻击 | 模型窃取、成员推理、侧信道 |
| 7 | 大规模自动化 AI 红队测试 | garak、PyRIT、promptfoo、CI/CD 集成 |
| 8 | 后渗透与影响分析 | 横向移动、报告、监管框架 |

## 实践实验室

每个模块都包含一个基于 Docker 的实验室环境。无需云 API 密钥 — 一切都通过 [Ollama](https://ollama.com/) 在本地运行。

### 快速开始

```bash
# 克隆仓库
git clone https://github.com/0x4d31/airt.git
cd airt/labs

# 启动任何实验室（例如 Lab 01）
cd lab01-foundations
docker compose up

# 访问实验室界面
open http://localhost:8888
```

### 前置条件

- [Docker](https://docs.docker.com/get-docker/) 和 Docker Compose
- 8 GB+ RAM（建议 Labs 07–08 使用 16 GB）
- ~20 GB 磁盘空间用于模型下载

## 许可证

内容许可证为 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). 代码和实验室文件许可证为 [MIT](LICENSE).

---

使用以下工具构建 [Perplexity Computer](https://www.perplexity.ai/computer).
