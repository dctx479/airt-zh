/* app.js — AIRT AI 红队学院交互脚本 */

(function() {
  'use strict';

  /* ========================================
     主题切换
     ======================================== */
  const themeToggle = document.querySelector('[data-theme-toggle]');
  const root = document.documentElement;
  let theme = 'dark'; // 安全课程默认使用暗色主题
  let currentLang = 'zh';
  root.setAttribute('data-theme', theme);

  function updateToggleIcon() {
    if (!themeToggle) return;
    var label = currentLang === 'zh'
      ? ('切换到' + (theme === 'dark' ? '浅色' : '暗色') + '模式')
      : ('Switch to ' + (theme === 'dark' ? 'light' : 'dark') + ' mode');
    themeToggle.setAttribute('aria-label', label);
    themeToggle.innerHTML = theme === 'dark'
      ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
      : '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
  }

  updateToggleIcon();

  if (themeToggle) {
    themeToggle.addEventListener('click', function() {
      theme = theme === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', theme);
      updateToggleIcon();
    });
  }

  /* ========================================
     头部滚动行为
     ======================================== */
  const header = document.querySelector('.header');
  if (header) {
    let lastScrollY = 0;
    window.addEventListener('scroll', function() {
      const currentScrollY = window.scrollY;
      if (currentScrollY > 60) {
        header.classList.add('header--scrolled');
      } else {
        header.classList.remove('header--scrolled');
      }
      lastScrollY = currentScrollY;
    }, { passive: true });
  }

  /* ========================================
     移动端菜单
     ======================================== */
  const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
  const headerNav = document.querySelector('.header__nav');

  if (mobileMenuBtn && headerNav) {
    mobileMenuBtn.addEventListener('click', function() {
      const isOpen = headerNav.classList.toggle('open');
      mobileMenuBtn.setAttribute('aria-expanded', isOpen);
      mobileMenuBtn.innerHTML = isOpen
        ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>'
        : '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>';
    });

    // 点击链接时关闭移动端菜单
    headerNav.querySelectorAll('a').forEach(function(link) {
      link.addEventListener('click', function() {
        headerNav.classList.remove('open');
        mobileMenuBtn.setAttribute('aria-expanded', 'false');
        mobileMenuBtn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>';
      });
    });
  }

  /* ========================================
     导航链接平滑滚动
     ======================================== */
  document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    anchor.addEventListener('click', function(e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      const target = document.querySelector(targetId);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
        // 更新 URL 哈希但不跳转
        if (window.history && window.history.pushState) {
          window.history.pushState(null, null, targetId);
        }
      }
    });
  });

  /* ========================================
     活动导航追踪
     ======================================== */
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.header__nav a');

  function updateActiveNav() {
    const scrollY = window.scrollY + 120;
    let currentSection = '';

    sections.forEach(function(section) {
      const top = section.offsetTop;
      const height = section.offsetHeight;
      if (scrollY >= top && scrollY < top + height) {
        currentSection = section.getAttribute('id');
      }
    });

    navLinks.forEach(function(link) {
      link.classList.remove('active');
      if (link.getAttribute('href') === '#' + currentSection) {
        link.classList.add('active');
      }
    });
  }

  window.addEventListener('scroll', updateActiveNav, { passive: true });
  updateActiveNav();

  /* ========================================
     模块展开/折叠
     ======================================== */
  document.querySelectorAll('.module-card__header').forEach(function(headerBtn) {
    headerBtn.addEventListener('click', function(e) {
      // 如果点击的是"阅读模块"链接，则不切换
      if (e.target.closest('.module-card__read-link')) return;

      var card = this.closest('.module-card');
      var isOpen = card.classList.contains('is-open');

      // 切换此卡片
      card.classList.toggle('is-open');

      // 更新 aria 属性
      this.setAttribute('aria-expanded', !isOpen);
    });
  });

  /* ========================================
     终端打字动画
     ======================================== */
  function animateTerminal() {
    var lines = document.querySelectorAll('.terminal-line');
    lines.forEach(function(line, index) {
      line.style.animationDelay = (index * 0.4) + 's';
    });
  }

  // 仅在 hero 区域可见时播放动画
  var heroTerminal = document.querySelector('.hero__terminal');
  if (heroTerminal) {
    var observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          animateTerminal();
          observer.disconnect();
        }
      });
    }, { threshold: 0.3 });
    observer.observe(heroTerminal);
  }

  /* ========================================
     滚动显示回退方案
     （用于不支持滚动驱动动画的浏览器）
     ======================================== */
  if (!CSS.supports || !CSS.supports('animation-timeline', 'scroll()')) {
    var revealElements = document.querySelectorAll('.fade-in, .reveal-up');
    if (revealElements.length > 0) {
      var revealObserver = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
          if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.clipPath = 'none';
            revealObserver.unobserve(entry.target);
          }
        });
      }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

      revealElements.forEach(function(el) {
        el.style.opacity = '0';
        el.style.transition = 'opacity 0.6s cubic-bezier(0.16, 1, 0.3, 1), clip-path 0.6s cubic-bezier(0.16, 1, 0.3, 1)';
        revealObserver.observe(el);
      });
    }
  }

  /* ========================================
     国际化 (i18n) — 中英双语切换
     ======================================== */
  const translations = {
    zh: {
      page_title: 'AIRT — AI 红队学院 | 免费 AI 安全课程',
      skip_link: '跳转到内容',
      nav_home: '首页', nav_modules: '模块', nav_labs: '实验室',
      nav_tools: '工具', nav_about: '关于',
      hero_badge: '开源 · 永久免费',
      hero_title_1: 'AI 红队', hero_title_2: '学院',
      hero_subtitle: '掌握 AI 安全。破解 AI 系统。保护重要的东西。',
      hero_description: '一门免费的开源课程，涵盖 AI 系统的攻击性安全测试 — 从 Prompt Injection 到供应链攻击。60+ 小时的内容，包含实践 Docker 实验室。',
      hero_cta_start: '开始学习', hero_cta_download: '下载全部实验室',
      terminal_title: 'airt-lab ~ 终端',
      terminal_comment_1: '# 扫描 LLM 漏洞',
      terminal_output_1: '[*] 正在加载 12 个类别中的 47 个探针...',
      terminal_output_2: '[*] 正在测试提示注入向量...',
      terminal_output_3: '[!] 漏洞：直接提示注入 — 系统提示覆盖',
      terminal_output_4: '[!] 漏洞：编码绕过 — Base64 指令注入',
      terminal_comment_2: '# 启动多轮 Crescendo 攻击',
      terminal_output_5: '[*] 正在初始化 5 轮升级序列...',
      terminal_output_6: '[*] 第 3/5 轮：检测到上下文边界弱化',
      terminal_output_7: '[!] 第 5/5 轮：护栏绕过成功 — ASR: 78%',
      stats_modules: '模块', stats_hours: '小时', stats_labs: 'Docker 实验室', stats_free: '免费',
      overview_label: '// 课程概览', overview_title: '您将学到什么',
      overview_desc: '一套全面的实践课程，涵盖 AI 系统的攻击性安全测试 — LLM、RAG 管道、多智能体系统和 AI 基础设施。每个模块都包含基于 Docker 的实验室环境。',
      overview_prereq_title: '先决条件',
      overview_prereq_1: '对机器学习概念的基本理解',
      overview_prereq_2: '熟悉 Python 编程',
      overview_prereq_3: '命令行/终端经验',
      overview_prereq_4: 'Docker 基础知识（开始前安装 Docker Desktop）',
      overview_prereq_5: '对 AI 系统如何被利用的好奇心',
      overview_who_title: '这是为谁准备的',
      overview_who_1: '扩展到 AI/ML 的安全专业人员',
      overview_who_2: '想要构建更安全系统的 AI/ML 工程师',
      overview_who_3: '渗透测试人员将 AI 目标添加到其技能集中',
      overview_who_4: '研究对抗性机器学习的研究人员',
      overview_who_5: '任何对 AI 安全和保护充满热情的人',
      modules_label: '课程大纲', modules_title: '8 个模块，60+ 小时，全程实操',
      modules_desc: '每个模块都包含详细的主题、实践 Docker 实验室和精选参考资源。单击任何模块以展开其完整内容。',
      topics_heading: '涵盖主题', refs_heading: '参考资料', btn_download_lab: '下载实验室',
      m1_title: 'AI 红队基础', m1_read: '阅读模块 1 →',
      m1_desc: '学习像 AI 对手一样思考。探索 AI 红队测试与传统渗透测试的区别 — 概率性目标与确定性目标、新型攻击面以及不断演变的 AI 威胁态势。',
      m2_title: 'Prompt Injection 攻击', m2_read: '阅读模块 2 →',
      m2_desc: '掌握 LLM 应用程序中的第 1 大漏洞。学习直接和间接 Prompt Injection、越狱技术以及如何系统地绕过安全护栏。',
      m3_title: 'RAG 利用与向量数据库攻击', m3_read: '阅读模块 3 →',
      m3_desc: '破坏检索增强生成管道。投毒知识库、操纵检索机制、利用向量数据库漏洞，并从 RAG 系统中泄露敏感数据。',
      m4_title: '多智能体系统利用', m4_read: '阅读模块 4 →',
      m4_desc: '利用多智能体 AI 系统中的新兴漏洞。破坏智能体间通信、执行拜占庭攻击、操纵集体决策，并在智能体网络中级联传播故障。',
      m5_title: 'AI 供应链与基础设施攻击', m5_read: '阅读模块 5 →',
      m5_desc: '攻击 AI 供应链 — 从 Hugging Face 上的投毒模型到被入侵的训练管道。利用模型序列化漏洞、依赖项混淆和基础设施配置错误。',
      m6_title: '模型提取与推理攻击', m6_read: '阅读模块 6 →',
      m6_desc: '盗窃专有 AI 模型并提取私人训练数据。通过战略性查询、训练数据提取和对 LLM 部署的侧信道攻击执行模型提取。',
      m7_title: '大规模自动化 AI 红队', m7_read: '阅读模块 7 →',
      m7_desc: '通过自动化扩展你的 AI 红队测试。掌握开源工具 — garak、PyRIT 和 promptfoo — 运行全面的漏洞评估、集成到 CI/CD 管道并生成可操作的报告。',
      m8_title: '后渗透与影响分析', m8_read: '阅读模块 8 →',
      m8_desc: '将 AI 红队发现转化为现实影响。演示业务后果、构建利用链、编写可操作的报告并制定推动安全改进的补救策略。',
      m1_topics: [
        '什么是 AI 红队以及为什么重要',
        '传统红队 vs AI 红队：关键区别',
        'AI 攻击面：模型、API、训练数据、输出、基础设施',
        'MITRE ATLAS 框架：14 种战术、66 种 AI 对手行为技术',
        'NVIDIA AI 杀伤链：侦察 → 投毒 → 劫持 → 持久化 → 影响',
        'OWASP LLM 应用程序 Top 10（2025 版）',
        'NIST AI 100-2：对抗性 ML 分类法',
        'AI 系统的威胁建模',
        'AI 红队中的法律和伦理考虑',
        '设置你的 AI 红队实验室环境'
      ],
      m2_topics: [
        '直接 Prompt Injection：覆盖系统提示',
        '间接 Prompt Injection：投毒外部上下文',
        '越狱技术：DAN、角色扮演、上下文操纵',
        '基于编码的攻击：Base64、ROT13、莫尔斯码、Leetspeak、Unicode',
        '多轮攻击：Crescendo 和上下文累积',
        '策略傀儡和指令层次结构利用',
        '令牌级攻击和对抗后缀',
        '使用进化算法的自动化 Prompt Injection',
        '测量攻击成功率 (ASR)',
        '绕过护栏：字符注入、AML 规避方法',
        '测试护栏产品：Azure Prompt Shield、Meta Prompt Guard、NeMo',
        '防御分析：什么有效，什么无效'
      ],
      m3_topics: [
        'RAG 架构深入探讨：摄取、嵌入、检索、生成',
        'RAG 攻击面：每个组件都是目标',
        '知识库投毒：注入恶意文档',
        '通过检索上下文的间接 Prompt Injection',
        'HijackRAG：操纵检索机制（黑盒和白盒）',
        '向量数据库安全：3000+ 个暴露数据库问题',
        '嵌入反演攻击：从向量重建源数据',
        '向量数据库中的数据投毒',
        '成员和属性推断攻击',
        '语义欺骗：欺骗相似性搜索',
        '跨上下文信息冲突',
        'RAG 凭证收集 (MITRE ATLAS 技术)',
        '编排层利用：LangChain、LlamaIndex 漏洞',
        'CVE-2025-27135：RAGFlow SQL 注入案例研究',
        'Microsoft 365 Copilot 利用链：Prompt Injection + ASCII 走私'
      ],
      m4_topics: [
        '多智能体 AI 架构：智能体如何通信和协调',
        '智能体之间的信任关系及其利用',
        '通信干扰和对智能体的中间人攻击',
        '拜占庭攻击和智能体冒充',
        '新兴利用：用于集体操纵的 M-Spoiler 框架',
        '跨多智能体系统的越狱传播',
        '通过智能体工具使用进行远程代码执行 (RCE)',
        '对智能体长期内存的内存操纵攻击',
        '智能体对话中的线程注入',
        '权限过度的智能体操作和权限提升',
        '用于持久后门的智能体配置修改',
        '激活触发器发现和利用',
        'AI 智能体工具调用进行未授权操作',
        '用于智能体交互的零信任架构',
        'MITRE ATLAS 2025：14 种新的智能体特定攻击技术'
      ],
      m5_topics: [
        'AI 供应链：模型、数据集、框架、依赖项',
        '模型投毒：后门、睡眠智能体和特洛伊木马模型',
        '恶意模型序列化：pickle 利用和代码执行',
        '模型注册表上的域名抢注 (openai-official, chatgpt-api, tensorfllow)',
        '训练数据投毒：医疗 LLM 案例研究（$5 即可投毒）',
        '后门触发器和睡眠智能体模型（Anthropic 研究）',
        '微调攻击：通过适应破坏模型行为',
        '框架漏洞：LangChain、LlamaIndex、Haystack 利用',
        'AI 管道中的 API 密钥泄露和凭证泄漏',
        'ML 部署的容器和基础设施安全',
        '通过蒸馏和提取攻击进行模型盗窃',
        'AI 的 SBOM：软件和 ML 物料清单',
        '供应链攻击案例研究：3CX、NullBulge/Hugging Face',
        '检测和防止模型投毒',
        '安全模型来源和完整性验证'
      ],
      m6_topics: [
        '模型提取基础知识：通过 API 访问克隆模型',
        '基于查询的模型盗窃：策略和优化',
        '从语言模型提取训练数据',
        '成员推断：这些数据是否在训练集中？',
        '从模型输出进行属性推断',
        '对 LLM 的侧信道攻击：Whisper Leak 流量分析',
        '用于响应重建的令牌长度侧信道',
        '对高效推理的时序攻击（推测解码）',
        '缓存共享时序攻击 (InputSnatch)',
        'TPUXtract：提取神经网络超参数',
        '模型反演：从输出重建输入',
        '知识产权盗窃影响',
        '防御：速率限制、输出扰动、水印',
        '用于提取尝试的 API 监控',
        '差分隐私作为缓解措施'
      ],
      m7_topics: [
        '为什么手动测试还不够：自动化的必要性',
        'garak 深入探讨：生成器、探针、检测器和分析器',
        'PyRIT 架构：数据集、编排器、转换器、评分',
        'Promptfoo：声明式红队配置和 CI/CD 集成',
        '设计攻击数据集和种子提示',
        '攻击策略选择和配置',
        '自动评分和评估模型响应',
        '多轮攻击编排',
        '转换器链：编码、混淆和规避',
        'AI 安全基准测试：CVE Bench 和评估框架',
        'CI/CD 集成：在部署管道中进行红队测试',
        '生成可操作的安全报告',
        '用于特定领域测试的自定义探针开发',
        '比较和组合多个工具',
        '构建持续的 AI 安全测试计划'
      ],
      m8_topics: [
        '从漏洞到影响：像业务对手一样思考',
        '构建 AI 利用链：结合多个弱点',
        '通过 AI 系统的数据泄露',
        '通过 AI 智能体工具滥用进行权限提升',
        '通过 AI 基础设施的横向移动',
        'AI 系统中的持久化机制',
        '影响类别：机密性、完整性、可用性、安全性',
        'AI 漏洞的业务影响量化',
        'AI 事件响应：检测、遏制、恢复',
        '编写有效的 AI 红队报告',
        '针对 AI 漏洞调整的 CVSS 评分',
        'AI 的补救策略和深度防御',
        '向技术和非技术利益相关者传达发现',
        '构建 AI 安全改进路线图',
        '持续监控和重新测试'
      ],
      lab1_title: '实验室 1：设置你的 AI 红队实验室',
      lab1_desc: '部署完整的 AI 红队环境，包含本地 LLM（Ollama）、向量数据库和测试工具。包含一个易受攻击的聊天机器人应用程序作为你的第一个目标。',
      lab1_objectives: [
        '使用本地 LLM (Mistral 7B 或 Llama 3) 部署 Ollama',
        '设置 ChromaDB 向量数据库',
        '部署易受攻击的 AI 聊天机器人应用程序',
        '安装并配置 garak、PyRIT 和 promptfoo',
        '使用 garak 运行你的第一次自动漏洞扫描',
        '使用 MITRE ATLAS 分类法记录发现'
      ],
      lab2_title: '实验室 2：Prompt Injection 游乐场',
      lab2_desc: '攻击一系列逐渐加固的聊天机器人。从未受保护的模型开始，通过受保护的系统进行，并学习系统地发现绕过方法。',
      lab2_objectives: [
        '对未受保护的聊天机器人执行直接 Prompt Injection',
        '从"安全"应用程序提取系统提示',
        '使用编码技术绕过内容过滤器 (Base64、Unicode 相似字符)',
        '执行多轮 Crescendo 攻击',
        '使用 garak 自动化越狱发现',
        '测试并绕过基于 DeBERTa 的 Prompt Injection 分类器',
        '实现进化提示生成以找到新的绕过方法',
        '计算并报告不同攻击策略的 ASR'
      ],
      lab3_title: '实验室 3：破坏 RAG 系统',
      lab3_desc: '构建然后系统地破坏 RAG 应用程序。投毒其知识库、劫持检索、执行嵌入反演并通过 LLM 泄露数据。',
      lab3_objectives: [
        '使用 ChromaDB 和 LangChain 部署易受攻击的 RAG 应用程序',
        '用恶意文档投毒知识库',
        '通过投毒的检索上下文执行间接 Prompt Injection',
        '执行嵌入反演以从向量恢复源文本',
        '演示对向量数据库的成员推断',
        '利用语义欺骗操纵搜索结果',
        '链接 RAG 投毒与通过 LLM 输出的数据泄露',
        '测试未经身份验证的向量数据库访问',
        '识别并利用编排框架漏洞'
      ],
      lab4_title: '实验室 4：破坏多智能体系统',
      lab4_desc: '攻击多智能体客户服务系统，其中智能体协作处理请求。破坏一个智能体以影响其他智能体、提升权限并通过工具调用泄露数据。',
      lab4_objectives: [
        '映射多智能体系统架构和信任关系',
        '通过 Prompt Injection 执行智能体冒充',
        '演示从一个智能体到另一个智能体的越狱传播',
        '操纵智能体内存以创建持久后门',
        '利用智能体工具访问执行未授权操作',
        '通过智能体工具调用执行数据泄露',
        '发现和利用激活触发器',
        '测试智能体间通信完整性',
        '实现并测试零信任防御'
      ],
      lab5_title: '实验室 5：AI 供应链攻击模拟',
      lab5_desc: '模拟对 ML 管道的供应链攻击。创建后门模型、利用 pickle 反序列化、演示域名抢注并投毒训练数据以破坏模型行为。',
      lab5_objectives: [
        '创建具有隐藏后门触发器的模型',
        '演示用于代码执行的恶意 pickle 反序列化',
        '模拟对模型注册表的域名抢注攻击',
        '投毒训练数据以引入有针对性的误分类',
        '利用 ML 管道中的不安全 API 密钥存储',
        '通过 API 查询执行模型提取',
        '分析模型是否存在投毒或后门迹象',
        '生成并验证 ML-SBOM',
        '实现模型完整性验证检查'
      ],
      lab6_title: '实验室 6：模型盗窃与隐私攻击',
      lab6_desc: '通过战略性 API 查询提取专有模型的行为。执行成员推断、尝试训练数据提取并分析加密流量以查找信息泄露。',
      lab6_objectives: [
        '通过系统的 API 查询克隆目标模型的行为',
        '训练与目标预测匹配的代理模型',
        '执行成员推断以识别训练数据',
        '从 LLM 提取记忆的训练数据',
        '分析加密的 LLM 流量进行主题分类（Whisper Leak）',
        '演示简单分类器上的模型反演',
        '实现并测试速率限制防御',
        '评估输出扰动作为防御机制',
        '生成提取检测报告'
      ],
      lab7_title: '实验室 7：自动化红队管道',
      lab7_desc: '使用 garak、PyRIT 和 promptfoo 构建并运行自动化 AI 红队管道。测试多个模型、生成综合报告，并将安全测试集成到 CI/CD 工作流中。',
      lab7_objectives: [
        '使用多种探针类型配置并运行 garak 对本地 LLM',
        '使用自定义数据集和转换器构建 PyRIT 编排器',
        '使用多个攻击向量创建 promptfoo 红队配置',
        '比较不同模型的漏洞结果',
        '使用 PyRIT 实现多轮攻击自动化',
        '为特定领域测试构建自定义 garak 探针',
        '使用 promptfoo 设置 CI/CD 集成',
        '生成并分析综合安全评估报告',
        '创建仪表板以跟踪 AI 安全态势'
      ],
      lab8_title: '实验室 8：完整的 AI 红队参与',
      lab8_desc: '对现实的 AI 驱动企业应用程序进行完整的 AI 红队参与。执行侦察、链接多个利用、演示业务影响并交付专业报告。',
      lab8_objectives: [
        '对目标 AI 应用程序执行全面侦察',
        '识别并记录所有攻击面',
        '链接 Prompt Injection + RAG 投毒 + 数据泄露',
        '演示通过智能体工具滥用进行权限提升',
        '在 AI 系统中建立持久性',
        '量化发现的漏洞的业务影响',
        '使用 CVSS 分数编写专业的 AI 红队报告',
        '按风险优先级呈现补救建议',
        '制定 30/60/90 天安全改进计划'
      ],
      m1_refs: ['MITRE ATLAS', 'OWASP Top 10 for LLM', 'NIST AI 100-2', 'NVIDIA AI 杀伤链', 'Microsoft AI 红队', 'garak LLM 扫描器', 'Microsoft 的 PyRIT', 'Promptfoo'],
      m2_refs: ['OWASP LLM01：Prompt Injection', '绕过 LLM 护栏 - Mindgard', '对 LLM 的自适应攻击 - Keysight', '使用演变提示的 LLM 红队', 'Prompt Injection - Obsidian Security', 'PyRIT 攻击策略', 'Promptfoo 红队指南'],
      m3_refs: ['HijackRAG 论文', 'RAG 数据投毒 - Promptfoo', '安全 RAG 系统 2025', '向量数据库威胁 - Pure Storage', 'LIAR 攻击框架', 'RAG 安全风险 - Fortanix', '企业 AI 安全框架'],
      m4_refs: ['多智能体利用 - Galileo AI', 'AI 智能体漏洞 - WitnessAI', '智能体 AI 安全 - CSO Online', 'MITRE ATLAS 智能体技术', 'MS-Agent 框架漏洞', 'AWS 多智能体渗透测试'],
      m5_refs: ['AI 供应链指南 - Hacker News', 'OWASP LLM04', '模型投毒 - LastPass', '数据投毒 - Cloudflare', '数据投毒类型 - Lasso', 'OWASP LLM Top 10'],
      m6_refs: ['Whisper Leak 侧信道', 'TPUXtract 侧信道 - Keysight', 'NIST AML 分类法', 'AI 红队 - Obsidian', 'MITRE ATLAS 模型盗窃'],
      m7_refs: ['garak GitHub', 'garak 文档', 'PyRIT GitHub', 'PyRIT 教程视频', 'Promptfoo 红队文档', 'Promptfoo GitHub', 'Databricks 上的 garak', 'AI 红队工具 - CSET'],
      m8_refs: ['AI 红队 - Palo Alto', '关键基础设施的 AI 红队 - DNV', 'AI 影响评估 - Schellman', 'Microsoft AI 红队课程', 'MITRE ATLAS', 'NIST AI 风险管理'],
      tools_label: '工具与资源', tools_title: '开源工具库',
      tools_desc: '整个课程中使用的三个行业领先工具，用于自动化 AI 漏洞发现和红队。',
      garak_org: '由 NVIDIA 开发',
      garak_desc: 'LLM 漏洞扫描器，包含 12 个类别中的 47+ 个探针。自动检测 Prompt Injection、数据泄露、毒性、幻觉等。',
      link_website: '官网',
      pyrit_org: '由 Microsoft 开发',
      pyrit_desc: '用于生成式 AI 的 Python 风险识别工具。多轮攻击编排、用于规避的转换器链、自动评分和综合报告。',
      promptfoo_org: '开源',
      promptfoo_desc: 'LLM 红队和评估框架。声明式 YAML 配置、CI/CD 集成、跨模型的比较测试和自动漏洞报告。',
      framework_nvidia: 'NVIDIA AI 杀伤链',
      frameworks_heading: '参考框架',
      quickstart_label: '快速开始',
      quickstart_title: '3 条命令完成设置',
      quickstart_desc: '每个实验室都通过 Docker 在本地运行。克隆存储库、选择实验室并开始破解。',
      code_block_terminal: '终端',
      code_comment_1: '# 下载并解压实验室',
      code_comment_2: '# 启动任意实验室（例如实验室 01 - 基础）',
      code_comment_3: '# 访问实验室界面',
      code_comment_4: '# 使用 garak 运行漏洞扫描',
      code_comment_5: '# 启动 PyRIT 编排器',
      about_label: '关于 AIRT',
      about_title: '社区驱动的 AI 安全教育',
      about_p1: 'AI 红队学院是一个免费的开源教育资源，旨在使 AI 安全知识民主化。我们相信理解攻击性技术对于构建强大的 AI 防御至关重要。',
      about_p2: '本课程涵盖与商业 AI 红队认证类似的内容 — 但对所有人完全免费开放。无论你是经验丰富的渗透测试人员、AI 研究人员还是对安全感兴趣的开发人员，AIRT 都能提供你所需的实践经验。',
      about_p3: '为安全专业人员、研究人员和任何对 AI 安全充满热情的人构建。所有实验室都通过 Docker 在本地运行，不需要云 API 密钥或外部服务。你的测试环境完全在你的控制下。',
      about_p4: '课程涵盖 8 个模块中的 60-80 小时内容，从基础概念到完整的红队参与。每个模块都包括理论和带有真实攻击模拟的实践 Docker 实验室。',
      about_link_download_title: '下载全部实验室 (ZIP)',
      about_link_download_desc: '8 个准备就绪的基于 Docker 的实验室环境',
      about_link_issues_title: '报告问题',
      about_link_issues_desc: '发现了错误或有建议？请告诉我们',
      about_link_contribute_title: '贡献',
      about_link_contribute_desc: '添加模块、改进实验室、修复文档',
      about_link_license_title: '许可证',
      about_link_license_desc: '内容采用 CC BY-SA 4.0，代码采用 MIT',
      footer_brand: 'AIRT 学院',
      footer_copyright: '内容：CC BY-SA 4.0 · 代码：MIT 许可证 · 2025 AI 红队学院',
      footer_attribution: '使用 Perplexity Computer 创建'
    },
    en: {
      page_title: 'AIRT — AI Red Team Academy | Free AI Security Course',
      skip_link: 'Skip to content',
      nav_home: 'Home', nav_modules: 'Modules', nav_labs: 'Labs',
      nav_tools: 'Tools', nav_about: 'About',
      hero_badge: 'Open Source · Free Forever',
      hero_title_1: 'AI Red Team', hero_title_2: 'Academy',
      hero_subtitle: 'Master AI Security. Break AI Systems. Defend What Matters.',
      hero_description: 'A free, open-source course covering offensive security testing of AI systems — from prompt injection to supply chain attacks. 60+ hours of content with hands-on Docker labs.',
      hero_cta_start: 'Start Learning', hero_cta_download: 'Download All Labs',
      terminal_title: 'airt-lab ~ terminal',
      terminal_comment_1: '# Scan for LLM vulnerabilities',
      terminal_output_1: '[*] Loading 47 probes across 12 categories...',
      terminal_output_2: '[*] Testing prompt injection vectors...',
      terminal_output_3: '[!] Vuln: Direct prompt injection — system prompt override',
      terminal_output_4: '[!] Vuln: Encoding bypass — Base64 instruction injection',
      terminal_comment_2: '# Launch multi-turn Crescendo attack',
      terminal_output_5: '[*] Initializing 5-round escalation sequence...',
      terminal_output_6: '[*] Round 3/5: Context boundary weakening detected',
      terminal_output_7: '[!] Round 5/5: Guardrail bypass successful — ASR: 78%',
      stats_modules: 'Modules', stats_hours: 'Hours', stats_labs: 'Docker Labs', stats_free: 'Free',
      overview_label: '// Course Overview', overview_title: 'What You\'ll Learn',
      overview_desc: 'A comprehensive hands-on curriculum covering offensive security testing of AI systems — LLMs, RAG pipelines, multi-agent systems, and AI infrastructure. Every module includes a Docker-based lab environment.',
      overview_prereq_title: 'Prerequisites',
      overview_prereq_1: 'Basic understanding of machine learning concepts',
      overview_prereq_2: 'Familiarity with Python programming',
      overview_prereq_3: 'Command-line / terminal experience',
      overview_prereq_4: 'Basic Docker knowledge (install Docker Desktop before starting)',
      overview_prereq_5: 'Curiosity about how AI systems can be exploited',
      overview_who_title: 'Who This Is For',
      overview_who_1: 'Security professionals expanding into AI/ML',
      overview_who_2: 'AI/ML engineers who want to build more secure systems',
      overview_who_3: 'Penetration testers adding AI targets to their skill set',
      overview_who_4: 'Researchers studying adversarial machine learning',
      overview_who_5: 'Anyone passionate about AI safety and security',
      modules_label: 'Curriculum', modules_title: '8 Modules, 60+ Hours, Fully Hands-On',
      modules_desc: 'Each module includes detailed topics, hands-on Docker labs, and curated references. Click any module to expand its full content.',
      topics_heading: 'Topics Covered', refs_heading: 'References', btn_download_lab: 'Download Lab',
      m1_title: 'AI Red Teaming Fundamentals', m1_read: 'Read Module 1 →',
      m1_desc: 'Learn to think like an AI adversary. Explore how AI red teaming differs from traditional pentesting — probabilistic vs. deterministic targets, novel attack surfaces, and the evolving AI threat landscape.',
      m2_title: 'Prompt Injection Attacks', m2_read: 'Read Module 2 →',
      m2_desc: 'Master the #1 vulnerability in LLM applications. Learn direct and indirect prompt injection, jailbreaking techniques, and how to systematically bypass safety guardrails.',
      m3_title: 'RAG Exploitation & Vector DB Attacks', m3_read: 'Read Module 3 →',
      m3_desc: 'Compromise retrieval-augmented generation pipelines. Poison knowledge bases, manipulate retrieval mechanisms, exploit vector database vulnerabilities, and exfiltrate sensitive data from RAG systems.',
      m4_title: 'Multi-Agent System Exploitation', m4_read: 'Read Module 4 →',
      m4_desc: 'Exploit emerging vulnerabilities in multi-agent AI systems. Compromise inter-agent communication, execute Byzantine attacks, manipulate collective decision-making, and cascade failures through agent networks.',
      m5_title: 'AI Supply Chain & Infrastructure Attacks', m5_read: 'Read Module 5 →',
      m5_desc: 'Attack the AI supply chain — from poisoned models on Hugging Face to compromised training pipelines. Exploit model serialization vulnerabilities, dependency confusion, and infrastructure misconfigurations.',
      m6_title: 'Model Extraction & Inference Attacks', m6_read: 'Read Module 6 →',
      m6_desc: 'Steal proprietary AI models and extract private training data. Perform model extraction through strategic querying, training data extraction, and side-channel attacks against LLM deployments.',
      m7_title: 'Automated AI Red Teaming at Scale', m7_read: 'Read Module 7 →',
      m7_desc: 'Scale your AI red teaming with automation. Master open-source tools — garak, PyRIT, and promptfoo — to run comprehensive vulnerability assessments, integrate into CI/CD pipelines, and generate actionable reports.',
      m8_title: 'Post-Exploitation & Impact Analysis', m8_read: 'Read Module 8 →',
      m8_desc: 'Turn AI red team findings into real-world impact. Demonstrate business consequences, build exploit chains, write actionable reports, and develop remediation strategies that drive security improvements.',
      m1_topics: [
        'What is AI red teaming and why it matters',
        'Traditional red teaming vs. AI red teaming: key differences',
        'AI attack surfaces: models, APIs, training data, outputs, infrastructure',
        'MITRE ATLAS framework: 14 tactics, 66 AI adversary behavior techniques',
        'NVIDIA AI Kill Chain: Recon → Poison → Hijack → Persist → Impact',
        'OWASP Top 10 for LLM Applications (2025 Edition)',
        'NIST AI 100-2: Adversarial ML taxonomy',
        'Threat modeling for AI systems',
        'Legal and ethical considerations in AI red teaming',
        'Setting up your AI red team lab environment'
      ],
      m2_topics: [
        'Direct Prompt Injection: overriding system prompts',
        'Indirect Prompt Injection: poisoning external context',
        'Jailbreaking techniques: DAN, role-playing, context manipulation',
        'Encoding-based attacks: Base64, ROT13, Morse code, Leetspeak, Unicode',
        'Multi-turn attacks: Crescendo and context accumulation',
        'Policy puppetry and instruction hierarchy exploitation',
        'Token-level attacks and adversarial suffixes',
        'Automated Prompt Injection using evolutionary algorithms',
        'Measuring Attack Success Rate (ASR)',
        'Bypassing guardrails: character injection, AML evasion methods',
        'Testing guardrail products: Azure Prompt Shield, Meta Prompt Guard, NeMo',
        'Defense analysis: what works and what doesn\'t'
      ],
      m3_topics: [
        'RAG architecture deep dive: ingestion, embedding, retrieval, generation',
        'RAG attack surfaces: every component is a target',
        'Knowledge base poisoning: injecting malicious documents',
        'Indirect Prompt Injection through retrieval context',
        'HijackRAG: manipulating retrieval mechanisms (black-box and white-box)',
        'Vector database security: 3000+ exposed database issue',
        'Embedding inversion attacks: reconstructing source data from vectors',
        'Data poisoning in vector databases',
        'Membership and attribute inference attacks',
        'Semantic deception: fooling similarity search',
        'Cross-context information conflicts',
        'RAG credential harvesting (MITRE ATLAS technique)',
        'Orchestration layer exploitation: LangChain, LlamaIndex vulnerabilities',
        'CVE-2025-27135: RAGFlow SQL injection case study',
        'Microsoft 365 Copilot exploit chain: Prompt Injection + ASCII smuggling'
      ],
      m4_topics: [
        'Multi-agent AI architectures: how agents communicate and coordinate',
        'Trust relationships between agents and their exploitation',
        'Communication tampering and man-in-the-middle attacks on agents',
        'Byzantine attacks and agent impersonation',
        'Emerging exploits: M-Spoiler framework for collective manipulation',
        'Jailbreak propagation across multi-agent systems',
        'Remote code execution (RCE) through agent tool usage',
        'Memory manipulation attacks against agent long-term memory',
        'Thread injection in agent conversations',
        'Over-privileged agent operations and privilege escalation',
        'Agent configuration modification for persistent backdoors',
        'Activation trigger discovery and exploitation',
        'AI agent tool calls for unauthorized operations',
        'Zero-trust architecture for agent interactions',
        'MITRE ATLAS 2025: 14 new agent-specific attack techniques'
      ],
      m5_topics: [
        'AI supply chain: models, datasets, frameworks, dependencies',
        'Model poisoning: backdoors, sleeper agents, and trojan models',
        'Malicious model serialization: pickle exploits and code execution',
        'Typosquatting on model registries (openai-official, chatgpt-api, tensorfllow)',
        'Training data poisoning: medical LLM case study ($5 to poison)',
        'Backdoor triggers and sleeper agent models (Anthropic research)',
        'Fine-tuning attacks: corrupting model behavior through adaptation',
        'Framework vulnerabilities: LangChain, LlamaIndex, Haystack exploits',
        'API key leakage and credential exposure in AI pipelines',
        'Container and infrastructure security for ML deployments',
        'Model theft through distillation and extraction attacks',
        'SBOM for AI: software and ML bills of materials',
        'Supply chain attack case studies: 3CX, NullBulge/Hugging Face',
        'Detecting and preventing model poisoning',
        'Secure model provenance and integrity verification'
      ],
      m6_topics: [
        'Model extraction fundamentals: cloning models through API access',
        'Query-based model theft: strategies and optimization',
        'Extracting training data from language models',
        'Membership inference: was this data in the training set?',
        'Attribute inference from model outputs',
        'Side-channel attacks on LLMs: Whisper Leak traffic analysis',
        'Token-length side channels for response reconstruction',
        'Timing attacks against efficient inference (speculative decoding)',
        'Cache-sharing timing attacks (InputSnatch)',
        'TPUXtract: extracting neural network hyperparameters',
        'Model inversion: reconstructing inputs from outputs',
        'Intellectual property theft implications',
        'Defenses: rate limiting, output perturbation, watermarking',
        'API monitoring for extraction attempts',
        'Differential privacy as a mitigation'
      ],
      m7_topics: [
        'Why manual testing isn\'t enough: the case for automation',
        'garak deep dive: generators, probes, detectors, and analyzers',
        'PyRIT architecture: datasets, orchestrators, transformers, scoring',
        'Promptfoo: declarative red teaming config and CI/CD integration',
        'Designing attack datasets and seed prompts',
        'Attack strategy selection and configuration',
        'Automated scoring and evaluating model responses',
        'Multi-turn attack orchestration',
        'Transformer chains: encoding, obfuscation, and evasion',
        'AI security benchmarking: CVE Bench and evaluation frameworks',
        'CI/CD integration: red teaming in deployment pipelines',
        'Generating actionable security reports',
        'Custom probe development for domain-specific testing',
        'Comparing and combining multiple tools',
        'Building a continuous AI security testing program'
      ],
      m8_topics: [
        'From vulnerabilities to impact: thinking like a business adversary',
        'Building AI exploit chains: combining multiple weaknesses',
        'Data exfiltration through AI systems',
        'Privilege escalation through AI agent tool abuse',
        'Lateral movement through AI infrastructure',
        'Persistence mechanisms in AI systems',
        'Impact categories: confidentiality, integrity, availability, safety',
        'Business impact quantification of AI vulnerabilities',
        'AI incident response: detection, containment, recovery',
        'Writing effective AI red team reports',
        'CVSS scoring adapted for AI vulnerabilities',
        'Remediation strategies and defense-in-depth for AI',
        'Communicating findings to technical and non-technical stakeholders',
        'Building AI security improvement roadmaps',
        'Continuous monitoring and re-testing'
      ],
      lab1_title: 'Lab 1: Set Up Your AI Red Team Lab',
      lab1_desc: 'Deploy a complete AI red teaming environment with a local LLM (Ollama), vector database, and testing tools. Includes a vulnerable chatbot application as your first target.',
      lab1_objectives: [
        'Deploy Ollama with a local LLM (Mistral 7B or Llama 3)',
        'Set up ChromaDB vector database',
        'Deploy a vulnerable AI chatbot application',
        'Install and configure garak, PyRIT, and promptfoo',
        'Run your first automated vulnerability scan with garak',
        'Document findings using MITRE ATLAS taxonomy'
      ],
      lab2_title: 'Lab 2: Prompt Injection Playground',
      lab2_desc: 'Attack a series of progressively hardened chatbots. Start with an unprotected model, work through protected systems, and learn to systematically discover bypass techniques.',
      lab2_objectives: [
        'Execute direct Prompt Injection against unprotected chatbots',
        'Extract system prompts from "secure" applications',
        'Bypass content filters using encoding techniques (Base64, Unicode lookalikes)',
        'Execute multi-turn Crescendo attacks',
        'Automate jailbreak discovery with garak',
        'Test and bypass DeBERTa-based Prompt Injection classifiers',
        'Implement evolutionary prompt generation to find new bypasses',
        'Calculate and report ASR for different attack strategies'
      ],
      lab3_title: 'Lab 3: Compromising a RAG System',
      lab3_desc: 'Build and then systematically compromise a RAG application. Poison its knowledge base, hijack retrieval, perform embedding inversion, and exfiltrate data through the LLM.',
      lab3_objectives: [
        'Deploy a vulnerable RAG application with ChromaDB and LangChain',
        'Poison the knowledge base with malicious documents',
        'Execute indirect Prompt Injection through poisoned retrieval context',
        'Perform embedding inversion to recover source text from vectors',
        'Demonstrate membership inference against vector databases',
        'Manipulate search results using semantic deception',
        'Chain RAG poisoning with data exfiltration through LLM output',
        'Test unauthenticated vector database access',
        'Identify and exploit orchestration framework vulnerabilities'
      ],
      lab4_title: 'Lab 4: Breaking Multi-Agent Systems',
      lab4_desc: 'Attack a multi-agent customer service system where agents collaborate to handle requests. Compromise one agent to influence others, escalate privileges, and exfiltrate data through tool calls.',
      lab4_objectives: [
        'Map multi-agent system architecture and trust relationships',
        'Execute agent impersonation through Prompt Injection',
        'Demonstrate jailbreak propagation from one agent to another',
        'Manipulate agent memory to create persistent backdoors',
        'Exploit agent tool access to execute unauthorized operations',
        'Perform data exfiltration through agent tool calls',
        'Discover and exploit activation triggers',
        'Test inter-agent communication integrity',
        'Implement and test zero-trust defenses'
      ],
      lab5_title: 'Lab 5: AI Supply Chain Attack Simulation',
      lab5_desc: 'Simulate a supply chain attack against an ML pipeline. Create backdoored models, exploit pickle deserialization, demonstrate typosquatting, and poison training data to corrupt model behavior.',
      lab5_objectives: [
        'Create models with hidden backdoor triggers',
        'Demonstrate malicious pickle deserialization for code execution',
        'Simulate typosquatting attacks against model registries',
        'Poison training data to introduce targeted misclassifications',
        'Exploit insecure API key storage in ML pipelines',
        'Perform model extraction through API queries',
        'Analyze models for signs of poisoning or backdoors',
        'Generate and verify ML-SBOM',
        'Implement model integrity verification checks'
      ],
      lab6_title: 'Lab 6: Model Theft & Privacy Attacks',
      lab6_desc: 'Extract a proprietary model\'s behavior through strategic API queries. Perform membership inference, attempt training data extraction, and analyze encrypted traffic for information leakage.',
      lab6_objectives: [
        'Clone target model behavior through systematic API queries',
        'Train a surrogate model matching target predictions',
        'Perform membership inference to identify training data',
        'Extract memorized training data from LLMs',
        'Analyze encrypted LLM traffic for topic classification (Whisper Leak)',
        'Demonstrate model inversion on a simple classifier',
        'Implement and test rate-limiting defenses',
        'Evaluate output perturbation as a defense mechanism',
        'Generate extraction detection reports'
      ],
      lab7_title: 'Lab 7: Automated Red Teaming Pipeline',
      lab7_desc: 'Build and run an automated AI red teaming pipeline using garak, PyRIT, and promptfoo. Test multiple models, generate comprehensive reports, and integrate security testing into CI/CD workflows.',
      lab7_objectives: [
        'Configure and run garak with multiple probe types against a local LLM',
        'Build a PyRIT orchestrator with custom datasets and transformers',
        'Create a promptfoo red team config with multiple attack vectors',
        'Compare vulnerability results across different models',
        'Implement multi-turn attack automation with PyRIT',
        'Build custom garak probes for domain-specific testing',
        'Set up CI/CD integration with promptfoo',
        'Generate and analyze comprehensive security assessment reports',
        'Create a dashboard to track AI security posture'
      ],
      lab8_title: 'Lab 8: Full AI Red Team Engagement',
      lab8_desc: 'Conduct a complete AI red team engagement against a realistic AI-powered enterprise application. Perform reconnaissance, chain multiple exploits, demonstrate business impact, and deliver a professional report.',
      lab8_objectives: [
        'Perform comprehensive reconnaissance against target AI application',
        'Identify and document all attack surfaces',
        'Chain Prompt Injection + RAG poisoning + data exfiltration',
        'Demonstrate privilege escalation through agent tool abuse',
        'Establish persistence in AI systems',
        'Quantify business impact of discovered vulnerabilities',
        'Write a professional AI red team report with CVSS scores',
        'Present remediation recommendations prioritized by risk',
        'Develop a 30/60/90-day security improvement plan'
      ],
      m1_refs: ['MITRE ATLAS', 'OWASP Top 10 for LLM', 'NIST AI 100-2', 'NVIDIA AI Kill Chain', 'Microsoft AI Red Teaming', 'garak LLM Scanner', 'Microsoft\'s PyRIT', 'Promptfoo'],
      m2_refs: ['OWASP LLM01: Prompt Injection', 'Bypassing LLM Guardrails - Mindgard', 'Adaptive Attacks on LLMs - Keysight', 'Red Teaming LLMs with Evolving Prompts', 'Prompt Injection - Obsidian Security', 'PyRIT Attack Strategies', 'Promptfoo Red Team Guide'],
      m3_refs: ['HijackRAG Paper', 'RAG Data Poisoning - Promptfoo', 'Secure RAG Systems 2025', 'Vector Database Threats - Pure Storage', 'LIAR Attack Framework', 'RAG Security Risks - Fortanix', 'Enterprise AI Security Framework'],
      m4_refs: ['Multi-Agent Exploits - Galileo AI', 'AI Agent Vulnerabilities - WitnessAI', 'Agentic AI Security - CSO Online', 'MITRE ATLAS Agent Techniques', 'MS-Agent Framework Vulnerability', 'AWS Multi-Agent Pentesting'],
      m5_refs: ['AI Supply Chain Guide - Hacker News', 'OWASP LLM04', 'Model Poisoning - LastPass', 'Data Poisoning - Cloudflare', 'Data Poisoning Types - Lasso', 'OWASP LLM Top 10'],
      m6_refs: ['Whisper Leak Side-Channel', 'TPUXtract Side-Channel - Keysight', 'NIST AML Taxonomy', 'AI Red Teaming - Obsidian', 'MITRE ATLAS Model Theft'],
      m7_refs: ['garak GitHub', 'garak Documentation', 'PyRIT GitHub', 'PyRIT Tutorial Video', 'Promptfoo Red Team Docs', 'Promptfoo GitHub', 'garak on Databricks', 'AI Red Teaming Tools - CSET'],
      m8_refs: ['AI Red Teaming - Palo Alto', 'AI Red Teaming for Critical Infrastructure - DNV', 'AI Impact Assessment - Schellman', 'Microsoft AI Red Teaming Course', 'MITRE ATLAS', 'NIST AI Risk Management'],
      tools_label: 'Tools & Resources', tools_title: 'Open-Source Toolkit',
      tools_desc: 'Three industry-leading tools used throughout the course for automated AI vulnerability discovery and red teaming.',
      garak_org: 'by NVIDIA',
      garak_desc: 'LLM vulnerability scanner with 47+ probes across 12 categories. Automatically detects prompt injection, data leakage, toxicity, hallucination, and more.',
      link_website: 'Website',
      pyrit_org: 'by Microsoft',
      pyrit_desc: 'Python Risk Identification Tool for generative AI. Multi-turn attack orchestration, transformer chains for evasion, automated scoring, and comprehensive reporting.',
      promptfoo_org: 'Open Source',
      promptfoo_desc: 'LLM red teaming and evaluation framework. Declarative YAML config, CI/CD integration, comparative testing across models, and automated vulnerability reporting.',
      framework_nvidia: 'NVIDIA AI Kill Chain',
      frameworks_heading: 'Reference Frameworks',
      quickstart_label: 'Quick Start',
      quickstart_title: '3 Commands to Get Started',
      quickstart_desc: 'Every lab runs locally via Docker. Clone the repo, pick a lab, and start hacking.',
      code_block_terminal: 'Terminal',
      code_comment_1: '# Download and unzip labs',
      code_comment_2: '# Start any lab (e.g., Lab 01 — Foundations)',
      code_comment_3: '# Access the lab interface',
      code_comment_4: '# Run a vulnerability scan with garak',
      code_comment_5: '# Start the PyRIT orchestrator',
      about_label: 'About AIRT',
      about_title: 'Community-Driven AI Security Education',
      about_p1: 'AI Red Team Academy is a free, open-source educational resource designed to democratize AI security knowledge. We believe understanding offensive techniques is essential for building robust AI defenses.',
      about_p2: 'This course covers content similar to commercial AI red teaming certifications — but completely free and open to everyone. Whether you\'re an experienced penetration tester, AI researcher, or developer interested in security, AIRT provides the hands-on experience you need.',
      about_p3: 'Built for security professionals, researchers, and anyone passionate about AI safety. All labs run locally via Docker — no cloud API keys or external services required. Your testing environment is entirely under your control.',
      about_p4: 'The curriculum covers 60–80 hours of content across 8 modules, from foundational concepts to full red team engagements. Each module includes theory and hands-on Docker labs with real attack simulations.',
      about_link_download_title: 'Download All Labs (ZIP)',
      about_link_download_desc: '8 Docker-based lab environments, ready to run',
      about_link_issues_title: 'Report an Issue',
      about_link_issues_desc: 'Found a bug or have a suggestion? Let us know',
      about_link_contribute_title: 'Contribute',
      about_link_contribute_desc: 'Add modules, improve labs, fix documentation',
      about_link_license_title: 'License',
      about_link_license_desc: 'Content under CC BY-SA 4.0, code under MIT',
      footer_brand: 'AIRT Academy',
      footer_copyright: 'Content: CC BY-SA 4.0 · Code: MIT License · 2025 AI Red Team Academy',
      footer_attribution: 'Built with Perplexity Computer'
    }
  };

  function setLanguage(lang) {
    currentLang = lang;
    root.setAttribute('data-lang', lang);
    document.documentElement.setAttribute('lang', lang === 'zh' ? 'zh-CN' : 'en');

    var t = translations[lang];
    if (!t) return;

    // 1. Regular data-i18n text elements
    document.querySelectorAll('[data-i18n]').forEach(function(el) {
      var key = el.getAttribute('data-i18n');
      if (t[key]) {
        el.textContent = t[key];
      }
    });

    // 2. List translations (data-i18n-list)
    document.querySelectorAll('[data-i18n-list]').forEach(function(ul) {
      var key = ul.getAttribute('data-i18n-list');
      var items = t[key];
      if (!items) return;
      var lis = ul.querySelectorAll('li');
      items.forEach(function(text, i) {
        if (!lis[i]) return;
        // For refs-list: preserve <a> structure and SVG icon
        var a = lis[i].querySelector('a');
        if (a) {
          // Replace only the first text node inside <a>, keep SVG
          for (var j = 0; j < a.childNodes.length; j++) {
            if (a.childNodes[j].nodeType === 3 && a.childNodes[j].textContent.trim()) {
              a.childNodes[j].textContent = text + ' ';
              break;
            }
          }
        } else {
          lis[i].textContent = text;
        }
      });
    });

    // 3. Update page title
    if (t.page_title) {
      document.title = t.page_title;
    }

    // 4. Update theme toggle aria-label
    updateToggleIcon();

    // 5. Language toggle visual state
    var zhSpan = document.querySelector('.lang-toggle__zh');
    var enSpan = document.querySelector('.lang-toggle__en');
    if (zhSpan && enSpan) {
      zhSpan.style.opacity = lang === 'zh' ? '1' : '0.5';
      zhSpan.style.fontWeight = lang === 'zh' ? '600' : '400';
      enSpan.style.opacity = lang === 'en' ? '1' : '0.5';
      enSpan.style.fontWeight = lang === 'en' ? '600' : '400';
    }

    localStorage.setItem('airt-lang', lang);
  }

  var langToggleBtn = document.querySelector('[data-lang-toggle]');
  if (langToggleBtn) {
    langToggleBtn.addEventListener('click', function() {
      var current = root.getAttribute('data-lang') || 'zh';
      setLanguage(current === 'zh' ? 'en' : 'zh');
    });
  }

  // 初始化语言
  var savedLang = localStorage.getItem('airt-lang') || 'zh';
  setLanguage(savedLang);

})();
