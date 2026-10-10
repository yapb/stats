<template>
  <SummaryBlock
    :date="stampToDate(latest.generated_at)"
    :servers="latest.totals.alive"
    :max-players="latest.totals.max_players"
    :players="totalPlayers"
    :bots="totalBots"
  />

  <StatCards :cards="cards" />

  <div class="grid md:grid-cols-2 gap-4 mb-6">
    <div class="card p-4">
      <h2 class="font-semibold text-white mb-2">Game mods</h2>
      <div class="scroll10 overflow-x-auto">
        <ModsTable :mods="latest.mods" :ver="ver" :ver-by-mod="verByMod" />
      </div>
    </div>
    <div class="card p-4">
      <h2 class="font-semibold text-white mb-2">Addons (click a row to inspect)</h2>
      <div class="scroll10 overflow-x-auto">
        <AddonsTable :addons="latest.addons" :active="addonName" @inspect="inspect" />
      </div>
    </div>
  </div>

  <div class="grid md:grid-cols-2 gap-4 mb-6">
    <div class="card p-4">
      <h2 class="font-semibold text-white mb-2">Unlisted mods (open a PR to track)</h2>
      <div class="scroll10 overflow-x-auto">
        <table class="stats w-full text-sm num">
          <thead>
            <tr>
              <th>Directory</th>
              <th>Servers</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!unlisted.length">
              <td colspan="2" class="text-slate-500">None seen.</td>
            </tr>
            <tr v-for="row in unlisted" :key="row.gamedir">
              <td>{{ row.gamedir }}</td>
              <td>{{ fmt(row.servers) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div class="card p-4">
      <h2 class="font-semibold text-white mb-2">Untracked version cvars (open a PR to track)</h2>
      <div class="scroll10 overflow-x-auto">
        <table class="stats w-full text-sm num">
          <thead>
            <tr>
              <th>Cvar</th>
              <th>Servers</th>
              <th>Example</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!unlistedVars.length">
              <td colspan="3" class="text-slate-500">None seen.</td>
            </tr>
            <tr v-for="row in unlistedVars" :key="row.var">
              <td>{{ row.var }}</td>
              <td>{{ fmt(row.servers) }}</td>
              <td class="text-slate-400">{{ row.example }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <div class="grid md:grid-cols-2 gap-4 mb-6">
    <div class="card p-4">
      <h2 class="font-semibold text-white mb-2">{{ addon.title }}: version share</h2>
      <VersionPie :title="addon.title" :values="addon.values" />
    </div>
    <div class="card p-4">
      <h2 class="font-semibold text-white mb-2">
        {{ addon.title }}: top values ({{ addon.name }}, click to filter)
      </h2>
      <ValuesBars
        :values="addon.values"
        :readable="latest.totals.with_rules"
        :selected="ver"
        :fresh="(latest.fresh || {})[addon.name] || []"
        @select="toggleVer"
      />
    </div>
  </div>

  <div class="card p-4 mb-6">
    <h2 class="font-semibold text-white mb-2">Servers by country</h2>
    <CountriesChart :countries="latest.countries" />
  </div>

  <div class="card p-4 mb-6">
    <h2 class="font-semibold text-white mb-2">History</h2>
    <HistoryChart :dates="dates" :series="series" :dual-axis="true" />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import AddonsTable from '../components/AddonsTable.vue';
import CountriesChart from '../components/CountriesChart.vue';
import HistoryChart from '../components/HistoryChart.vue';
import ModsTable from '../components/ModsTable.vue';
import StatCards from '../components/StatCards.vue';
import SummaryBlock from '../components/SummaryBlock.vue';
import ValuesBars from '../components/ValuesBars.vue';
import VersionPie from '../components/VersionPie.vue';
import {
  addonByName,
  buildOverviewSeries,
  fmt,
  histDate,
  stampToDate,
} from '../lib/data.js';

const props = defineProps({
  latest: { type: Object, required: true },
  histRows: { type: Array, required: true },
});

const names = computed(function () {
  return props.latest.addons.map(function (a) {
    return a.name;
  });
});

const addonName = ref(names.value.includes('yb_version') ? 'yb_version' : names.value[0]);
const ver = ref(null);

const unlisted = computed(function () {
  return props.latest.unlisted_mods || [];
});

const unlistedVars = computed(function () {
  return props.latest.unlisted_vars || [];
});

const addon = computed(function () {
  return addonByName(props.latest.addons, addonName.value);
});

const verByMod = computed(function () {
  return addon.value.by_mod || {};
});

const totalPlayers = computed(function () {
  return props.latest.mods.reduce(function (acc, m) {
    return acc + (m.players || 0);
  }, 0);
});

const totalBots = computed(function () {
  return props.latest.mods.reduce(function (acc, m) {
    return acc + (m.bots || 0);
  }, 0);
});

const cards = computed(function () {
  const t = props.latest.totals;
  const vals = addon.value.values || {};
  const count = ver.value ? vals[ver.value] || 0 : addon.value.servers || 0;
  const title = ver.value ? addon.value.title + ' ' + ver.value : addon.value.title + ' servers';
  const pct = t.with_rules ? ((100 * count) / t.with_rules).toFixed(1) + '% of readable' : '';
  return [
    { title: 'Servers alive (A2S)', value: t.alive, sub: fmt(t.master) + ' in master list' },
    {
      title: 'Answering rules',
      value: t.with_rules,
      sub: fmt(t.rules_unknown) + ' firewalled / unknown',
    },
    { title, value: count, sub: pct },
    { title: 'Players online', value: totalPlayers.value, sub: fmt(totalBots.value) + ' bots' },
  ];
});

const dates = computed(function () {
  return props.histRows.map(histDate);
});

const series = computed(function () {
  const base = buildOverviewSeries(props.latest, props.histRows);
  if (ver.value) {
    base.push({
      name: addon.value.title + ' ' + ver.value,
      type: 'line',
      smooth: true,
      yAxisIndex: 1,
      lineStyle: { width: 3 },
      itemStyle: { color: '#9ece6a' },
      data: props.histRows.map(function (r) {
        return (((r.addon_versions || {})[addon.value.name] || {})[ver.value] || 0);
      }),
    });
  }
  return base;
});

function inspect(name) {
  addonName.value = name;
  ver.value = null;
}

function toggleVer(value) {
  ver.value = ver.value === value ? null : value;
}
</script>
