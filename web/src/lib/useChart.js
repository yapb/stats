import { onBeforeUnmount, shallowRef } from 'vue';
import * as echarts from 'echarts';

export function useChart() {
  const el = shallowRef(null);
  let chart = null;

  function onResize() {
    if (chart && el.value && el.value.offsetParent !== null) {
      chart.resize();
    }
  }

  function render(option) {
    if (!el.value) {
      return;
    }
    if (!chart) {
      chart = echarts.init(el.value);
      addEventListener('resize', onResize);
    }
    chart.setOption(option, true);
  }

  onBeforeUnmount(function () {
    removeEventListener('resize', onResize);
    if (chart) {
      chart.dispose();
      chart = null;
    }
  });

  return { el, render };
}

export function baseText() {
  return { color: '#cbd5e1' };
}
