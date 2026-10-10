<template>
  <img
    class="capsule"
    width="92"
    height="35"
    loading="lazy"
    alt=""
    :src="src"
    @error="hidden = true"
    v-show="!hidden"
  >
</template>

<script setup>
import { computed, ref } from 'vue';
import { capsuleUrl } from '../lib/data.js';

const props = defineProps({
  appid: { type: [Number, String], required: true },
});

const hidden = ref(false);
const src = computed(function () {
  return capsuleUrl(props.appid);
});
</script>
