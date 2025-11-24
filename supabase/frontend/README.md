**Resumen**: Aplicación frontend que consume el backend en Supabase para `cliente`, `producto`, `orden` y muestra recomendaciones basadas en reglas de asociación.

**Ubicación**: `supabase/frontend`

**Cómo ejecutar**
- Instala Node.js (recomendado v18+) y npm.
- Desde PowerShell:
  ```powershell
  cd supabase/frontend
  npm install
  npm run dev
  ```

**Variables de entorno (`.env.local`)**
- El frontend espera un archivo `supabase/frontend/.env.local` con las siguientes variables (Vite usa el prefijo `VITE_`):
  - `VITE_SUPABASE_URL` — URL del proyecto Supabase (ej.: `https://xyz.supabase.co`)
  - `VITE_SUPABASE_ANON_KEY` — clave pública anon del proyecto

Ejemplo de `.env.local` (NO subir claves reales):
```
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...anon-key...
```

**Notas**
- El frontend usa `src/services/api.js` y `@supabase/supabase-js` para acceder a datos. Ahora filtra `association_rule` por `active = true`, por lo que las reglas soft-deleted se ignoran en las recomendaciones.
- Si pruebas con otro proyecto Supabase o cambias claves, actualiza `.env.local` y reinicia el servidor de desarrollo.

**Tareas comunes**
- Compilar para producción:
  ```powershell
  npm run build
  npm run preview
  ```

**Opcional**
- Puedo añadir una vista de administrador que muestre reglas inactivas (`association_rule.active`) si lo deseas.
