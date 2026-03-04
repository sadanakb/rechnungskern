'use client'

import { Suspense, useState, useEffect, useCallback } from 'react'
import { useForm, useFieldArray, useWatch } from 'react-hook-form'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Plus,
  Trash2,
  Loader2,
  CheckCircle,
  AlertCircle,
  FileText,
  X,
  ArrowLeft,
  Users,
} from 'lucide-react'
import {
  createQuote,
  updateQuote,
  getQuote,
  getErrorMessage,
  listContacts,
  type QuoteCreate,
  type Contact,
} from '@/lib/api'
import { toast } from '@/components/ui/toast'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface QuoteLineItem {
  description: string
  quantity: number
  unit_price: number
  net_amount: number
  tax_rate: number
}

interface FormData {
  quote_date: string
  valid_until: string
  seller_name: string
  seller_vat_id: string
  seller_address: string
  buyer_name: string
  buyer_vat_id: string
  buyer_address: string
  tax_rate: number
  line_items: QuoteLineItem[]
  intro_text: string
  closing_text: string
  internal_notes: string
  iban: string
  bic: string
  payment_account_name: string
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function calcTotals(
  lineItems: { quantity?: number; unit_price?: number }[],
  taxRate: number,
) {
  const net = lineItems.reduce((sum, item) => {
    return sum + (Number(item.quantity) || 0) * (Number(item.unit_price) || 0)
  }, 0)
  const tax = net * (taxRate / 100)
  const gross = net + tax
  return { net, tax, gross }
}

function getDefaultDate(): string {
  return new Date().toISOString().split('T')[0]
}

function getDefault30Days(): string {
  const d = new Date()
  d.setDate(d.getDate() + 30)
  return d.toISOString().split('T')[0]
}

const sectionVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, ease: 'easeOut' as const, delay: i * 0.06 },
  }),
}

