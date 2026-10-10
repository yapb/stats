<template>
  <div class="card p-4 mb-6">
    <dl class="summary grid grid-cols-2 md:grid-cols-4 gap-4">
      <div>
        <dt>Date</dt>
        <dd class="num text-xl">{{ date }}</dd>
      </div>
      <div>
        <dt>Total servers</dt>
        <dd class="num text-xl">{{ fmt(servers) }}</dd>
        <div class="text-slate-400 text-xs font-normal">having {{ fmt(maxPlayers) }} max players</div>
      </div>
      <div>
        <dt>Total players</dt>
        <dd class="num text-xl">{{ fmt(players) }}</dd>
        <div class="text-slate-400 text-xs font-normal">
          at {{ capacity(players, maxPlayers) }} capacity, {{ fmt(bots) }} bots excluded
        </div>
      </div>
      <div>
        <dt>Player/server ratio</dt>
        <dd class="num text-xl">{{ ratio(players, servers) }}</dd>
        <div class="text-slate-400 text-xs font-normal">players per server</div>
      </div>
    </dl>
  </div>
</template>

<script setup>
import { capacity, fmt, ratio } from '../lib/data.js';

defineProps({
  date: { type: String, required: true },
  servers: { type: Number, required: true },
  maxPlayers: { type: Number, required: true },
  players: { type: Number, required: true },
  bots: { type: Number, required: true },
});
</script>
