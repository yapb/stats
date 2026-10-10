<template>
  <div class="crumb mb-2"><a :href="homePath()">Overview</a> / {{ addon.title }}</div>

  <div class="flex items-center gap-3 mb-4">
    <Avatar :title="addon.title" />
    <div>
      <h2 class="text-2xl font-bold text-white">Statistics for: {{ addon.title }}</h2>
      <div v-if="addon.url" class="text-slate-400 text-sm break-all">
        <a :href="addon.url">{{ addon.url }}</a> ({{ addon.name }})
      </div>
      <div v-else class="text-slate-400 text-sm">({{ addon.name }})</div>
    </div>
  </div>

  <SummaryBlock
    :date="stampToDate(latest.generated_at)"
    :servers="addon.servers || 0"
    :max-players="addon.max_players || 0"
    :players="addon.players || 0"
    :bots="addon.bots || 0"
  />

  <div class="card p-4 mb-4 overflow-x-auto">
    <h3 class="font-semibold text-white mb-2">Servers per mod</h3>
    <table class="stats w-full text-sm num">
      <thead>
        <tr>
          <th>Addon</th>
          <th @click="sortMods('label')" class="cursor-pointer select-none">
            Game mod{{ modArrow('label') }}
          </th>
          <th @click="sortMods('servers')" class="cursor-pointer select-none">
            Servers{{ modArrow('servers') }}
          </th>
          <th>% of mod</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="!sortedModRows.length">
          <td colspan="4" class="text-slate-500">Nothing seen yet.</td>
        </tr>
        <tr v-for="row in sortedModRows" :key="row.id" class="link" @click="openMod(row.id)">
          <td>{{ addon.title }}</td>
          <td>
            <a :href="modPath(row.id)" @click.stop>{{ row.label }}</a>
          </td>
          <td>{{ fmt(row.servers) }}</td>
          <td>{{ row.pct }}</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="card p-4 mb-4 overflow-x-auto">
    <h3 class="font-semibold text-white mb-2">Tracked values</h3>
    <p v-if="addon.novalue" class="text-slate-400 text-sm">
      Presence-only tracking: values of {{ addon.name }} are settings, not versions.
    </p>
    <table v-else class="stats w-full text-sm num">
      <thead>
        <tr>
          <th class="hidden sm:table-cell">Variable</th>
          <th @click="sortVals('value')" class="cursor-pointer select-none">
            Value{{ valArrow('value') }}
          </th>
          <th @click="sortVals('count')" class="cursor-pointer select-none">
            Servers{{ valArrow('count') }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="!sortedValRows.length">
          <td colspan="3" class="text-slate-500">Nothing seen yet.</td>
        </tr>
        <tr v-for="row in sortedValRows" :key="row.value">
          <td class="hidden sm:table-cell">{{ addon.name }}</td>
          <td>
            {{ row.value }}
            <span
              v-if="fresh.includes(row.value)"
              class="ml-1 text-[10px] font-bold text-black bg-lime-300 rounded px-1"
            >NEW</span>
          </td>
          <td>{{ fmt(row.count) }}</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="card p-4 mb-4">
    <h3 class="font-semibold text-white mb-2">Servers by country</h3>
    <CountriesChart :countries="addon.countries || []" />
  </div>

  <div class="card p-4 mb-4">
    <h3 class="font-semibold text-white mb-2">Version history</h3>
    <p v-if="histRows.length <= 1" class="text-slate-500 text-sm">
      Version history appears after a few daily runs.
    </p>
    <HistoryChart v-else :dates="dates" :series="series" />
  </div>
</template>

<script setup>
import { computed } from 'vue';
import Avatar from '../components/Avatar.vue';
import CountriesChart from '../components/CountriesChart.vue';
import HistoryChart from '../components/HistoryChart.vue';
import SummaryBlock from '../components/SummaryBlock.vue';
import {
  addonByName,
  buildAddonSeries,
  fmt,
  histDate,
  homePath,
  modByGamedir,
  modById,
  modPath,
  sortedValues,
  stampToDate,
} from '../lib/data.js';
import { useSort } from '../lib/useSort.js';

const props = defineProps({
  latest: { type: Object, required: true },
  histRows: { type: Array, required: true },
  name: { type: String, required: true },
});

const addon = computed(function () {
  return addonByName(props.latest.addons, props.name);
});

const modsSort = useSort('servers');
const valsSort = useSort('count');

function sortMods(k) {
  modsSort.toggle(k);
}

function modArrow(k) {
  return modsSort.arrow(k);
}

function sortVals(k) {
  valsSort.toggle(k);
}

function valArrow(k) {
  return valsSort.arrow(k);
}

const modRows = computed(function () {
  const byMod = addon.value.by_mod || {};
  return Object.keys(byMod)
    .map(function (id) {
      const entry = byMod[id] || { servers: 0 };
      const m = modByGamedir(props.latest.mods, id) || modById(props.latest.mods, id);
      return {
        id,
        servers: entry.servers || 0,
        label: m ? m.name : id,
        pct: m && m.alive ? ((100 * (entry.servers || 0)) / m.alive).toFixed(2) + '%' : 'n/a',
      };
    })
    .filter(function (row) {
      return row.servers > 0;
    });
});

const sortedModRows = computed(function () {
  return modsSort.apply(modRows.value, function (r, k) {
    return r[k];
  });
});

const valRows = computed(function () {
  return sortedValues(addon.value.values)
    .slice(0, 30)
    .map(function (kv) {
      return { value: kv[0], count: kv[1] };
    });
});

const sortedValRows = computed(function () {
  return valsSort.apply(valRows.value, function (r, k) {
    return r[k];
  });
});

  const fresh = computed(function () {
    return ((props.latest.fresh || {})[addon.value.name] || []);
  });

const dates = computed(function () {
  return props.histRows.map(histDate);
});

const series = computed(function () {
  return buildAddonSeries(addon.value, props.histRows, 5);
});

function openMod(id) {
  location.href = modPath(id);
}
</script>
