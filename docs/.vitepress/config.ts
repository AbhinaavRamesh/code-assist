import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

export default withMermaid(
  defineConfig({
    title: 'code-assist',
    description: 'AI-powered coding assistant - Python package',
    base: '/code-assist/',
    lang: 'en-US',
    cleanUrls: true,
    lastUpdated: true,

    head: [
      ['link', { rel: 'icon', type: 'image/svg+xml', href: '/logo.svg' }],
      ['meta', { name: 'theme-color', content: '#D97706' }],
      ['meta', { property: 'og:type', content: 'website' }],
      ['meta', { property: 'og:title', content: 'code-assist' }],
      ['meta', { property: 'og:description', content: 'AI-powered coding assistant - Python package' }],
    ],

    themeConfig: {
      logo: '/logo.svg',
      siteTitle: 'code-assist',

      search: {
        provider: 'local',
        options: {
          detailedView: true,
        },
      },

      nav: [
        { text: 'Guide', link: '/guide/getting-started', activeMatch: '/guide/' },
        { text: 'Tools', link: '/guide/tools', activeMatch: '/guide/tools' },
        { text: 'API', link: '/api/', activeMatch: '/api/' },
        {
          text: 'v0.1.0',
          items: [
            { text: 'Changelog', link: '/changelog' },
            { text: 'Contributing', link: '/contributing' },
          ],
        },
        { text: 'GitHub', link: 'https://github.com/abhinaavramesh/code-assist' },
      ],

      sidebar: {
        '/guide/': [
          {
            text: 'Getting Started',
            collapsed: false,
            items: [
              { text: 'Introduction', link: '/guide/getting-started' },
              { text: 'Architecture', link: '/guide/architecture' },
            ],
          },
          {
            text: 'Core Concepts',
            collapsed: false,
            items: [
              { text: 'Tools Reference', link: '/guide/tools' },
              { text: 'Commands', link: '/guide/commands' },
              { text: 'Permissions', link: '/guide/permissions' },
              { text: 'Configuration', link: '/guide/configuration' },
            ],
          },
          {
            text: 'Advanced',
            collapsed: false,
            items: [
              { text: 'Hooks', link: '/guide/hooks' },
              { text: 'MCP Servers', link: '/guide/mcp' },
              { text: 'Agents', link: '/guide/agents' },
              { text: 'Memory System', link: '/guide/memory' },
              { text: 'Tasks', link: '/guide/tasks' },
              { text: 'Skills & Plugins', link: '/guide/skills' },
            ],
          },
        ],
        '/api/': [
          {
            text: 'API Reference',
            collapsed: false,
            items: [
              { text: 'Overview', link: '/api/' },
              { text: 'QueryEngine', link: '/api/query-engine' },
              { text: 'Tools API', link: '/api/tools' },
            ],
          },
        ],
      },

      socialLinks: [
        { icon: 'github', link: 'https://github.com/abhinaavramesh/code-assist' },
      ],

      editLink: {
        pattern: 'https://github.com/abhinaavramesh/code-assist/edit/main/docs/:path',
        text: 'Edit this page on GitHub',
      },

      footer: {
        message: 'Research and educational use only. Inspired by Claude Code by Anthropic. All original rights reserved by Anthropic.',
        copyright: 'Copyright 2025-present Abhinaav Ramesh',
      },

      outline: {
        level: [2, 3],
      },
    },

    mermaid: {
      theme: 'default',
      themeVariables: {
        fontSize: '16px',
      },
    },

    mermaidPlugin: {
      class: 'mermaid-zoom',
    },

    markdown: {
      lineNumbers: true,
    },
  })
)
