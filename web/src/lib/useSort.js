import { ref } from 'vue';

function cmp(a, b) {
  if (typeof a === 'number' && typeof b === 'number') {
    return a - b;
  }
  const sa = String(a == null ? '' : a).toLowerCase();
  const sb = String(b == null ? '' : b).toLowerCase();
  if (sa < sb) {
    return -1;
  }
  if (sa > sb) {
    return 1;
  }
  return 0;
}

export function useSort(defaultKey) {
  const key = ref(defaultKey);
  const dir = ref(-1);

  function arrow(k) {
    if (key.value !== k) {
      return '';
    }
    return dir.value === -1 ? ' ↓' : ' ↑';
  }

  function toggle(k) {
    if (key.value === k) {
      dir.value = -dir.value;
    } else {
      key.value = k;
      dir.value = -1;
    }
  }

  function apply(rows, get) {
    return rows.slice().sort(function (x, y) {
      return cmp(get(x, key.value), get(y, key.value)) * dir.value;
    });
  }

  return { arrow, toggle, apply };
}
