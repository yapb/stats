<template>
  <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
    <div v-for="c in cards" :key="c.title" class="card p-4">
      <div class="text-slate-400 text-sm">{{ c.title }}</div>
      <div class="num text-2xl font-bold text-white">{{ fmt(c.value) }}</div>
      <div v-if="c.sub" class="text-slate-500 text-xs mt-1">{{ c.sub }}</div>
    </div>
  </div>
</template>

<script setup>
import { fmt } from '../lib/data.js';

defineProps({
  cards: { type: Array, required: true },
});
</script>
