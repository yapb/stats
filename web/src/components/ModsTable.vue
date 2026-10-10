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
      <tr v-for="m in sorted" :key="m.gamedir" class="link" @click="open(m.gamedir)">
        <td>
          <span class="flex items-center gap-2">
            <CapsuleImg :appid="m.appid" />
            <a :href="'#/mod/' + m.gamedir" @click.stop>{{ m.name }}</a>
          </span>
        </td>
        <td>{{ fmt(m.alive) }}</td>
        <td class="hidden sm:table-cell">{{ fmt(m.with_rules) }}</td>
        <td v-if="ver" class="hidden sm:table-cell">{{ fmt(verCount(m.gamedir)) }}</td>
        <td>{{ fmt(m.players) }}</td>
        <td class="hidden md:table-cell">{{ fmt(m.bots) }}</td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
import { computed } from 'vue';
import CapsuleImg from './CapsuleImg.vue';
import { fmt } from '../lib/data.js';

const props = defineProps({
  mods: { type: Array, required: true },
  ver: { type: [String, null], default: null },
  verByMod: { type: Object, default: function () { return {}; } },
});

const sorted = computed(function () {
  return props.mods.slice().sort(function (a, b) {
    return b.alive - a.alive;
  });
});

function verCount(gamedir) {
  const entry = props.verByMod[gamedir] || { values: {} };
  return (entry.values || {})[props.ver] || 0;
}

function open(gamedir) {
  location.hash = '#/mod/' + gamedir;
}
</script>
