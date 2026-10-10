<template>
  <div v-if="!rows.length" class="text-sm">
    <p class="text-slate-500">Nothing seen in this scope yet.</p>
  </div>
  <div v-else class="text-sm">
    <div
      v-for="row in rows"
      :key="row.value"
      class="vrow"
      :class="{ active: row.value === selected }"
      @click="$emit('select', row.value)"
    >
      <div class="vname num" style="width:38%">
        {{ row.value }}
        <span
          v-if="fresh.includes(row.value)"
          class="ml-1 text-[10px] font-bold text-black bg-lime-300 rounded px-1"
        >NEW</span>
      </div>
      <div style="flex:1">
        <div class="vbar" :style="{ width: Math.max(2, (100 * row.count) / max) + '%' }"></div>
      </div>
      <div class="num text-slate-300" style="width:4.5rem;text-align:right">{{ fmt(row.count) }}</div>
      <div class="num text-slate-500" style="width:3.5rem;text-align:right">{{ row.pct }}%</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { fmt, sortedValues } from '../lib/data.js';

const props = defineProps({
  values: { type: Object, required: true },
  readable: { type: Number, required: true },
  selected: { type: [String, null], default: null },
  fresh: { type: Array, default: function () { return []; } },
});

defineEmits(['select']);

const rows = computed(function () {
  return sortedValues(props.values)
    .slice(0, 15)
    .map(function (kv) {
      return {
        value: kv[0],
        count: kv[1],
        pct: props.readable ? ((100 * kv[1]) / props.readable).toFixed(1) : '0.0',
      };
    });
});

const max = computed(function () {
  return rows.value.length ? rows.value[0].count : 1;
});
</script>
