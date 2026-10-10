<template>
  <div v-if="!entry">
    <div class="crumb mb-2"><a :href="homePath()">Overview</a> / unknown country</div>
    <p class="text-slate-400">Country not found. <a :href="homePath()">Back to overview</a>.</p>
  </div>
  <div v-else>
    <div class="crumb mb-2">
      <a :href="homePath()">Overview</a> / {{ entry.name }} ({{ cc }})
    </div>

    <div class="flex items-center gap-3 mb-4">
      <span class="text-3xl">{{ flag(cc) }}</span>
      <div>
        <h2 class="text-2xl font-bold text-white">Statistics for country: {{ entry.name }}</h2>
        <div class="text-slate-400 text-sm">{{ entry.servers }} servers in census</div>
      </div>
    </div>

    <SummaryBlock
      :date="stampToDate(latest.generated_at)"
      :servers="entry.servers || 0"
      :max-players="entry.max_players || 0"
      :players="entry.players || 0"
      :bots="entry.bots || 0"
    />

    <div class="grid md:grid-cols-2 gap-4 mb-6">
      <div class="card p-4 overflow-x-auto">
        <h3 class="font-semibold text-white mb-2">Mods in {{ entry.name }}</h3>
        <table class="stats w-full text-sm num">
          <thead>
            <tr>
              <th @click="sortMods('label')" class="cursor-pointer select-none">
                Mod{{ modArrow('label') }}
              </th>
              <th @click="sortMods('servers')" class="cursor-pointer select-none">
                Servers{{ modArrow('servers') }}
              </th>
              <th>% of country</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!sortedModRows.length">
              <td colspan="3" class="text-slate-500">Nothing seen yet.</td>
            </tr>
            <tr
              v-for="row in sortedModRows"
              :key="row.gamedir"
              class="link"
              @click="openMod(row.gamedir)"
            >
              <td>
                <a :href="modPath(row.gamedir)" @click.stop>{{ row.label }}</a>
              </td>
              <td>{{ fmt(row.servers) }}</td>
              <td>{{ row.pct }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="card p-4 overflow-x-auto">
        <h3 class="font-semibold text-white mb-2">Addons in {{ entry.name }}</h3>
        <table class="stats w-full text-sm num">
          <thead>
            <tr>
              <th @click="sortAddons('title')" class="cursor-pointer select-none">
                Addon{{ addonArrow('title') }}
              </th>
              <th @click="sortAddons('servers')" class="cursor-pointer select-none">
                Servers{{ addonArrow('servers') }}
              </th>
              <th>% of country</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!sortedAddonRows.length">
              <td colspan="3" class="text-slate-500">Nothing seen yet.</td>
            </tr>
            <tr
              v-for="row in sortedAddonRows"
              :key="row.name"
              class="link"
              @click="openAddon(row.name)"
            >
              <td>
                <a :href="addonPath(row.name)" @click.stop>{{ row.title }}</a>
              </td>
              <td>{{ fmt(row.servers) }}</td>
              <td>{{ row.pct }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import SummaryBlock from '../components/SummaryBlock.vue';
import {
  addonByName,
  addonPath,
  fmt,
  homePath,
  flag,
  modByGamedir,
  modPath,
  stampToDate,
} from '../lib/data.js';
import { useSort } from '../lib/useSort.js';

const props = defineProps({
  latest: { type: Object, required: true },
  cc: { type: String, required: true },
});

const entry = computed(function () {
  const all = props.latest.by_country || {};
  return all[props.cc] || all[props.cc.toUpperCase()] || null;
});

const modsSort = useSort('servers');
const addonsSort = useSort('servers');

function sortMods(k) {
  modsSort.toggle(k);
}

function modArrow(k) {
  return modsSort.arrow(k);
}

function sortAddons(k) {
  addonsSort.toggle(k);
}

function addonArrow(k) {
  return addonsSort.arrow(k);
}

const modRows = computed(function () {
  if (!entry.value) {
    return [];
  }
  return Object.keys(entry.value.mods || {})
    .map(function (gamedir) {
      const m = modByGamedir(props.latest.mods, gamedir);
      return {
        gamedir,
        label: m ? m.name : gamedir,
        servers: entry.value.mods[gamedir] || 0,
        pct: entry.value.servers
          ? ((100 * (entry.value.mods[gamedir] || 0)) / entry.value.servers).toFixed(1) + '%'
          : 'n/a',
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

const addonRows = computed(function () {
  if (!entry.value) {
    return [];
  }
  return Object.keys(entry.value.addons || {})
    .map(function (name) {
      const a = addonByName(props.latest.addons, name);
      return {
        name,
        title: a ? a.title : name,
        servers: entry.value.addons[name] || 0,
        pct: entry.value.servers
          ? ((100 * (entry.value.addons[name] || 0)) / entry.value.servers).toFixed(1) + '%'
          : 'n/a',
      };
    })
    .filter(function (row) {
      return row.servers > 0;
    });
});

const sortedAddonRows = computed(function () {
  return addonsSort.apply(addonRows.value, function (r, k) {
    return r[k];
  });
});

function openMod(gamedir) {
  location.href = modPath(gamedir);
}

function openAddon(name) {
  location.href = addonPath(name);
}
</script>
