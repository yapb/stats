<template>
  <table class="stats w-full text-sm num">
    <thead>
      <tr>
        <th>Mod</th>
        <th>Alive</th>
        <th class="hidden sm:table-cell">Rules</th>
        <th v-if="ver" class="hidden sm:table-cell">{{ ver }}</th>
        <th>Players</th>
        <th class="hidden md:table-cell">Bots</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="m in sorted" :key="modKey(m)" class="link" @click="open(modKey(m))">
        <td>
          <span class="flex items-center gap-2 min-w-0">
            <span class="hidden sm:inline shrink-0"><CapsuleImg :appid="m.appid" /></span>
            <a class="truncate max-w-[9rem] sm:max-w-none" :href="modPath(modKey(m))" @click.stop>{{ m.name }}</a>
          </span>
        </td>
        <td>{{ fmt(m.alive) }}</td>
        <td class="hidden sm:table-cell">{{ fmt(m.with_rules) }}</td>
        <td v-if="ver" class="hidden sm:table-cell">{{ fmt(verCount(m)) }}</td>
        <td>{{ fmt(m.players) }}</td>
        <td class="hidden md:table-cell">{{ fmt(m.bots) }}</td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
import { computed } from 'vue';
import CapsuleImg from './CapsuleImg.vue';
import { fmt, modPath } from '../lib/data.js';

const props = defineProps({
  mods: { type: Array, required: true },
  ver: { type: [String, null], default: null },
  verByMod: { type: Object, default: function () { return {}; } },
});

const sorted = computed(function () {
  return props.mods
    .filter(function (m) {
      return (m.alive || 0) > 0;
    })
    .sort(function (a, b) {
      return b.alive - a.alive;
    });
});

function verCount(m) {
  const byMod = props.verByMod;
  const entry = byMod[m.gamedir] || byMod[String(m.appid)] || { values: {} };
  return (entry.values || {})[props.ver] || 0;
}

function modKey(m) {
  return m.gamedir || String(m.appid);
}

function open(key) {
  location.href = modPath(key);
}
</script>
