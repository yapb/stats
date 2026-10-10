<template>
  <span class="avatar" :style="style">{{ title.charAt(0) }}</span>
</template>

<script setup>
import { computed } from 'vue';
import { hue } from '../lib/data.js';

const props = defineProps({
  title: { type: String, required: true },
});

const style = computed(function () {
  return 'background:hsl(' + hue(props.title) + ',60%,65%)';
});
</script>
