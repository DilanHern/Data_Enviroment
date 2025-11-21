import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

const _normalizeId = (id) => {
	if (id === null || id === undefined) return id
	const n = Number(id)
	return Number.isNaN(n) ? id : n
}

// Clientes API (tabla: cliente)
export const clientesApi = {
	getAll: async () => {
		const { data, error } = await supabase
			.from('cliente')
			.select('*')
			.order('nombre', { ascending: true })
		if (error) throw error
		return { data }
	},
	getById: async (id) => {
		const { data, error } = await supabase.from('cliente').select('*').eq('cliente_id', _normalizeId(id)).single()
		if (error) throw error
		return { data }
	},
	create: async (payload) => {
		const { data, error } = await supabase.from('cliente').insert([payload]).single()
		if (error) throw error
		return { data }
	},
	update: async (id, payload) => {
		const { data, error } = await supabase.from('cliente').update(payload).eq('cliente_id', _normalizeId(id)).select().single()
		if (error) throw error
		return { data }
	},
	delete: async (id) => {
		const { data, error } = await supabase.from('cliente').delete().eq('cliente_id', _normalizeId(id))
		if (error) throw error
		return { data }
	}
}

// Productos API (tabla: producto)
export const productosApi = {
	getAll: async () => {
		const { data, error } = await supabase.from('producto').select('*').order('nombre', { ascending: true })
		if (error) throw error
		return { data }
	},
	getById: async (id) => {
		const { data, error } = await supabase.from('producto').select('*').eq('producto_id', _normalizeId(id)).single()
		if (error) throw error
		return { data }
	},
	create: async (payload) => {
		const { data, error } = await supabase.from('producto').insert([payload]).single()
		if (error) throw error
		return { data }
	},
	update: async (id, payload) => {
		const { data, error } = await supabase.from('producto').update(payload).eq('producto_id', _normalizeId(id)).select().single()
		if (error) throw error
		return { data }
	},
	delete: async (id) => {
		const { data, error } = await supabase.from('producto').delete().eq('producto_id', _normalizeId(id))
		if (error) throw error
		return { data }
	}
}

// Ordenes API (tablas: orden, orden_detalle)
export const ordenesApi = {
	getAll: async () => {
		// traer ordenes con sus detalles (items) incluyendo nombre, id y sku del producto en cada detalle
		// select syntax: orden_detalle(producto(producto_id,nombre,sku), cantidad, precio_unit)
		const { data, error } = await supabase.from('orden').select('*, orden_detalle(producto(producto_id,nombre,sku), cantidad, precio_unit)').order('fecha', { ascending: false })
		if (error) throw error
		return { data }
	},
	getById: async (id) => {
		const { data, error } = await supabase.from('orden').select('*, orden_detalle(producto(producto_id,nombre,sku), cantidad, precio_unit)').eq('orden_id', _normalizeId(id)).single()
		if (error) throw error
		return { data }
	},
	create: async (payload) => {
		// payload: { cliente_id, fecha, canal, moneda, total, items: [{producto_id, cantidad, precio_unit}], metadatos }
		const { items, metadatos, ...orderData } = payload
		// Insert orden
		const { data: orden, error: errOrden } = await supabase.from('orden').insert([orderData]).select().single()
		if (errOrden) throw errOrden

		// Insert detalles
		if (items && items.length > 0) {
			const detalles = items.map(i => ({ ...i, orden_id: orden.orden_id }))
			const { error: errDetalle } = await supabase.from('orden_detalle').insert(detalles)
			if (errDetalle) throw errDetalle
		}

		// Attach items to returned object
		const { data: created } = await supabase.from('orden').select('*, orden_detalle(*)').eq('orden_id', _normalizeId(orden.orden_id)).single()
		return { data: created }
	},
	update: async (id, payload) => {
		const { items, metadatos, ...orderData } = payload
		const { error: errOrden } = await supabase.from('orden').update(orderData).eq('orden_id', _normalizeId(id))
		if (errOrden) throw errOrden

		// replace detalles: delete existing then insert
		const { error: errDel } = await supabase.from('orden_detalle').delete().eq('orden_id', _normalizeId(id))
		if (errDel) throw errDel

		if (items && items.length > 0) {
			const detalles = items.map(i => ({ ...i, orden_id: _normalizeId(id) }))
			const { error: errIns } = await supabase.from('orden_detalle').insert(detalles)
			if (errIns) throw errIns
		}

		const { data } = await supabase.from('orden').select('*, orden_detalle(*)').eq('orden_id', _normalizeId(id)).single()
		return { data }
	},
	delete: async (id) => {
		// borrar detalles primero
		const { error: errDel } = await supabase.from('orden_detalle').delete().eq('orden_id', _normalizeId(id))
		if (errDel) throw errDel
		const { data, error } = await supabase.from('orden').delete().eq('orden_id', _normalizeId(id))
		if (error) throw error
		return { data }
	}
}

