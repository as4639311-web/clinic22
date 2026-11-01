/** "In 40 min" / "Tomorrow" / "In 3 days" for an upcoming time. */
export function relative(iso, t) {
  const ms = new Date(iso) - Date.now()
  const min = Math.round(ms / 60000)
  if (min < 60) return t('inMinutes', { n: Math.max(min, 0) })
  const h = Math.round(min / 60)
  const today = new Date(); today.setHours(0, 0, 0, 0)
  const day = new Date(iso); day.setHours(0, 0, 0, 0)
  const days = Math.round((day - today) / 86400000)
  if (days === 0) return t('inHours', { n: h })
  if (days === 1) return t('tomorrow')
  return t('inDays', { n: days })
}

export const isoDay = (d) => {
  const z = new Date(d.getTime() - d.getTimezoneOffset() * 60000)
  return z.toISOString().slice(0, 10)
}

/** .ics download so "Add to calendar" works on any device. */
export function downloadIcs({ title, start, minutes = 45, location = '' }) {
  const s = new Date(start), e = new Date(s.getTime() + minutes * 60000)
  const f = (d) => d.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '')
  const ics = [
    'BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Tawazun//Clinic//EN', 'BEGIN:VEVENT',
    `UID:${f(s)}-${Math.random().toString(36).slice(2)}@tawazun`, `DTSTAMP:${f(new Date())}`,
    `DTSTART:${f(s)}`, `DTEND:${f(e)}`, `SUMMARY:${title}`, `LOCATION:${location}`,
    'BEGIN:VALARM', 'TRIGGER:-PT1H', 'ACTION:DISPLAY', 'DESCRIPTION:Reminder', 'END:VALARM',
    'END:VEVENT', 'END:VCALENDAR',
  ].join('\r\n')
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([ics], { type: 'text/calendar' }))
  a.download = 'tawazun-appointment.ics'
  a.click()
  URL.revokeObjectURL(a.href)
}
