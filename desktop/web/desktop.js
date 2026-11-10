'use strict';

let desktopApi = null;
let desktopExpanded = false;
let desktopPinned = false;
let desktopNoticeTimer = null;
let desktopTheme = 'system';

function desktopNotify(message) {
  const status = document.getElementById('desktop-status');
  status.textContent = message;
  status.hidden = false;
  clearTimeout(desktopNoticeTimer);
  desktopNoticeTimer = setTimeout(() => { status.hidden = true; }, 4000);
}

async function desktopCall(method, ...args) {
  if (!desktopApi) throw new Error('Aguarde a preparação do Vehicula.');
  try {
    return await desktopApi[method](...args);
  } catch (error) {
    desktopNotify('A operação falhou. Tente novamente.');
    throw error;
  }
}

async function desktopOpenTool(id) {
  const result = await desktopCall('open_tool', id);
  desktopNotify(result.message);
  await desktopRefreshStatus();
}

async function desktopSetExpanded(expanded) {
  await desktopCall('set_expanded', expanded);
  desktopExpanded = expanded;
  document.body.classList.toggle('desktop-compact', !expanded);
  document.getElementById('desktop-expand').textContent = expanded ? 'Recolher' : 'Ferramentas';
  document.getElementById('desktop-expand').setAttribute('aria-expanded', String(expanded));
  if (!expanded) document.getElementById('desktop-preferences').hidden = true;
}

async function desktopToggleWorkspace() {
  await desktopSetExpanded(!desktopExpanded);
}

async function desktopTogglePin() {
  const result = await desktopCall('set_on_top', !desktopPinned);
  desktopPinned = result.on_top;
  document.getElementById('desktop-pin').setAttribute('aria-pressed', String(desktopPinned));
}

async function desktopSettings() {
  const preferences = document.getElementById('desktop-preferences');
  if (!desktopExpanded) await desktopSetExpanded(true);
  preferences.hidden = !preferences.hidden;
  if (!preferences.hidden) document.getElementById('desktop-theme').focus();
}

function desktopApplyTheme(theme) {
  desktopTheme = theme;
  applyTheme(theme === 'system' ? (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark') : theme);
  document.getElementById('desktop-theme').value = theme;
}

async function desktopChangeTheme(theme) {
  desktopApplyTheme(theme);
  await desktopCall('save_preferences', {theme});
}

async function desktopRefreshStatus() {
  if (!desktopApi) return;
  const status = await desktopApi.get_tool_status();
  for (const id of ['preparafrota', 'pbix']) {
    document.getElementById(`open-${id}`).classList.toggle('is-running', !!status[id]);
  }
}

function desktopMinimize() { return desktopCall('minimize'); }
function desktopClose() { return desktopCall('close'); }

const desktopOriginalShowPage = window.showPage;
window.showPage = function(id, navButton) {
  desktopOriginalShowPage(id, navButton);
  document.getElementById('desktop-tool-picker').value = id;
  if (desktopApi && !desktopExpanded) desktopSetExpanded(true);
  document.querySelector('.shell').scrollTo(0, 0);
};

const desktopOriginalToggleFav = window.toggleFav;
window.toggleFav = function(event, id) {
  desktopOriginalToggleFav(event, id);
  if (desktopApi) desktopCall('save_preferences', {favorites: getFavs()});
};

window.toggleTheme = function() {
  desktopChangeTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark');
};

matchMedia('(prefers-color-scheme: light)').addEventListener('change', () => {
  if (desktopTheme === 'system') desktopApplyTheme('system');
});

async function desktopInitialize() {
  desktopApi = window.pywebview.api;
  try {
    const preferences = await desktopApi.get_preferences();
    desktopApplyTheme(preferences.theme);
    memFavs = preferences.favorites;
    renderFavs();
    desktopPinned = preferences.on_top;
    document.getElementById('desktop-pin').setAttribute('aria-pressed', String(desktopPinned));
    document.querySelectorAll('[data-native]').forEach(button => { button.disabled = false; });
    document.documentElement.dataset.desktopReady = 'true';
    setInterval(() => desktopRefreshStatus().catch(() => {}), 1500);
  } catch (error) {
    desktopNotify('Não foi possível preparar o painel. Feche e abra o Vehicula novamente.');
  }
}

window.addEventListener('pywebviewready', desktopInitialize);
if (window.pywebview && window.pywebview.api) desktopInitialize();
