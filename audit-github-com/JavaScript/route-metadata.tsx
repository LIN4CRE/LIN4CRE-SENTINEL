// Public-site SPA pattern only. Prefer prerender/SSR for indexable public content.
import { useEffect } from 'react'

export function usePageMetadata(title: string, description: string, canonicalUrl: string) {
  useEffect(() => {
    const previousTitle = document.title
    document.title = title

    let descriptionNode = document.head.querySelector<HTMLMetaElement>('meta[name="description"]')
    if (!descriptionNode) {
      descriptionNode = document.createElement('meta')
      descriptionNode.name = 'description'
      document.head.appendChild(descriptionNode)
    }
    descriptionNode.content = description

    let canonicalNode = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]')
    if (!canonicalNode) {
      canonicalNode = document.createElement('link')
      canonicalNode.rel = 'canonical'
      document.head.appendChild(canonicalNode)
    }
    canonicalNode.href = canonicalUrl
    return () => { document.title = previousTitle }
  }, [title, description, canonicalUrl])
}

// For SEO-critical pages, emit metadata in server-rendered HTML. Client updates alone may not be seen reliably.
