<template>
  <div v-if="!dates.length">
    <p class="text-slate-500 text-sm">History appears after a few daily runs.</p>
  </div>
  <div v-else ref="el" style="height:280px"></div>
</template>

<script setup>
import { onMounted, watch } from 'vue';
import { baseText, useChart } from '../lib/useChart.js';

const props = defineProps({
  dates: { type: Array, required: true },
  series: { type: Array, required: true },
  dualAxis: { type: Boolean, default: false },
});

const { el, render } = useChart();

function draw() {
  if (!props.dates.length) {
    return;
  }
  render({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    textStyle: baseText(),
    legend: { textStyle: { color: '#94a3b8' } },
    xAxis: { type: 'category', data: props.dates },
    yAxis: props.dualAxis
      ? [{ type: 'value' }, { type: 'value', splitLine: { show: false } }]
      : { type: 'value' },
    series: props.series,
    grid: { left: 8, right: 24, containLabel: true },
  });
}

  onMounted(draw);
  watch(
    function () {
      return [props.dates, props.series];
    },
    draw,
    { deep: true, flush: 'post' }
  );
</script>
