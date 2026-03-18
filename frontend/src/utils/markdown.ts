import DOMPurify from 'dompurify'
import { marked } from 'marked'

export function renderMarkdown(content: string): string {
  const raw = marked.parse(content, { breaks: true }) as string
  return DOMPurify.sanitize(raw)
}
