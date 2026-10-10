<template>
  <div ref="el" style="height:320px"></div>
</template>

<script setup>
import { onMounted, watch } from 'vue';
import { sortedValues } from '../lib/data.js';
import { baseText, useChart } from '../lib/useChart.js';

const props = defineProps({
  title: { type: String, required: true },
  values: { type: Object, required: true },
});

const { el, render } = useChart();

function draw() {
  const arr = sortedValues(props.values);
  const top = arr.slice(0, 8);
  const rest = arr.slice(8).reduce(function (acc, kv) {
    return acc + kv[1];
  }, 0);
  const data = top.map(function (kv) {
    return { name: kv[0], value: kv[1] };
  });
  if (rest > 0) {
    data.push({ name: 'other', value: rest });
  }
  if (!data.length) {
    data.push({ name: 'none seen', value: 1 });
  }
  render({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item' },
    textStyle: baseText(),
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        label: {
          formatter: '{b}  {d}%',
          fontSize: 13,
          fontWeight: 'bold',
          color: '#fff',
          textBorderColor: 'rgba(0,0,0,0.7)',
          textBorderWidth: 3,
        },
        labelLine: { show: true, length: 12, length2: 8 },
        labelLayout: { hideOverlap: true },
        minShowLabelAngle: 4,
        data,
      },
    ],
  });
}

onMounted(draw);
watch(
  function () {
    return [props.title, props.values];
  },
  draw,
  { deep: true }
);
</script>
