<template>
  <div v-if="!rows.length">
    <p class="text-slate-500 text-sm">Country data appears with the next census.</p>
  </div>
  <div v-else ref="el" :style="{ height: height + 'px' }"></div>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue';
import { baseText, useChart } from '../lib/useChart.js';
import { flag, hue } from '../lib/data.js';

const props = defineProps({
  countries: { type: Array, required: true },
});

const { el, render, onClick } = useChart();

const rows = computed(function () {
  return (props.countries || []).slice(0, 12);
});

const height = computed(function () {
  return Math.max(300, (rows.value.length + 1) * 30);
});

const emit = defineEmits(['pick']);

function draw() {
  if (!rows.value.length) {
    return;
  }
  const items = rows.value.map(function (c) {
    return { cc: c.cc, name: c.name, servers: c.servers };
  });
  const rest = (props.countries || [])
    .slice(12)
    .reduce(function (acc, c) {
      return acc + c.servers;
    }, 0);
  if (rest > 0) {
    items.push({ cc: null, name: 'other', servers: rest });
  }
  const names = items.map(function (c) {
    const mark = flag(c.cc);
    return (mark ? mark + ' ' : '') + c.name;
  });
  const data = items.map(function (c) {
    const color = c.cc ? 'hsl(' + hue(c.cc) + ',60%,55%)' : '#475569';
    return { value: c.servers, itemStyle: { color } };
  });
  render({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    textStyle: baseText(),
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: names, inverse: true },
    series: [
      {
        type: 'bar',
        data,
        label: { show: true, position: 'right', color: '#94a3b8' },
      },
    ],
    grid: { left: 8, right: 48, containLabel: true },
  });
  onClick(function (params) {
    const item = items[params.dataIndex];
    if (item && item.cc) {
      emit('pick', item.cc);
    }
  });
}

onMounted(draw);
watch(
  function () {
    return props.countries;
  },
  draw,
  { deep: true }
);
</script>
