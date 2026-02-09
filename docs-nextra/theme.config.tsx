import React from 'react'
import { DocsThemeConfig } from 'nextra-theme-docs'
import { useTheme } from 'next-themes'

const basePath = '/cldpm'

const Logo = () => {
  const { resolvedTheme } = useTheme()
  return (
    <>
      <img
        src={`${basePath}/logo/light.svg`}
        alt="CLDPM"
        height={24}
        style={{
          height: 24,
          display: resolvedTheme === 'dark' ? 'none' : 'block'
        }}
      />
      <img
        src={`${basePath}/logo/dark.svg`}
        alt="CLDPM"
        height={24}
        style={{
          height: 24,
          display: resolvedTheme === 'dark' ? 'block' : 'none'
        }}
      />
    </>
  )
}

const config: DocsThemeConfig = {
  logo: <Logo />,
  project: {
    link: 'https://github.com/transilienceai/cldpm',
  },
  docsRepositoryBase: 'https://github.com/transilienceai/cldpm/tree/main/docs-nextra',
  footer: {
    text: (
      <span>
        Crafted by{' '}
        <a href="https://transilience.ai" target="_blank" rel="noopener noreferrer">
          Transilience.ai
        </a>
      </span>
    ),
  },
  head: (
    <>
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta property="og:title" content="CLDPM - Claude Project Manager" />
      <meta property="og:description" content="Mono repo management for Claude Code projects" />
      <link rel="icon" type="image/svg+xml" href={`${basePath}/logo/light.svg`} media="(prefers-color-scheme: light)" />
      <link rel="icon" type="image/svg+xml" href={`${basePath}/logo/dark.svg`} media="(prefers-color-scheme: dark)" />
    </>
  ),
  useNextSeoProps() {
    return {
      titleTemplate: '%s – CLDPM'
    }
  },
  primaryHue: 270,
  sidebar: {
    defaultMenuCollapseLevel: 1,
    toggleButton: true,
  },
  toc: {
    backToTop: true,
  },
}

export default config
