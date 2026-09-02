/**
 * Semantic tokens only. Every colour resolves through a CSS variable so light and dark
 * share one set of names, and no component hardcodes a hex value.
 *
 * The palette is warm parchment and ink with a single antique brass accent. Forest and
 * oxblood appear only where a result has to be reported (solved, failed). Nothing is
 * pastel, nothing is saturated past what print could hold, and there are no gradients.
 */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        canvas: 'rgb(var(--canvas) / <alpha-value>)',
        surface: 'rgb(var(--surface) / <alpha-value>)',
        raised: 'rgb(var(--raised) / <alpha-value>)',
        hairline: 'rgb(var(--hairline) / <alpha-value>)',
        ink: 'rgb(var(--ink) / <alpha-value>)',
        'ink-2': 'rgb(var(--ink-2) / <alpha-value>)',
        'ink-3': 'rgb(var(--ink-3) / <alpha-value>)',
        brass: 'rgb(var(--brass) / <alpha-value>)',
        'on-brass': 'rgb(var(--on-brass) / <alpha-value>)',
        forest: 'rgb(var(--forest) / <alpha-value>)',
        oxblood: 'rgb(var(--oxblood) / <alpha-value>)',
      },
      fontFamily: {
        /* System stacks only. No downloaded face, so first paint carries no text swap. */
        sans: [
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Helvetica Neue',
          'Arial',
          'sans-serif',
        ],
        serif: ['ui-serif', 'Iowan Old Style', 'Palatino', 'Georgia', 'serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'SF Mono', 'Menlo', 'monospace'],
      },
      fontSize: {
        micro: ['0.75rem', { lineHeight: '1.05rem', letterSpacing: '0.005em' }],
        caption: ['0.8125rem', { lineHeight: '1.3rem' }],
        body: ['0.9375rem', { lineHeight: '1.65' }],
        lead: ['1.0625rem', { lineHeight: '1.6' }],
        title: ['1.3125rem', { lineHeight: '1.3', letterSpacing: '-0.008em' }],
        display: ['1.875rem', { lineHeight: '1.2', letterSpacing: '-0.014em' }],
        hero: ['2.625rem', { lineHeight: '1.12', letterSpacing: '-0.018em' }],
      },
      maxWidth: { prose: '66ch' },
      /* Deliberately tight. Edges stay crisp rather than pill shaped. */
      borderRadius: { sm: '2px', DEFAULT: '3px', md: '3px', lg: '4px', xl: '4px' },
      spacing: { 11: '2.75rem' },
    },
  },
  plugins: [],
};
