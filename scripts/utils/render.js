/**
 *
 * @param {typeof import('svelte').SvelteComponent} Component
 * @param {HTMLElement} target
 * @param {Record<string, any>} props
 * @param {import('svelte').Com}
 */
export function renderSvelteComponent(
  Component,
  target,
  props = {},
  hydrate = false
) {
  return new Component({ target, props, hydrate });
}
