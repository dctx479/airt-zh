# AIRT — AI 红队学院（中文版）

> 🇨🇳 **完全汉化版本** | 原项目：[0x4D31/airt](https://github.com/0x4D31/airt)

一门免费的开源课程，涵盖 AI 系统的攻击性安全测试 — 从 Prompt Injection 到供应链攻击。60+ 小时的内容，包含实践 Docker 实验室。

**本仓库特点**：
- ✅ 所有课程内容已翻译为中文（9 个模块，~22,000 行）
- ✅ 所有实验室文档和代码注释已汉化
- ✅ 包含中文版实验室压缩包（`airt-labs-zh.zip`）
- ✅ 保持代码功能完整，可直接运行

🌐 **在线课程**: 打开 `index.html` 即可在浏览器中查看完整课程

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
git clone https://github.com/dctx479/airt-zh.git
cd airt-zh/labs

# 启动任何实验室（例如 Lab 01）
cd lab01-foundations
docker compose up

# 访问实验室界面
open http://localhost:8888
```

**或者使用中文版压缩包**：
```bash
# 解压中文版实验室
unzip airt-labs-zh.zip
cd labs/lab01-foundations
docker compose up
```

### 前置条件

- [Docker](https://docs.docker.com/get-docker/) 和 Docker Compose
- 8 GB+ RAM（建议 Labs 07–08 使用 16 GB）
- ~20 GB 磁盘空间用于模型下载

## 许可证

内容许可证为 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)。代码和实验室文件许可证为 [MIT](LICENSE)。

## 致谢

- **原项目作者**: [0x4D31](https://github.com/0x4D31) - 感谢创建了这个优秀的 AI 安全课程
- **原项目地址**: https://github.com/0x4D31/airt
- **汉化说明**: 本仓库是原项目的完全中文化版本，所有用户界面文本、文档和代码注释均已翻译为中文

## 汉化详情

| 类别 | 文件数 | 说明 |
|------|--------|------|
| HTML 页面 | 9 | 所有课程模块页面 |
| Python 代码 | 19 | 实验室应用代码（注释和文档字符串） |
| Markdown 文档 | 11 | README 和实验室文档 |
| 配置文件 | 7 | YAML/Shell 脚本注释 |
| **总计** | **46** | **约 22,000 行翻译** |

**翻译原则**：
- ✅ 所有用户界面文本已翻译
- ✅ 代码逻辑完整保留
- ✅ 专业术语保持英文或中英对照
- ✅ 所有功能验证通过

---

使用 [Perplexity Computer](https://www.perplexity.ai/computer) 构建。