// ---------------------------------------------------------------------------
// Section component
// ---------------------------------------------------------------------------
function Section({
  title,
  icon,
  info,
  children,
}: {
  title: string
  icon?: React.ReactNode
  info?: string
  children: React.ReactNode
}) {
  return (
    <div
      className="rounded-xl border p-5"
      style={{
        backgroundColor: 'rgb(var(--card))',
        borderColor: 'rgb(var(--border))',
      }}
    >
      <div className="flex items-center gap-2 mb-4">
        {icon && (
          <span style={{ color: 'rgb(var(--primary))' }}>{icon}</span>
        )}
        <h2 className="text-sm font-semibold" style={{ color: 'rgb(var(--foreground))' }}>
          {title}
        </h2>
      </div>
      {info && (
        <p className="text-xs leading-relaxed mb-4" style={{ color: 'rgb(var(--foreground-muted))' }}>
          {info}
        </p>
      )}
      {children}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------
function QuoteFormContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const editId = searchParams.get('edit')

  const [loading, setLoading] = useState(false)
  const [loadingEdit, setLoadingEdit] = useState(!!editId)
  const [success, setSuccess] = useState<{ quoteId: string } | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)
  const [contacts, setContacts] = useState<Contact[]>([])
  const [showContactPicker, setShowContactPicker] = useState(false)

  const {
    register,
    control,
    handleSubmit,
    setValue,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    mode: 'onBlur',
    defaultValues: {
      quote_date: getDefaultDate(),
      valid_until: getDefault30Days(),
      seller_name: '',
      seller_vat_id: '',
      seller_address: '',
      buyer_name: '',
      buyer_vat_id: '',
      buyer_address: '',
      tax_rate: 19,
      line_items: [{ description: '', quantity: 1, unit_price: 0, net_amount: 0, tax_rate: 19 }],
      intro_text: '',
      closing_text: '',
      internal_notes: '',
      iban: '',
      bic: '',
      payment_account_name: '',
    },
  })

  const { fields, append, remove } = useFieldArray({ control, name: 'line_items' })

  const watchedItems = useWatch({ control, name: 'line_items' }) ?? []
  const watchedTaxRate = useWatch({ control, name: 'tax_rate' }) ?? 19
  const { net, tax, gross } = calcTotals(watchedItems, watchedTaxRate)

  // Load contacts for picker
  useEffect(() => {
    listContacts({ type: 'customer' })
      .then(setContacts)
      .catch(() => {})
  }, [])

  // Load existing quote data for editing
  useEffect(() => {
    if (!editId) return
    setLoadingEdit(true)
    getQuote(editId)
      .then((q) => {
        reset({
          quote_date: q.quote_date || getDefaultDate(),
          valid_until: q.valid_until || getDefault30Days(),
          seller_name: q.seller_name || '',
          seller_vat_id: q.seller_vat_id || '',
          seller_address: q.seller_address || '',
          buyer_name: q.buyer_name || '',
          buyer_vat_id: q.buyer_vat_id || '',
          buyer_address: q.buyer_address || '',
          tax_rate: q.tax_rate ?? 19,
          line_items:
            q.line_items && q.line_items.length > 0
              ? q.line_items.map((li) => ({
                  description: li.description,
                  quantity: li.quantity,
                  unit_price: li.unit_price,
                  net_amount: li.net_amount,
                  tax_rate: li.tax_rate ?? 19,
                }))
              : [{ description: '', quantity: 1, unit_price: 0, net_amount: 0, tax_rate: 19 }],
          intro_text: q.intro_text || '',
          closing_text: q.closing_text || '',
          internal_notes: q.internal_notes || '',
          iban: q.iban || '',
          bic: q.bic || '',
          payment_account_name: q.payment_account_name || '',
        })
      })
      .catch((err) => {
        setApiError(getErrorMessage(err, 'Angebot konnte nicht geladen werden'))
      })
      .finally(() => setLoadingEdit(false))
  }, [editId, reset])

  const selectContact = useCallback(
    (contact: Contact) => {
      setValue('buyer_name', contact.name)
      if (contact.vat_id) setValue('buyer_vat_id', contact.vat_id)
      const addressParts = [contact.address_line1, contact.address_line2, `${contact.zip || ''} ${contact.city || ''}`.trim()].filter(Boolean)
      if (addressParts.length > 0) setValue('buyer_address', addressParts.join(', '))
      setShowContactPicker(false)
    },
    [setValue]
  )

  const onSubmit = async (data: FormData) => {
    setLoading(true)
    setApiError(null)

    const processedItems = data.line_items.map((item) => ({
      ...item,
      net_amount: (Number(item.quantity) || 0) * (Number(item.unit_price) || 0),
    }))

    const payload: QuoteCreate = {
      quote_date: data.quote_date,
      valid_until: data.valid_until,
      seller_name: data.seller_name || undefined,
      seller_vat_id: data.seller_vat_id || undefined,
      seller_address: data.seller_address || undefined,
      buyer_name: data.buyer_name || undefined,
      buyer_vat_id: data.buyer_vat_id || undefined,
      buyer_address: data.buyer_address || undefined,
      tax_rate: data.tax_rate,
      line_items: processedItems,
      intro_text: data.intro_text || undefined,
      closing_text: data.closing_text || undefined,
      internal_notes: data.internal_notes || undefined,
      iban: data.iban || undefined,
      bic: data.bic || undefined,
      payment_account_name: data.payment_account_name || undefined,
    }

    try {
      if (editId) {
        await updateQuote(editId, payload)
        toast.success('Angebot aktualisiert')
        router.push(`/angebote/${editId}`)
      } else {
        const result = await createQuote(payload)
        setSuccess({ quoteId: result.quote_id })
      }
    } catch (err: unknown) {
      setApiError(getErrorMessage(err, 'Angebot konnte nicht erstellt werden'))
    } finally {
      setLoading(false)
    }
  }

  const inputClass = 'w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 transition-colors'

  const inputStyle = {
    backgroundColor: 'rgb(var(--input))',
    borderColor: 'rgb(var(--input-border))',
    color: 'rgb(var(--foreground))',
  }

  const labelStyle = { color: 'rgb(var(--foreground))' }
  const labelMutedStyle = { color: 'rgb(var(--foreground-muted))' }

  if (loadingEdit) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Loader2 size={24} className="animate-spin" style={{ color: 'rgb(var(--foreground-muted))' }} />
        <span className="ml-2 text-sm" style={{ color: 'rgb(var(--foreground-muted))' }}>Angebot wird geladen...</span>
      </div>
    )
  }

  // ===== Success screen =====
  if (success) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center px-4 py-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
          className="rounded-2xl border p-8 text-center max-w-md w-full"
          style={{
            backgroundColor: 'rgb(var(--card))',
            borderColor: 'rgb(var(--border))',
            boxShadow: 'var(--shadow-xl)',
          }}
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
          >
            <CheckCircle
              className="mx-auto mb-4"
              size={56}
              style={{ color: 'rgb(var(--accent))' }}
            />
          </motion.div>
          <h2 className="text-xl font-bold mb-2" style={{ color: 'rgb(var(--foreground))' }}>
            Angebot erfolgreich erstellt!
          </h2>
          <p className="text-sm mb-6" style={{ color: 'rgb(var(--foreground-muted))' }}>
            Ihr Angebot wurde gespeichert und kann jetzt versendet werden.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href={`/angebote/${success.quoteId}`}
              className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium text-white"
              style={{ backgroundColor: 'rgb(var(--primary))' }}
            >
              <FileText size={16} /> Angebot anzeigen
            </Link>
            <Link
              href="/angebote"
              className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium"
              style={{
                backgroundColor: 'rgb(var(--muted))',
                color: 'rgb(var(--foreground))',
              }}
            >
              Zur Angebotsliste
            </Link>
            <button
              onClick={() => {
                setSuccess(null)
                reset()
              }}
              className="px-4 py-2.5 rounded-lg text-sm font-medium"
              style={{
                backgroundColor: 'rgb(var(--muted))',
                color: 'rgb(var(--foreground))',
              }}
            >
              Neues Angebot
            </button>
          </div>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-6 pb-24 lg:pb-6 max-w-3xl mx-auto">
      {/* Page header */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <div className="flex items-center gap-3 mb-1">
          <Link
            href="/angebote"
            className="p-1.5 rounded-md transition-colors"
            style={{ color: 'rgb(var(--foreground-muted))' }}
          >
            <ArrowLeft size={18} />
          </Link>
          <h1 className="text-2xl font-bold tracking-tight" style={{ color: 'rgb(var(--foreground))' }}>
            {editId ? 'Angebot bearbeiten' : 'Neues Angebot'}
          </h1>
        </div>
        <p className="text-sm mt-0.5 ml-9" style={{ color: 'rgb(var(--foreground-muted))' }}>
          {editId ? 'Bearbeiten Sie die Angebotsdetails' : 'Erstellen Sie ein neues Angebot fuer Ihren Kunden'}
        </p>
      </motion.div>

      {/* API error */}
      <AnimatePresence>
        {apiError && (
          <motion.div
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            className="mb-4 rounded-xl border p-4 flex items-start gap-3"
            style={{
              backgroundColor: 'rgb(var(--destructive-light))',
              borderColor: 'rgb(var(--destructive-border))',
            }}
          >
            <AlertCircle size={18} className="shrink-0 mt-0.5" style={{ color: 'rgb(var(--destructive))' }} />
            <p className="text-sm flex-1" style={{ color: 'rgb(var(--destructive))' }}>{apiError}</p>
            <button onClick={() => setApiError(null)} className="shrink-0 p-0.5" style={{ color: 'rgb(var(--destructive))' }}>
              <X size={14} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">

        {/* ---- Angebotsdaten ---- */}
        <motion.div custom={0} variants={sectionVariants} initial="hidden" animate="visible">
          <Section title="Angebotsdaten" icon={<FileText size={16} />} info="Datum des Angebots und Gueltigkeitszeitraum.">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1" style={labelStyle}>
                  Angebotsdatum
                </label>
                <input
                  type="date"
                  {...register('quote_date')}
                  className={inputClass}
                  style={inputStyle}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1" style={labelStyle}>
                  Gueltig bis
                </label>
                <input
                  type="date"
                  {...register('valid_until')}
                  className={inputClass}
                  style={inputStyle}
                />
              </div>
            </div>
          </Section>
        </motion.div>

        {/* ---- Absender (Seller) ---- */}
        <motion.div custom={1} variants={sectionVariants} initial="hidden" animate="visible">
          <Section title="Absender" info="Ihre eigenen Firmendaten.">
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium mb-1" style={labelStyle}>
                  Firmenname
                </label>
                <input
                  {...register('seller_name')}
                  className={inputClass}
                  style={inputStyle}
                  placeholder="Muster GmbH"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1" style={labelStyle}>
                  USt-IdNr.
                </label>
                <input
                  {...register('seller_vat_id')}
                  className={inputClass}
                  style={inputStyle}
                  placeholder="DE123456789"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1" style={labelStyle}>
                  Adresse
                </label>
                <textarea
                  {...register('seller_address')}
                  rows={2}
                  className={inputClass}
                  style={inputStyle}
                  placeholder="Musterstrasse 1, 60311 Frankfurt am Main"
                />
              </div>
            </div>
          </Section>
        </motion.div>

        {/* ---- Empfaenger (Buyer) ---- */}
        <motion.div custom={2} variants={sectionVariants} initial="hidden" animate="visible">
          <Section title="Empfaenger" info="Die Daten Ihres Kunden.">
            <div className="space-y-3">
              <div className="flex items-end gap-2">
                <div className="flex-1">
                  <label className="block text-sm font-medium mb-1" style={labelStyle}>
                    Firmenname
                  </label>
                  <input
                    {...register('buyer_name')}
                    className={inputClass}
                    style={inputStyle}
                    placeholder="Kunde AG"
                  />
                </div>
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setShowContactPicker(!showContactPicker)}
                    className="p-2 rounded-lg border transition-colors"
                    style={{
                      borderColor: 'rgb(var(--border))',
                      color: 'rgb(var(--foreground-muted))',
                      backgroundColor: 'rgb(var(--muted))',
                    }}
                    title="Kontakt auswaehlen"
                  >
                    <Users size={16} />
                  </button>
                  {showContactPicker && contacts.length > 0 && (
                    <div
                      className="absolute right-0 top-full mt-1 z-50 w-64 rounded-lg border shadow-lg max-h-48 overflow-y-auto"
                      style={{
                        backgroundColor: 'rgb(var(--card))',
                        borderColor: 'rgb(var(--border))',
                      }}
                    >
                      {contacts.map((c) => (
                        <button
                          key={c.id}
                          type="button"
                          onClick={() => selectContact(c)}
                          className="w-full text-left px-3 py-2 text-sm transition-colors"
                          style={{ color: 'rgb(var(--foreground))' }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.backgroundColor = 'rgb(var(--sidebar-item-hover))'
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.backgroundColor = 'transparent'
                          }}
                        >
                          <span className="font-medium">{c.name}</span>
                          {c.email && (
                            <span className="block text-xs" style={{ color: 'rgb(var(--foreground-muted))' }}>
                              {c.email}
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1" style={labelStyle}>
                  USt-IdNr. <span className="text-xs font-normal" style={labelMutedStyle}>(optional)</span>
                </label>
                <input
                  {...register('buyer_vat_id')}
                  className={inputClass}
                  style={inputStyle}
                  placeholder="DE987654321"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1" style={labelStyle}>
                  Adresse
                </label>
                <textarea
                  {...register('buyer_address')}
                  rows={2}
                  className={inputClass}
                  style={inputStyle}
                  placeholder="Kundenstrasse 5, 10115 Berlin"
                />
              </div>
            </div>
          </Section>
        </motion.div>

        {/* ---- Einleitungstext ---- */}
        <motion.div custom={3} variants={sectionVariants} initial="hidden" animate="visible">
          <Section title="Einleitungstext" info="Optionaler Text, der vor den Positionen auf dem Angebot erscheint.">
            <textarea
              {...register('intro_text')}
              rows={3}
              className={inputClass}
              style={inputStyle}
              placeholder="Vielen Dank fuer Ihre Anfrage. Gerne unterbreiten wir Ihnen folgendes Angebot..."
            />
          </Section>
        </motion.div>

        {/* ---- Positionen ---- */}
        <motion.div custom={4} variants={sectionVariants} initial="hidden" animate="visible">
          <Section title="Positionen">
            <div className="flex items-center justify-between mb-4">
              <p className="text-xs" style={labelMutedStyle}>
                Netto-Betrag = Menge x Einzelpreis (live berechnet)
              </p>
              <button
                type="button"
                onClick={() =>
                  append({ description: '', quantity: 1, unit_price: 0, net_amount: 0, tax_rate: 19 })
                }
                className="flex items-center gap-1.5 text-sm font-medium"
                style={{ color: 'rgb(var(--primary))' }}
              >
                <Plus size={14} /> Position hinzufuegen
              </button>
            </div>

            {/* Column headers */}
            <div
              className="grid grid-cols-12 gap-2 text-xs font-semibold uppercase tracking-wide mb-2 px-1"
              style={{ color: 'rgb(var(--foreground-muted))' }}
            >
              <div className="col-span-5">Beschreibung</div>
              <div className="col-span-2 text-center">Menge</div>
              <div className="col-span-3 text-right">Einzelpreis</div>
              <div className="col-span-2 text-right">Netto</div>
            </div>

            <div className="space-y-2">
              <AnimatePresence>
                {fields.map((field, index) => {
                  const qty = Number(watchedItems[index]?.quantity) || 0
                  const price = Number(watchedItems[index]?.unit_price) || 0
                  const lineNet = qty * price
                  return (
                    <motion.div
                      key={field.id}
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <div className="grid grid-cols-12 gap-2 items-center">
                        <div className="col-span-5">
                          <input
                            {...register(`line_items.${index}.description`)}
                            className={inputClass}
                            style={inputStyle}
                            placeholder="Beratungsleistung"
                          />
                        </div>
                        <div className="col-span-2">
                          <input
                            type="number"
                            step="0.01"
                            min="0"
                            {...register(`line_items.${index}.quantity`, {
                              valueAsNumber: true,
                            })}
                            className={`${inputClass} text-center`}
                            style={inputStyle}
                            placeholder="1"
                          />
                        </div>
                        <div className="col-span-3">
                          <input
                            type="number"
                            step="0.01"
                            min="0"
                            {...register(`line_items.${index}.unit_price`, {
                              valueAsNumber: true,
                            })}
                            className={`${inputClass} text-right`}
                            style={inputStyle}
                            placeholder="100.00"
                          />
                        </div>
                        <div className="col-span-2 flex items-center justify-end gap-1.5">
                          <span
                            className="text-sm font-semibold tabular-nums"
                            style={{ color: 'rgb(var(--foreground))' }}
                          >
                            {lineNet.toFixed(2)}
                          </span>
                          <button
                            type="button"
                            onClick={() => remove(index)}
                            disabled={fields.length === 1}
                            className="disabled:opacity-30 transition-opacity p-0.5"
                            style={{ color: 'rgb(var(--destructive))' }}
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  )
                })}
              </AnimatePresence>
            </div>
          </Section>
        </motion.div>

        {/* ---- Schlusstext ---- */}
        <motion.div custom={5} variants={sectionVariants} initial="hidden" animate="visible">
          <Section title="Schlusstext" info="Optionaler Text, der nach den Positionen auf dem Angebot erscheint.">
            <textarea
              {...register('closing_text')}
              rows={3}
              className={inputClass}
              style={inputStyle}
              placeholder="Wir freuen uns auf Ihre Rueckmeldung und stehen fuer Rueckfragen gerne zur Verfuegung."
            />
          </Section>
        </motion.div>

        {/* ---- Interne Notizen ---- */}
        <motion.div custom={6} variants={sectionVariants} initial="hidden" animate="visible">
          <Section title="Interne Notizen" info="Diese Notizen werden nicht auf dem PDF angezeigt und sind nur intern sichtbar.">
            <textarea
              {...register('internal_notes')}
              rows={2}
              className={inputClass}
              style={inputStyle}
              placeholder="Interne Anmerkungen..."
            />
          </Section>
        </motion.div>

        {/* ---- Zahlungsinformationen ---- */}
        <motion.div custom={7} variants={sectionVariants} initial="hidden" animate="visible">
          <Section title="Zahlungsinformationen" info="Optionale Bankverbindung fuer die Zahlungsabwicklung.">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1" style={labelStyle}>
                  IBAN
                </label>
                <input
                  {...register('iban')}
                  className={`${inputClass} font-mono`}
                  style={inputStyle}
                  placeholder="DE89 3704 0044 0532 0130 00"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1" style={labelStyle}>
                  BIC/SWIFT
                </label>
                <input
                  {...register('bic')}
                  className={`${inputClass} font-mono`}
                  style={inputStyle}
                  placeholder="COBADEFFXXX"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1" style={labelStyle}>
                  Kontoinhaber
                </label>
                <input
                  {...register('payment_account_name')}
                  className={inputClass}
                  style={inputStyle}
                  placeholder="Firmenname GmbH"
                />
              </div>
            </div>
          </Section>
        </motion.div>

        {/* ---- Zusammenfassung ---- */}
        <motion.div custom={8} variants={sectionVariants} initial="hidden" animate="visible">
          <Section title="Zusammenfassung">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span style={{ color: 'rgb(var(--foreground-muted))' }}>Nettobetrag</span>
                <span className="font-medium tabular-nums" style={{ color: 'rgb(var(--foreground))' }}>
                  {net.toFixed(2)} EUR
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span style={{ color: 'rgb(var(--foreground-muted))' }}>
                  MwSt ({watchedTaxRate}%)
                </span>
                <span className="font-medium tabular-nums" style={{ color: 'rgb(var(--foreground))' }}>
                  {tax.toFixed(2)} EUR
                </span>
              </div>
              <div
                className="flex justify-between text-sm font-bold pt-2 border-t"
                style={{ borderColor: 'rgb(var(--border))' }}
              >
                <span style={{ color: 'rgb(var(--foreground))' }}>Bruttobetrag</span>
                <span className="tabular-nums" style={{ color: 'rgb(var(--foreground))' }}>
                  {gross.toFixed(2)} EUR
                </span>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1 mt-3" style={labelStyle}>
                  MwSt-Satz %
                </label>
                <input
                  type="number"
                  step="1"
                  min="0"
                  max="100"
                  {...register('tax_rate', { valueAsNumber: true })}
                  className={inputClass}
                  style={inputStyle}
                />
              </div>
            </div>
          </Section>
        </motion.div>

        {/* ---- Actions ---- */}
        <motion.div custom={9} variants={sectionVariants} initial="hidden" animate="visible">
          <div className="flex items-center justify-end gap-3 pt-2">
            <Link
              href="/angebote"
              className="px-4 py-2.5 rounded-lg text-sm font-medium border transition-colors"
              style={{
                borderColor: 'rgb(var(--border))',
                color: 'rgb(var(--foreground))',
              }}
            >
              Abbrechen
            </Link>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium text-white transition-colors disabled:opacity-50"
              style={{ backgroundColor: 'rgb(var(--primary))' }}
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Wird gespeichert...
                </>
              ) : editId ? (
                'Angebot aktualisieren'
              ) : (
                'Angebot erstellen'
              )}
            </button>
          </div>
        </motion.div>
      </form>
    </div>
  )
}

export default function QuoteFormPage() {
  return (
    <Suspense fallback={<div className="p-8"><div className="animate-pulse h-8 w-48 rounded" style={{ background: 'rgb(var(--muted))' }} /></div>}>
      <QuoteFormContent />
    </Suspense>
  )
}
