import DefaultTheme from 'vitepress/theme'
import './mermaid-zoom.css'

export default {
  extends: DefaultTheme,
  enhanceApp({ app, router }) {
    // After each page load, make mermaid diagrams zoomable
    if (typeof window !== 'undefined') {
      const addZoomToMermaid = () => {
        document.querySelectorAll('.mermaid').forEach((el: Element) => {
          if (el.getAttribute('data-zoom-ready')) return
          el.setAttribute('data-zoom-ready', 'true')

          el.addEventListener('click', () => {
            el.classList.toggle('mermaid-zoomed')
          })
        })
      }

      // Run on initial load and on route changes
      router.onAfterRouteChanged = () => {
        setTimeout(addZoomToMermaid, 500)
      }
      setTimeout(addZoomToMermaid, 1000)
    }
  },
}
