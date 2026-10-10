<template>
  <table class="stats w-full text-sm num">
    <thead>
      <tr>
        <th @click="toggle('title')" class="cursor-pointer select-none">Addon{{ arrow('title') }}</th>
        <th @click="toggle('servers')" class="cursor-pointer select-none">Servers{{ arrow('servers') }}</th>
        <th class="hidden sm:table-cell">Top values</th>
      </tr>
    </thead>
    <tbody>
      <tr
        v-for="a in rows"
        :key="a.name"
        :class="a.name === active ? 'active link' : 'link'"
        @click="inspect(a, $event)"
      >
        <td>
          <span class="flex items-center gap-2">
            <Avatar :title="a.title" />
            <span>
              <a :href="addonPath(a.name)" @click.stop>{{ a.title }}</a>
              <br>
              <span class="text-slate-500 text-xs">{{ a.name }}</span>
            </span>
          </span>
        </td>
        <td>{{ fmt(a.servers) }}</td>
        <td class="hidden sm:table-cell">{{ topValues(a) }}</td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
import { computed } from 'vue';
import Avatar from './Avatar.vue';
import { addonPath, fmt, sortedValues } from '../lib/data.js';
import { useSort } from '../lib/useSort.js';

const props = defineProps({
  addons: { type: Array, required: true },
  active: { type: String, required: true },
});

const emit = defineEmits(['inspect']);

const { arrow, toggle, apply } = useSort('servers');

const rows = computed(function () {
  return apply(props.addons, function (a, k) {
    return k === 'title' ? a.title : a.servers;
  });
});

function topValues(a) {
  if (a.novalue) {
    return 'presence only';
  }
  const top = sortedValues(a.values || {})
    .slice(0, 4)
    .map(function (kv) {
      return kv[0] + ' (' + fmt(kv[1]) + ')';
    })
    .join(', ');
  return top || 'none yet';
}

function inspect(a, ev) {
  if (ev.target.tagName === 'A') {
    return;
  }
  emit('inspect', a.name);
}
</script>
