<template>
  <div v-if="!mod">
    <div class="crumb mb-2"><a href="#/">Overview</a> / unknown mod</div>
    <p class="text-slate-400">Mod not found. <a href="#/">Back to overview</a>.</p>
  </div>
  <div v-else>
    <div class="crumb mb-2"><a href="#/">Overview</a> / {{ mod.name }}</div>

    <div class="flex items-center gap-3 mb-4">
      <CapsuleImg :appid="mod.appid" />
      <div>
        <h2 class="text-2xl font-bold text-white">Statistics for mod: {{ mod.name }}</h2>
        <div v-if="mod.url" class="text-slate-400 text-sm">
          <a :href="mod.url">{{ mod.url }}</a>
        </div>
      </div>
    </div>

    <SummaryBlock
      :date="stampToDate(latest.generated_at)"
      :servers="mod.alive || 0"
      :max-players="mod.max_players || 0"
      :players="mod.players || 0"
      :bots="mod.bots || 0"
    />

    <div class="card p-4 mb-4 overflow-x-auto">
      <h3 class="font-semibold text-white mb-2">Addons on this mod</h3>
      <table class="stats w-full text-sm num">
        <thead>
          <tr>
            <th>Addon</th>
            <th>Servers</th>
            <th>% of mod</th>
            <th class="hidden sm:table-cell">Top values</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!rows.length">
            <td colspan="4" class="text-slate-500">Nothing seen yet.</td>
          </tr>
          <tr v-for="row in rows" :key="row.name" class="link" @click="openAddon(row.name)">
            <td>
              <span class="flex items-center gap-2">
                <Avatar :title="row.title" />
                <a :href="'#/addon/' + row.name" @click.stop>{{ row.title }}</a>
              </span>
            </td>
            <td>{{ fmt(row.servers) }}</td>
            <td>{{ row.pct }}</td>
            <td class="hidden sm:table-cell">{{ row.top }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="card p-4 mb-4">
      <h3 class="font-semibold text-white mb-2">Mod history</h3>
      <p v-if="histRows.length <= 1" class="text-slate-500 text-sm">
        Mod history appears after a few daily runs.
      </p>
      <HistoryChart v-else :dates="dates" :series="series" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import Avatar from '../components/Avatar.vue';
import CapsuleImg from '../components/CapsuleImg.vue';
import HistoryChart from '../components/HistoryChart.vue';
import SummaryBlock from '../components/SummaryBlock.vue';
import {
  buildModSeries,
  fmt,
  histDate,
  modByGamedir,
  sortedAddons,
  sortedValues,
  stampToDate,
} from '../lib/data.js';

const props = defineProps({
  latest: { type: Object, required: true },
  histRows: { type: Array, required: true },
  gamedir: { type: String, required: true },
});

const mod = computed(function () {
  return modByGamedir(props.latest.mods, props.gamedir);
});

const rows = computed(function () {
  if (!mod.value) {
    return [];
  }
  const out = [];
  for (const a of sortedAddons(props.latest.addons)) {
    const entry = ((a.by_mod || {})[mod.value.gamedir] || { servers: 0, values: {} });
    if (!entry.servers) {
      continue;
    }
    const top = sortedValues(entry.values || {})
      .slice(0, 3)
      .map(function (kv) {
        return kv[0] + ' (' + fmt(kv[1]) + ')';
      })
      .join(', ');
    out.push({
      name: a.name,
      title: a.title,
      servers: entry.servers,
      pct: mod.value.alive ? ((100 * entry.servers) / mod.value.alive).toFixed(2) + '%' : 'n/a',
      top,
    });
  }
  return out;
});

const dates = computed(function () {
  return props.histRows.map(histDate);
});

const series = computed(function () {
  return buildModSeries(props.histRows, mod.value ? mod.value.gamedir : '', mod.value ? mod.value.appid : 0);
});

function openAddon(name) {
  location.hash = '#/addon/' + name;
}
</script>
