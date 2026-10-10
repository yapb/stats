<template>
  <div class="max-w-6xl mx-auto px-4 py-8">
    <header class="mb-6">
      <h1 class="text-3xl font-bold text-white">
        <a href="#/" style="color:#fff">Addons Stats</a>
      </h1>
      <p class="text-slate-400 mt-1">
        Daily census of public Half-Life servers: which addons run where and on
        which version. Scanned via Steam master list plus A2S queries.
      </p>
    </header>

    <div v-if="failed" class="card p-6 text-slate-400">
      No data yet: the first scheduled census has not run. Check back soon.
    </div>
    <Overview v-else-if="latest && route.view === 'overview'" :latest="latest" :hist-rows="histRows" />
    <AddonView
      v-else-if="latest && route.view === 'addon'"
      :latest="latest"
      :hist-rows="histRows"
      :name="route.param"
    />
    <ModView
      v-else-if="latest && route.view === 'mod'"
      :latest="latest"
      :hist-rows="histRows"
      :appid="route.param"
    />

    <footer v-if="latest" class="text-sm text-slate-500 mt-6">
      <p>{{ quality }}</p>
      <p class="mt-2">
        Raw data:
        <a href="data/latest.json">latest.json</a>,
        <a href="data/history.json">history.json</a>, source:
        <a href="https://github.com/yapb/stats">yapb/stats</a>. Missing your
        addon or mod? Open a PR against
        <a href="https://github.com/yapb/stats/blob/master/config/tracked_vars.yml">tracked_vars.yml</a>
        or
        <a href="https://github.com/yapb/stats/blob/master/config/mods.yml">mods.yml</a>.
      </p>
    </footer>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import AddonView from './views/AddonView.vue';
import ModView from './views/ModView.vue';
import Overview from './views/Overview.vue';
import { fmt, loadJSON } from './lib/data.js';

const latest = ref(null);
const histRows = ref([]);
const failed = ref(false);
const route = ref(parseHash());

function parseHash() {
  const h = location.hash || '#/';
  if (h.indexOf('#/addon/') === 0) {
    return { view: 'addon', param: decodeURIComponent(h.slice(8)) };
  }
  if (h.indexOf('#/mod/') === 0) {
    return { view: 'mod', param: decodeURIComponent(h.slice(6)) };
  }
  return { view: 'overview', param: null };
}

function onHash() {
  route.value = parseHash();
  window.scrollTo(0, 0);
}

onMounted(async function () {
  addEventListener('hashchange', onHash);
  try {
    latest.value = await loadJSON('data/latest.json');
    try {
      histRows.value = await loadJSON('data/history.json');
    } catch (e) {
      histRows.value = [];
    }
  } catch (e) {
    failed.value = true;
  }
});

onBeforeUnmount(function () {
  removeEventListener('hashchange', onHash);
});

const quality = computed(function () {
  if (!latest.value) {
    return '';
  }
  const t = latest.value.totals;
  const trunc = ((latest.value.quality && latest.value.quality.truncated_appids) || []).join(', ');
  return (
    'Unknown is not absent: ' +
    fmt(t.rules_unknown) +
    ' alive servers ignore A2S_RULES (firewalled), so their versions stay unseen.' +
    (trunc ? ' Master list truncated at 10k for appids: ' + trunc + ' (partial census).' : '') +
    ' ' +
    fmt(t.farm_dropped || 0) +
    ' farm addrs on ' +
    t.ips_over_100_servers +
    ' dense hosts plus ' +
    fmt(t.fake_dropped || 0) +
    ' fake player-count addrs excluded before scanning.'
  );
});
</script>
