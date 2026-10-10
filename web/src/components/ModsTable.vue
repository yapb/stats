<template>
  <table class="stats w-full text-sm num">
    <thead>
      <tr>
        <th @click="toggle('name')" class="cursor-pointer select-none">Mod{{ arrow('name') }}</th>
        <th @click="toggle('alive')" class="cursor-pointer select-none">Alive{{ arrow('alive') }}</th>
        <th @click="toggle('with_rules')" class="cursor-pointer select-none hidden sm:table-cell">
          Rules{{ arrow('with_rules') }}
        </th>
        <th v-if="ver" class="hidden sm:table-cell">{{ ver }}</th>
        <th @click="toggle('players')" class="cursor-pointer select-none">Players{{ arrow('players') }}</th>
        <th @click="toggle('bots')" class="cursor-pointer select-none hidden md:table-cell">
          Bots{{ arrow('bots') }}
        </th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="m in rows" :key="modKey(m)" class="link" @click="open(modKey(m))">
        <td>
          <span class="flex items-center gap-2 min-w-0">
            <span class="hidden sm:inline shrink-0"><CapsuleImg :appid="m.appid" /></span>
            <a class="truncate max-w-[9rem] sm:max-w-none" :href="modPath(modKey(m))" @click.stop>{{
              m.name
            }}</a>
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
import { useSort } from '../lib/useSort.js';

const props = defineProps({
  mods: { type: Array, required: true },
  ver: { type: [String, null], default: null },
  verByMod: { type: Object, default: function () { return {}; } },
});

const { arrow, toggle, apply } = useSort('alive');

const rows = computed(function () {
  const alive = props.mods.filter(function (m) {
    return (m.alive || 0) > 0;
  });
  return apply(alive, function (m, k) {
    return m[k];
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
