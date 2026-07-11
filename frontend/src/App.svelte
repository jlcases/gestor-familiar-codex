<script>
  import { House, CheckSquare, CalendarBlank, ShoppingCart, Wallet, Plus, Bell, List, X, ArrowRight, Check, MapPin, Trash, UsersThree } from 'phosphor-svelte';
  import { api } from './lib/api.js';
  import Modal from './lib/Modal.svelte';

  const nav = [
    { id:'inicio', label:'Inicio', icon:House }, { id:'tareas', label:'Tareas', icon:CheckSquare },
    { id:'calendario', label:'Calendario', icon:CalendarBlank }, { id:'compra', label:'Compra', icon:ShoppingCart },
    { id:'gastos', label:'Gastos', icon:Wallet }
  ];
  let page = $state('inicio'), loading = $state(true), error = $state(''), mobile = $state(false), modal = $state('');
  let members = $state([]), dashboard = $state(null), tasks = $state([]), events = $state([]), shopping = $state([]), expenses = $state([]);
  let form = $state({});
  const today = new Date().toISOString().slice(0,10);
  const fmtDate = (d) => new Intl.DateTimeFormat('es-ES',{weekday:'short',day:'numeric',month:'short'}).format(new Date(d+'T12:00:00'));
  const money = (n) => new Intl.NumberFormat('es-ES',{style:'currency',currency:'EUR'}).format(n);
  const greeting = new Date().getHours() < 14 ? 'Buenos días' : new Date().getHours() < 20 ? 'Buenas tardes' : 'Buenas noches';

  async function load() {
    loading = true; error = '';
    try { [members,dashboard,tasks,events,shopping,expenses] = await Promise.all(['/members','/dashboard','/tasks','/events','/shopping','/expenses'].map(api.get)); }
    catch(e) { error = e.message; } finally { loading = false; }
  }
  $effect(() => { load(); });
  function open(type) {
    modal = type;
    form = type === 'task' ? {title:'',category:'Casa',due_date:today,due_time:'',assignee_id:members[0]?.id,priority:'normal'} :
      type === 'event' ? {title:'',event_date:today,start_time:'18:00',end_time:'',location:'',category:'Familia',member_id:members[0]?.id} :
      type === 'shopping' ? {name:'',quantity:'1',section:'Despensa',added_by:members[0]?.id} :
      {concept:'',amount:'',category:'Casa',expense_date:today,member_id:members[0]?.id};
  }
  async function save(e) {
    e.preventDefault(); error='';
    const endpoints={task:'/tasks',event:'/events',shopping:'/shopping',expense:'/expenses'};
    try { await api.post(endpoints[modal], form); modal=''; await load(); } catch(e) { error=e.message; }
  }
  async function toggle(kind,id) { await api.patch(`/${kind}/${id}/toggle`); await load(); }
  async function remove(kind,id) { await api.delete(`/${kind}/${id}`); await load(); }
  function navigate(id) { page=id; mobile=false; }
</script>

<svelte:head><title>{nav.find(n=>n.id===page)?.label} — Nido</title></svelte:head>

