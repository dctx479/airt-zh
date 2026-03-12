/* app.js — AIRT AI 红队学院交互脚本 */

(function() {
  'use strict';

  /* ========================================
     主题切换
     ======================================== */
  const themeToggle = document.querySelector('[data-theme-toggle]');
  const root = document.documentElement;
  let theme = 'dark'; // 安全课程默认使用暗色主题
  root.setAttribute('data-theme', theme);

  function updateToggleIcon() {
    if (!themeToggle) return;
    themeToggle.setAttribute('aria-label',
      '切换到' + (theme === 'dark' ? '浅色' : '暗色') + '模式'
    );
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
      skip_link: '跳转到内容',
      nav_home: '首页', nav_modules: '模块', nav_labs: '实验室',
      nav_tools: '工具', nav_about: '关于',
      hero_badge: '开源 · 永久免费',
      hero_title_1: 'AI 红队', hero_title_2: '学院',
      hero_subtitle: '掌握 AI 安全。破解 AI 系统。保护重要的东西。',
      hero_description: '一门免费的开源课程，涵盖 AI 系统的攻击性安全测试 — 从 Prompt Injection 到供应链攻击。60+ 小时的内容，包含实践 Docker 实验室。',
      hero_cta_start: '开始学习', hero_cta_download: '下载全部实验室',
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
      lab1_title: '实验室 1：设置你的 AI 红队实验室',
      lab1_desc: '部署完整的 AI 红队环境，包含本地 LLM（Ollama）、向量数据库和测试工具。包含一个易受攻击的聊天机器人应用程序作为你的第一个目标。',
      lab2_title: '实验室 2：Prompt Injection 游乐场',
      lab2_desc: '攻击一系列逐渐加固的聊天机器人。从未受保护的模型开始，通过受保护的系统进行，并学习系统地发现绕过方法。',
      lab3_title: '实验室 3：破坏 RAG 系统',
      lab3_desc: '构建然后系统地破坏 RAG 应用程序。投毒其知识库、劫持检索、执行嵌入反演并通过 LLM 泄露数据。',
      lab4_title: '实验室 4：破坏多智能体系统',
      lab4_desc: '攻击多智能体客户服务系统，其中智能体协作处理请求。破坏一个智能体以影响其他智能体、提升权限并通过工具调用泄露数据。',
      lab5_title: '实验室 5：AI 供应链攻击模拟',
      lab5_desc: '模拟对 ML 管道的供应链攻击。创建后门模型、利用 pickle 反序列化、演示域名抢注并投毒训练数据以破坏模型行为。',
      lab6_title: '实验室 6：模型盗窃与隐私攻击',
      lab6_desc: '通过战略性 API 查询提取专有模型的行为。执行成员推断、尝试训练数据提取并分析加密流量以查找信息泄露。',
      lab7_title: '实验室 7：自动化红队管道',
      lab7_desc: '使用 garak、PyRIT 和 promptfoo 构建并运行自动化 AI 红队管道。测试多个模型、生成综合报告，并将安全测试集成到 CI/CD 工作流中。',
      lab8_title: '实验室 8：完整的 AI 红队参与',
      lab8_desc: '对现实的 AI 驱动企业应用程序进行完整的 AI 红队参与。执行侦察、链接多个利用、演示业务影响并交付专业报告。',
      tools_label: '工具与资源', tools_title: '开源工具库',
      tools_desc: '整个课程中使用的三个行业领先工具，用于自动化 AI 漏洞发现和红队。',
      garak_org: '由 NVIDIA 开发',
      garak_desc: 'LLM 漏洞扫描器，包含 12 个类别中的 47+ 个探针。自动检测 Prompt Injection、数据泄露、毒性、幻觉等。',
      link_website: '官网'
    },
    en: {
      skip_link: 'Skip to content',
      nav_home: 'Home', nav_modules: 'Modules', nav_labs: 'Labs',
      nav_tools: 'Tools', nav_about: 'About',
      hero_badge: 'Open Source · Free Forever',
      hero_title_1: 'AI Red Team', hero_title_2: 'Academy',
      hero_subtitle: 'Master AI Security. Break AI Systems. Defend What Matters.',
      hero_description: 'A free, open-source course covering offensive security testing of AI systems — from prompt injection to supply chain attacks. 60+ hours of content with hands-on Docker labs.',
      hero_cta_start: 'Start Learning', hero_cta_download: 'Download All Labs',
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
      lab1_title: 'Lab 1: Set Up Your AI Red Team Lab',
      lab1_desc: 'Deploy a complete AI red teaming environment with a local LLM (Ollama), vector database, and testing tools. Includes a vulnerable chatbot application as your first target.',
      lab2_title: 'Lab 2: Prompt Injection Playground',
      lab2_desc: 'Attack a series of progressively hardened chatbots. Start with an unprotected model, work through protected systems, and learn to systematically discover bypass techniques.',
      lab3_title: 'Lab 3: Compromising a RAG System',
      lab3_desc: 'Build and then systematically compromise a RAG application. Poison its knowledge base, hijack retrieval, perform embedding inversion, and exfiltrate data through the LLM.',
      lab4_title: 'Lab 4: Breaking Multi-Agent Systems',
      lab4_desc: 'Attack a multi-agent customer service system where agents collaborate to handle requests. Compromise one agent to influence others, escalate privileges, and exfiltrate data through tool calls.',
      lab5_title: 'Lab 5: AI Supply Chain Attack Simulation',
      lab5_desc: 'Simulate a supply chain attack against an ML pipeline. Create backdoored models, exploit pickle deserialization, demonstrate typosquatting, and poison training data to corrupt model behavior.',
      lab6_title: 'Lab 6: Model Theft & Privacy Attacks',
      lab6_desc: 'Extract a proprietary model\'s behavior through strategic API queries. Perform membership inference, attempt training data extraction, and analyze encrypted traffic for information leakage.',
      lab7_title: 'Lab 7: Automated Red Teaming Pipeline',
      lab7_desc: 'Build and run an automated AI red teaming pipeline using garak, PyRIT, and promptfoo. Test multiple models, generate comprehensive reports, and integrate security testing into CI/CD workflows.',
      lab8_title: 'Lab 8: Full AI Red Team Engagement',
      lab8_desc: 'Conduct a complete AI red team engagement against a realistic AI-powered enterprise application. Perform reconnaissance, chain multiple exploits, demonstrate business impact, and deliver a professional report.',
      tools_label: 'Tools & Resources', tools_title: 'Open-Source Toolkit',
      tools_desc: 'Three industry-leading tools used throughout the course for automated AI vulnerability discovery and red teaming.',
      garak_org: 'by NVIDIA',
      garak_desc: 'LLM vulnerability scanner with 47+ probes across 12 categories. Automatically detects prompt injection, data leakage, toxicity, hallucination, and more.',
      link_website: 'Website'
    }
  };

  function setLanguage(lang) {
    root.setAttribute('data-lang', lang);
    document.documentElement.setAttribute('lang', lang === 'zh' ? 'zh-CN' : 'en');
    document.querySelectorAll('[data-i18n]').forEach(function(el) {
      var key = el.getAttribute('data-i18n');
      if (translations[lang] && translations[lang][key]) {
        el.textContent = translations[lang][key];
      }
    });
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
