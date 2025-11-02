# Supabase frontend

Instalación y ejecución del frontend (Vite + React):

1. Instalar dependencias:

	npm install

2. Configurar variables de entorno en `supabase/frontend/.env.local` (o en la raíz del frontend):

	VITE_SUPABASE_URL=your-supabase-url
	VITE_SUPABASE_ANON_KEY=your-anon-key

3. Correr el servidor de desarrollo:

	npm run dev

El proyecto usa `@supabase/supabase-js` para comunicarse con las tablas descritas en `backEnd/db/migrations/creationScript.sql`.

Notas:
- Las rutas del frontend esperan las tablas `cliente`, `producto`, `orden` y `orden_detalle` en Supabase/Postgres.
- Los campos principales son UUIDs: `cliente_id`, `producto_id`, `orden_id`.