<div class="shell">
  <aside class:open={mobile}>
    <div class="brand"><div class="mark"><span></span><span></span><span></span></div><strong>Nido</strong><button class="mobile-close" onclick={()=>mobile=false} aria-label="Cerrar menú"><X/></button></div>
    <nav aria-label="Navegación principal">
      {#each nav as item}<button class:active={page===item.id} onclick={()=>navigate(item.id)}><item.icon size={21} weight={page===item.id?'fill':'regular'}/><span>{item.label}</span>{#if item.id==='tareas' && dashboard}<em>{dashboard.stats.open_tasks}</em>{/if}</button>{/each}
    </nav>
    <div class="family"><div class="family-title"><span>LA FAMILIA</span><UsersThree size={17}/></div><div class="avatar-stack">{#each members as m}<span style={`--avatar:${m.color}`} title={m.name}>{m.initials}</span>{/each}</div><small>{members.map(m=>m.name).join(', ')}</small></div>
    <div class="profile"><span class="avatar main">MA</span><div><strong>Mara</strong><small>Administradora</small></div></div>
  </aside>
  {#if mobile}<button class="scrim" onclick={()=>mobile=false} aria-label="Cerrar menú"></button>{/if}

  <main>
    <header class="topbar"><button class="menu-btn" onclick={()=>mobile=true} aria-label="Abrir menú"><List size={24}/></button><div class="crumb">NIDO <span>/</span> {nav.find(n=>n.id===page)?.label.toUpperCase()}</div><button class="bell" aria-label="Notificaciones"><Bell size={21}/><span></span></button></header>
    {#if error}<div class="error-banner">{error}<button onclick={()=>error=''}><X size={18}/></button></div>{/if}
    {#if loading}
      <div class="content skeletons"><div class="skeleton wide"></div><div class="skeleton grid"></div><div class="skeleton tall"></div></div>
    {:else if page==='inicio'}
      <div class="content reveal">
        <section class="welcome"><div><p class="eyebrow">{new Intl.DateTimeFormat('es-ES',{weekday:'long',day:'numeric',month:'long'}).format(new Date())}</p><h1>{greeting}, Mara.</h1><p>Todo lo importante de casa, a la vista.</p></div><button class="primary" onclick={()=>open('task')}><Plus size={19} weight="bold"/>Añadir tarea</button></section>
        <section class="pulse-grid">
          <button onclick={()=>navigate('tareas')}><span class="metric">{dashboard.stats.open_tasks}</span><span>Tareas pendientes</span><small>Ver lista <ArrowRight/></small></button>
          <button onclick={()=>navigate('calendario')}><span class="metric">{dashboard.stats.today_events}</span><span>Planes para hoy</span><small>Ver agenda <ArrowRight/></small></button>
          <button class="accent" onclick={()=>navigate('compra')}><span class="metric">{dashboard.stats.shopping_left}</span><span>Faltan en la compra</span><small>Ir a la lista <ArrowRight/></small></button>
          <button onclick={()=>navigate('gastos')}><span class="metric money">{money(dashboard.stats.month_spend)}</span><span>Gastado este mes</span><small>Ver gastos <ArrowRight/></small></button>
        </section>
        <div class="dashboard-grid">
          <section class="panel"><div class="panel-head"><div><p class="eyebrow">EN MARCHA</p><h2>Tareas de hoy</h2></div><button onclick={()=>navigate('tareas')}>Ver todas <ArrowRight/></button></div>
            <div class="list">{#each dashboard.tasks as t}<article class:done={t.completed}><button class="check" onclick={()=>toggle('tasks',t.id)} aria-label="Completar tarea">{#if t.completed}<Check weight="bold"/>{/if}</button><div class="grow"><strong>{t.title}</strong><small>{t.category}{t.due_time ? ` · ${t.due_time}`:''}</small></div>{#if t.initials}<span class="avatar mini" style={`--avatar:${t.color}`}>{t.initials}</span>{/if}</article>{/each}</div>
          </section>
          <section class="agenda"><div class="panel-head"><div><p class="eyebrow">PRÓXIMAMENTE</p><h2>Agenda familiar</h2></div></div>{#each dashboard.events as ev}<article><div class="date-block"><strong>{new Date(ev.event_date+'T12:00').getDate()}</strong><small>{new Intl.DateTimeFormat('es-ES',{month:'short'}).format(new Date(ev.event_date+'T12:00'))}</small></div><div><strong>{ev.title}</strong><small>{ev.start_time}{ev.location ? ` · ${ev.location}`:''}</small></div></article>{/each}</section>
        </div>
      </div>
    {:else if page==='tareas'}
      <div class="content reveal"><PageHeader eyebrow="ORGANIZACIÓN" title="Tareas" subtitle={`${tasks.filter(t=>!t.completed).length} pendientes entre todos`} action="Nueva tarea" onclick={()=>open('task')}/><section class="panel full"><div class="list task-list">{#each tasks as t}<article class:done={t.completed}><button class="check" onclick={()=>toggle('tasks',t.id)} aria-label="Cambiar estado">{#if t.completed}<Check weight="bold"/>{/if}</button><div class="grow"><strong>{t.title}</strong><small><span class="tag">{t.category}</span> {fmtDate(t.due_date)} {t.due_time||''}</small></div>{#if t.priority==='alta'}<span class="priority">PRIORIDAD</span>{/if}<span class="avatar mini" style={`--avatar:${t.color||'#777'}`}>{t.initials||'—'}</span><button class="delete" onclick={()=>remove('tasks',t.id)} aria-label="Eliminar"><Trash/></button></article>{/each}</div></section></div>
    {:else if page==='calendario'}
      <div class="content reveal"><PageHeader eyebrow="TIEMPO COMPARTIDO" title="Calendario" subtitle="La semana de todos, sin cruces" action="Nuevo evento" onclick={()=>open('event')}/><section class="timeline">{#each events as ev, i}{#if i===0 || events[i-1].event_date!==ev.event_date}<h3>{fmtDate(ev.event_date)}</h3>{/if}<article><time>{ev.start_time}<small>{ev.end_time||''}</small></time><div class="line"><span style={`--event:${ev.color||'#315c4a'}`}></span></div><div><span class="tag">{ev.category}</span><h2>{ev.title}</h2>{#if ev.location}<p><MapPin size={16}/>{ev.location}</p>{/if}<small>Con {ev.member_name||'toda la familia'}</small></div></article>{/each}</section></div>
    {:else if page==='compra'}
      <div class="content reveal"><PageHeader eyebrow="LISTA COMPARTIDA" title="La compra" subtitle={`${shopping.filter(i=>!i.checked).length} cosas por coger`} action="Añadir producto" onclick={()=>open('shopping')}/><section class="shopping-board">{#each [...new Set(shopping.map(i=>i.section))] as section}<div><h3>{section}</h3>{#each shopping.filter(i=>i.section===section) as item}<article class:done={item.checked}><button class="check" onclick={()=>toggle('shopping',item.id)}>{#if item.checked}<Check weight="bold"/>{/if}</button><div class="grow"><strong>{item.name}</strong><small>{item.quantity} · añadió {item.added_by_name}</small></div><button class="delete" onclick={()=>remove('shopping',item.id)}><Trash/></button></article>{/each}</div>{/each}</section></div>
    {:else}
      <div class="content reveal"><PageHeader eyebrow="ECONOMÍA DOMÉSTICA" title="Gastos" subtitle="Una visión clara, sin hojas de cálculo" action="Añadir gasto" onclick={()=>open('expense')}/><div class="finance-summary"><div><small>GASTO ESTE MES</small><strong>{money(expenses.reduce((a,e)=>a+e.amount,0))}</strong></div><div class="bar"><span style={`width:${Math.min(100,expenses.reduce((a,e)=>a+e.amount,0)/12)}%`}></span></div><p>Presupuesto orientativo de 1.200 €</p></div><section class="panel full expense-list">{#each expenses as ex}<article><span class="expense-icon"><Wallet/></span><div class="grow"><strong>{ex.concept}</strong><small>{ex.category} · {fmtDate(ex.expense_date)} · {ex.member_name}</small></div><strong class="amount">−{money(ex.amount)}</strong></article>{/each}</section></div>
    {/if}
  </main>
</div>

{#if modal}
  <Modal title={{task:'Nueva tarea',event:'Nuevo evento',shopping:'Añadir a la compra',expense:'Registrar gasto'}[modal]} onclose={()=>modal=''}>
    <form onsubmit={save}>
      {#if modal==='task'}<Field label="¿Qué hay que hacer?"><input bind:value={form.title} required minlength="2" placeholder="Ej. Llamar al pediatra"/></Field><div class="form-grid"><Field label="Fecha"><input type="date" bind:value={form.due_date} required/></Field><Field label="Hora"><input type="time" bind:value={form.due_time}/></Field></div><Field label="Responsable"><select bind:value={form.assignee_id}>{#each members as m}<option value={m.id}>{m.name}</option>{/each}</select></Field>
      {:else if modal==='event'}<Field label="Nombre del evento"><input bind:value={form.title} required placeholder="Ej. Festival del colegio"/></Field><div class="form-grid"><Field label="Fecha"><input type="date" bind:value={form.event_date} required/></Field><Field label="Empieza"><input type="time" bind:value={form.start_time} required/></Field></div><Field label="Lugar"><input bind:value={form.location} placeholder="Opcional"/></Field>
      {:else if modal==='shopping'}<Field label="Producto"><input bind:value={form.name} required placeholder="Ej. Tomates cherry"/></Field><div class="form-grid"><Field label="Cantidad"><input bind:value={form.quantity}/></Field><Field label="Sección"><select bind:value={form.section}><option>Fruta y verdura</option><option>Despensa</option><option>Frío</option><option>Hogar</option><option>Otros</option></select></Field></div>
      {:else}<Field label="Concepto"><input bind:value={form.concept} required placeholder="Ej. Material escolar"/></Field><div class="form-grid"><Field label="Importe (€)"><input type="number" min="0.01" step="0.01" bind:value={form.amount} required/></Field><Field label="Fecha"><input type="date" bind:value={form.expense_date} required/></Field></div><Field label="Categoría"><select bind:value={form.category}><option>Casa</option><option>Alimentación</option><option>Salud</option><option>Actividades</option><option>Educación</option><option>Otros</option></select></Field>{/if}
      <div class="form-actions"><button type="button" class="secondary" onclick={()=>modal=''}>Cancelar</button><button class="primary" type="submit">Guardar</button></div>
    </form>
  </Modal>
{/if}

{#snippet PageHeader(eyebrow,title,subtitle,action,onclick)}<section class="page-head"><div><p class="eyebrow">{eyebrow}</p><h1>{title}</h1><p>{subtitle}</p></div><button class="primary" {onclick}><Plus size={19} weight="bold"/>{action}</button></section>{/snippet}
{#snippet Field(label, children)}<label class="field"><span>{label}</span>{@render children()}</label>{/snippet}
