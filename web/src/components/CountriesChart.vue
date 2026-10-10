<template>
  <div v-if="!rows.length">
    <p class="text-slate-500 text-sm">Country data appears with the next census.</p>
  </div>
  <div v-else ref="el" style="height:340px"></div>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue';
import { baseText, useChart } from '../lib/useChart.js';

const props = defineProps({
  countries: { type: Array, required: true },
});

const { el, render } = useChart();

const rows = computed(function () {
  return (props.countries || []).slice(0, 15);
});

function draw() {
  if (!rows.value.length) {
    return;
  }
  const rest = (props.countries || [])
    .slice(15)
    .reduce(function (acc, c) {
      return acc + c.servers;
    }, 0);
  const names = rows.value.map(function (c) {
    return c.name + ' (' + c.cc + ')';
  });
  const data = rows.value.map(function (c) {
    return c.servers;
  });
  if (rest > 0) {
    names.push('other');
    data.push(rest);
  }
  render({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    textStyle: baseText(),
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: names.reverse() },
    series: [
      {
        type: 'bar',
        data: data.reverse(),
        label: { show: true, position: 'right', color: '#94a3b8' },
        itemStyle: { color: '#38bdf8' },
      },
    ],
    grid: { left: 8, right: 48, containLabel: true },
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
