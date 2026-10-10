import { onBeforeUnmount, shallowRef } from 'vue';
import * as echarts from 'echarts';

export function useChart() {
  const el = shallowRef(null);
  let chart = null;
  let observer = null;

  function onResize() {
    if (chart && el.value && el.value.offsetParent !== null) {
      chart.resize();
    }
  }

  function render(option) {
    if (!el.value) {
      return false;
    }
    if (!chart) {
      chart = echarts.init(el.value);
      if (typeof ResizeObserver !== 'undefined') {
        observer = new ResizeObserver(onResize);
        observer.observe(el.value);
      } else {
        addEventListener('resize', onResize);
      }
      requestAnimationFrame(onResize);
    }
    chart.setOption(option, true);
    return true;
  }

  function onClick(fn) {
    if (!chart) {
      return;
    }
    chart.off('click');
    chart.on('click', fn);
  }

  onBeforeUnmount(function () {
    if (observer) {
      observer.disconnect();
      observer = null;
    } else {
      removeEventListener('resize', onResize);
    }
    if (chart) {
      chart.dispose();
      chart = null;
    }
  });

  return { el, render, onClick };
}

export function baseText() {
  return { color: '#cbd5e1' };
}
