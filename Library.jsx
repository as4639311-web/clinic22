import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { FileText, Lightbulb, PlayCircle, Search } from 'lucide-react'
import { useApp, useData } from '../state'
import { Chevron, Empty, ErrorBox, ServiceIcon, Spinner, TopBar } from '../components/ui'

const SERVICES = ['mental', 'fitness', 'sports_medicine', 'nutrition', 'education']
const TYPE_ICON = { article: FileText, video: PlayCircle, tip: Lightbulb }

export function Library() {
  const { t, pick } = useApp()
  const [service, setService] = useState('')
  const [q, setQ] = useState('')
  const params = new URLSearchParams({ ...(service && { service }), ...(q && { q }) })
  const { data, loading, error, reload } = useData(`/content?${params}`, [service, q])
  return (
    <>
      <TopBar title={t('library')} back />
      <div className="page">
        <label className="field" style={{ position: 'relative' }}>
          <span className="sr-only">{t('search')}</span>
          <Search size={20} className="muted" style={{ position: 'absolute', insetInlineStart: 14, insetBlockStart: 14 }} />
          <input className="input" type="search" placeholder={t('search')} value={q} onChange={(e) => setQ(e.target.value)} style={{ paddingInlineStart: 44 }} />
        </label>
        <div className="chips">
          <button className="chip" aria-pressed={!service} onClick={() => setService('')}>{t('all')}</button>
          {SERVICES.map((s) => <button key={s} className="chip" aria-pressed={service === s} onClick={() => setService(s)}>{t(`svc_${s}`)}</button>)}
        </div>
        {loading ? <Spinner /> : error ? <ErrorBox error={error} onRetry={reload} /> : !data.length ? <Empty icon={Search} text={t('noResults')} /> : (
          <div className="list">
            {data.map((c) => {
              const Icon = TYPE_ICON[c.type]
              return (
                <Link key={c.id} to={`/library/${c.id}`} className="row">
                  <ServiceIcon service={c.service} />
                  <span className="grow">
                    <span className="title">{pick(c.title)}</span><br />
                    <span className="muted small">{pick(c.summary)}</span><br />
                    <span className="small muted" style={{ display: 'inline-flex', gap: 4, alignItems: 'center' }}><Icon size={14} />{t(`t_${c.type}`)} · {t('readMin', { n: c.minutes })}</span>
                  </span>
                  <Chevron />
                </Link>
              )
            })}
          </div>
        )}
      </div>
    </>
  )
}

export function Article() {
  const { id } = useParams()
  const { t, pick } = useApp()
  const { data, loading, error, reload } = useData(`/content/${id}`)
  if (loading) return <><TopBar title="" back /><Spinner /></>
  if (error) return <><TopBar title="" back /><ErrorBox error={error} onRetry={reload} /></>
  return (
    <>
      <TopBar title={t(`svc_${data.service}`)} back />
      <article className="page" style={{ maxWidth: '68ch' }}>
        <span className="badge">{t(`t_${data.type}`)} · {t('readMin', { n: data.minutes })}</span>
        <h1>{pick(data.title)}</h1>
        {data.type === 'video' && (
          <div className="panel center" style={{ minBlockSize: 200, background: 'var(--surface-2)' }}><PlayCircle size={56} color="var(--primary)" /></div>
        )}
        {pick(data.body).split('\n\n').map((para, i) => <p key={i} style={{ fontSize: '1.0625rem', lineHeight: 1.8 }}>{para}</p>)}
        <Link to={`/book?service=${data.service}`} className="btn btn-primary">{t('bookNow')}</Link>
      </article>
    </>
  )
}
