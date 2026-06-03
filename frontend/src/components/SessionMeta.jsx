// Live local date/time + best-effort city from IP-based geolocation.
//
// The geolocation lookup is non-interactive (no browser permission prompt)
// and uses ipapi.co's free unauthenticated tier. Results are cached in
// localStorage for 24h so we don't re-hit the API on every page load.
//
// If the API call fails (offline, rate-limited, blocked by ad-blocker), the
// component silently degrades to showing date + time only.

import { useEffect, useState } from 'react'
import { Clock, MapPin, CalendarDays } from 'lucide-react'

const CACHE_KEY = 'sequre_geo_v1'
const CACHE_TTL_MS = 24 * 60 * 60 * 1000  // 24 hours

function readCache() {
  try {
    const raw = localStorage.getItem(CACHE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (Date.now() - (parsed.fetched_at || 0) > CACHE_TTL_MS) return null
    return parsed.data
  } catch {
    return null
  }
}

function writeCache(data) {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({ fetched_at: Date.now(), data }))
  } catch { /* private mode etc. — ignore */ }
}

export default function SessionMeta() {
  const [now, setNow] = useState(() => new Date())
  const [geo, setGeo] = useState(() => readCache())

  // Tick the clock every second.
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  // Fetch geo once per 24h window (skip if cache is fresh).
  useEffect(() => {
    if (geo) return
    let cancelled = false
    fetch('https://ipapi.co/json/')
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(data => {
        if (cancelled) return
        const compact = {
          city: data.city || null,
          region: data.region || null,
          country_name: data.country_name || null,
          country_code: data.country_code || null,
          timezone: data.timezone || null,
        }
        writeCache(compact)
        setGeo(compact)
      })
      .catch(() => { /* silent — keep date/time only */ })
    return () => { cancelled = true }
  }, [geo])

  const timeStr = now.toLocaleTimeString('en-GB', {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
  const dateStr = now.toLocaleDateString('en-GB', {
    weekday: 'short', day: 'numeric', month: 'short', year: 'numeric',
  })
  const tz = geo?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone

  const locationLabel = geo
    ? (geo.city
        ? `${geo.city}, ${geo.country_code || geo.country_name || ''}`.trim().replace(/,\s*$/, '')
        : (geo.country_name || tz))
    : tz

  return (
    <div className="flex items-center gap-3 text-xs text-gray-400 font-mono">
      <span className="flex items-center gap-1.5">
        <Clock size={11} className="text-violet-400" />
        {timeStr}
      </span>
      <span className="text-gray-700">·</span>
      <span className="flex items-center gap-1.5">
        <CalendarDays size={11} className="text-violet-400" />
        {dateStr}
      </span>
      <span className="text-gray-700">·</span>
      <span className="flex items-center gap-1.5" title={tz}>
        <MapPin size={11} className="text-violet-400" />
        {locationLabel}
      </span>
    </div>
  )
}
