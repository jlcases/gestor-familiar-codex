<script>
  import { X } from 'phosphor-svelte';
  let { title, subtitle = '', onclose, children } = $props();
  function keydown(e) { if (e.key === 'Escape') onclose(); }
</script>
<svelte:window onkeydown={keydown} />
<div class="backdrop" role="presentation" onclick={(e) => e.target === e.currentTarget && onclose()}>
  <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
    <header><div><p class="eyebrow">NUEVO</p><h2 id="modal-title">{title}</h2>{#if subtitle}<p>{subtitle}</p>{/if}</div><button class="icon-btn" onclick={onclose} aria-label="Cerrar"><X size={20}/></button></header>
    {@render children()}
  </div>
</div>
