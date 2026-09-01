/**
 * Renderizador de Markdown.
 *
 * Segurança: `react-markdown` **não** interpreta HTML bruto por padrão (não
 * usamos `rehype-raw`), então qualquer `<script>` que passasse pelo
 * sanitizador do backend seria exibido como texto, não executado. É a segunda
 * camada da defesa contra XSS.
 */
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function Markdown({ children, className = '' }) {
  if (!children?.trim()) {
    return <p className="text-subtle text-sm italic">Esta anotação ainda está vazia.</p>
  }

  return (
    <div className={`markdown-body ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Links externos abrem em nova aba, sem vazar o referrer nem
          // dar acesso a `window.opener`.
          a: ({ node, ...props }) => (
            <a {...props} target="_blank" rel="noopener noreferrer nofollow" />
          ),
          // Checklists do GFM são apenas visuais (o estado vive no Markdown).
          input: ({ node, ...props }) => <input {...props} disabled readOnly />,
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  )
}