// Recommendations API: obtiene productos recomendados basados en reglas de asociación.
// Ahora requiere que TODOS los antecedentes de una regla estén presentes (AND).
export const recommendationsApi = {
	// dado un array de producto_ids (strings or uuids), devuelve objetos { producto_id, score, avg_lift, producto, rules }
	getForAntecedents: async (antecedentIds = []) => {
		if (!antecedentIds || antecedentIds.length === 0) return { data: [] }

		// 1) obtener rule_ids candidatos que contienen AL MENOS uno de los antecedentes
		const { data: antRows, error: errAnt } = await supabase
			.from('rule_antecedente')
			.select('rule_id, producto_id')
			.in('producto_id', antecedentIds)
		if (errAnt) throw errAnt

		const candidateRuleIds = Array.from(new Set((antRows || []).map(r => r.rule_id)))
		if (candidateRuleIds.length === 0) return { data: [] }

		// 2) obtener todos los antecedentes de esas reglas para comprobar que TODOS estén presentes
		const { data: allAnts, error: errAllAnts } = await supabase
			.from('rule_antecedente')
			.select('rule_id, producto_id')
			.in('rule_id', candidateRuleIds)
		if (errAllAnts) throw errAllAnts

		// agrupar antecedentes por rule_id
		const antsByRule = new Map()
		;(allAnts || []).forEach(a => {
			const arr = antsByRule.get(a.rule_id) || []
			arr.push(a.producto_id)
			antsByRule.set(a.rule_id, arr)
		})

		const providedSet = new Set(antecedentIds.map(String))
		// filtrar reglas cuyo conjunto de antecedentes sea EXACTAMENTE el conjunto proporcionado
		// (mismo tamaño y mismos elementos). Esto evita incluir reglas cuyos
		// antecedentes sean subconjuntos de los proporcionados.
		const matchedRuleIds = []
		for (const [ruleId, antList] of antsByRule.entries()) {
			const antArr = (antList || []).map(String)
			const antSet = new Set(antArr)
			// sizes must match exactly
			if (antSet.size !== providedSet.size) continue
			let allPresent = true
			for (const a of antSet) {
				if (!providedSet.has(a)) {
					allPresent = false
					break
				}
			}
			if (allPresent) matchedRuleIds.push(ruleId)
		}

		if (matchedRuleIds.length === 0) return { data: [] }

		// 3) obtener las reglas y sus consecuentes únicamente para las reglas que coinciden totalmente
		const { data: rules, error: errRules } = await supabase
			.from('association_rule')
			.select('rule_id, soporte, confianza, lift')
			.in('rule_id', matchedRuleIds)
		if (errRules) throw errRules

		const { data: consRows, error: errCons } = await supabase
			.from('rule_consecuente')
			.select('rule_id, producto_id')
			.in('rule_id', matchedRuleIds)
		if (errCons) throw errCons

		// 4) acumular scores por producto_id (sum of confidences), pero EXCLUIR productos que ya están en los antecedentes
		const ruleMap = new Map((rules || []).map(r => [r.rule_id, r]))
		const scoreMap = new Map()
		const providedSetLower = new Set(Array.from(providedSet).map(String))
		;(consRows || []).forEach(c => {
			const rule = ruleMap.get(c.rule_id)
			if (!rule) return
			const pid = String(c.producto_id)
			// excluir si el producto recomendado está dentro de los antecedentes proporcionados
			if (providedSetLower.has(pid)) return
			const score = Number(rule.confianza || 0)
			const lift = Number(rule.lift || 0)
			const prev = scoreMap.get(pid) || { score: 0, lifts: [], count: 0, rules: [] }
			prev.score += score
			prev.lifts.push(lift)
			prev.count += 1
			prev.rules.push(rule.rule_id)
			scoreMap.set(pid, prev)
		})

		// 5) build list and fetch product details
		const productIds = Array.from(scoreMap.keys())
		if (productIds.length === 0) return { data: [] }

		const { data: products, error: errProds } = await supabase.from('producto').select('*').in('producto_id', productIds)
		if (errProds) throw errProds

		const prodMap = new Map((products || []).map(p => [p.producto_id, p]))
		const results = productIds.map(pid => {
			const s = scoreMap.get(pid)
			const avg_lift = (s.lifts.reduce((a,b)=>a+b,0) / Math.max(1, s.lifts.length))
			const max_lift = Math.max(...s.lifts)
			return {
				producto_id: pid,
				score: s.score,
				avg_lift: avg_lift,
				max_lift: max_lift,
				lifts: s.lifts,
				count: s.count,
				producto: prodMap.get(pid) || null,
				rules: s.rules
			}
		}).sort((a,b) => b.score - a.score)

		return { data: results }
	}
}