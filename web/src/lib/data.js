export async function loadJSON(p) {
  const r = await fetch(p, { cache: 'no-store' });
  if (!r.ok) {
    throw new Error(p + ': ' + r.status);
  }
  return r.json();
}

export function fmt(n) {
  return (n || 0).toLocaleString('en-US');
}

export function sortedValues(values) {
  const arr = Object.keys(values || {}).map(function (k) {
    return [k, values[k]];
  });
  arr.sort(function (a, b) {
    return b[1] - a[1];
  });
  return arr;
}

export function sortedAddons(addons) {
  return (addons || []).slice().sort(function (a, b) {
    const x = a.title.toLowerCase();
    const y = b.title.toLowerCase();
    if (x < y) {
      return -1;
    }
    return x > y ? 1 : 0;
  });
}

export function addonByName(addons, name) {
  for (const a of addons) {
    if (a.name === name) {
      return a;
    }
  }
  return addons[0];
}

export function modById(mods, id) {
  for (const m of mods) {
    if (String(m.appid) === String(id)) {
      return m;
    }
  }
  return null;
}

export function capacity(players, max) {
  return max > 0 ? ((100 * players) / max).toFixed(2) + '%' : 'n/a';
}

export function ratio(players, servers) {
  return servers > 0 ? (players / servers).toFixed(2) : 'n/a';
}

export function hue(name) {
  let h = 0;
  for (let i = 0; i < name.length; i++) {
    h = (h * 31 + name.charCodeAt(i)) % 360;
  }
  return h;
}

export function capsuleUrl(appid) {
  return 'https://cdn.cloudflare.steamstatic.com/steam/apps/' + appid + '/capsule_184x69.jpg';
}

export function stampToDate(stamp) {
  return (stamp || '?').replace('T', ' ').replace('+00:00', ' UTC');
}

export function histDate(r) {
  return r.ts || r.date;
}

export function buildOverviewSeries(latest, histRows, ver) {
  const series = [
    {
      name: 'alive',
      type: 'line',
      smooth: true,
      data: histRows.map(function (r) {
        return r.alive || 0;
      }),
    },
    {
      name: 'with rules',
      type: 'line',
      smooth: true,
      data: histRows.map(function (r) {
        return r.with_rules || 0;
      }),
    },
  ];
  for (const a of latest.addons) {
    series.push({
      name: a.title,
      type: 'line',
      smooth: true,
      yAxisIndex: 1,
      data: histRows.map(function (r) {
        return r['addon:' + a.name] || 0;
      }),
    });
  }
  return series;
}

export function buildAddonSeries(addon, histRows, topN) {
  const series = [
    {
      name: 'total',
      type: 'line',
      smooth: true,
      lineStyle: { width: 3 },
      data: histRows.map(function (r) {
        return r['addon:' + addon.name] || 0;
      }),
    },
  ];
  const topVers = sortedValues(addon.values).slice(0, topN).map(function (kv) {
    return kv[0];
  });
  for (const v of topVers) {
    series.push({
      name: v,
      type: 'line',
      smooth: true,
      data: histRows.map(function (r) {
        return (((r.addon_versions || {})[addon.name] || {})[v] || 0);
      }),
    });
  }
  return series;
}

export function buildModSeries(histRows, appid) {
  const at = function (r, field) {
    return (((r.mods || {})[String(appid)] || {})[field] || 0);
  };
  return [
    {
      name: 'alive',
      type: 'line',
      smooth: true,
      data: histRows.map(function (r) {
        return at(r, 'alive');
      }),
    },
    {
      name: 'with rules',
      type: 'line',
      smooth: true,
      data: histRows.map(function (r) {
        return at(r, 'rules');
      }),
    },
  ];
}
