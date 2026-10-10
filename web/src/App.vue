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
      :gamedir="route.param"
    />

    <footer v-if="latest" class="text-sm mt-6">
      <div class="card p-4 mb-4">
        <h2 class="font-semibold text-white mb-3">Census notes</h2>
        <dl class="grid sm:grid-cols-2 gap-x-6 gap-y-3">
          <div v-for="note in notes" :key="note.label" class="flex gap-3">
            <div class="num text-xl font-bold text-white whitespace-nowrap">{{ note.value }}</div>
            <div>
              <dt class="text-slate-200 text-sm font-medium">{{ note.label }}</dt>
              <dd class="text-slate-500 text-xs">{{ note.text }}</dd>
            </div>
          </div>
        </dl>
      </div>
      <p class="text-slate-500">
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

const notes = computed(function () {
  if (!latest.value) {
    return [];
  }
  const t = latest.value.totals;
  const trunc = (latest.value.quality && latest.value.quality.truncated_appids) || [];
  const out = [
    {
      label: 'Firewalled',
      value: fmt(t.rules_unknown),
      text: 'alive servers ignore A2S_RULES, their versions stay unseen',
    },
    {
      label: 'Farms excluded',
      value: fmt(t.farm_dropped || 0),
      text:
        'addrs on ' +
        t.ips_over_100_servers +
        ' dense hosts plus ' +
        fmt(t.fake_dropped || 0) +
        ' fake-count addrs, cut before scanning',
    },
  ];
  if ((t.mystery_servers || 0) > 0) {
    out.push({
      label: 'Mystery bots',
      value: fmt(t.mystery_servers),
      text: 'servers run bots with no recognized bot addon (' + fmt(t.mystery_bots) + ' bots)',
    });
  }
  if (trunc.length) {
    out.push({
      label: 'Partial census',
      value: trunc.join(', '),
      text: 'master list truncated at 10k appids',
    });
  }
  return out;
});
</script>
