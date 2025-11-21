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