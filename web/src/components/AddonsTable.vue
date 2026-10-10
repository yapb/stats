<template>
  <table class="stats w-full text-sm num">
    <thead>
      <tr>
        <th>Addon</th>
        <th>Servers</th>
        <th class="hidden sm:table-cell">Top values</th>
      </tr>
    </thead>
    <tbody>
      <tr
        v-for="a in byCount"
        :key="a.name"
        :class="a.name === active ? 'active link' : 'link'"
        @click="inspect(a, $event)"
      >
        <td>
          <span class="flex items-center gap-2">
            <Avatar :title="a.title" />
            <span>
              <a :href="'#/addon/' + a.name" @click.stop>{{ a.title }}</a>
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
import { fmt, sortedValues } from '../lib/data.js';

const props = defineProps({
  addons: { type: Array, required: true },
  active: { type: String, required: true },
});

const emit = defineEmits(['inspect']);

const byCount = computed(function () {
  return props.addons.slice().sort(function (a, b) {
    return b.servers - a.servers || (a.title < b.title ? -1 : 1);
  });
});

function topValues(a) {
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
