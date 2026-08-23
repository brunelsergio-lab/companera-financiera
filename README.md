# 🌱 Compañera Financiera V11 — Beta Comunitaria

Esta versión reemplaza la base SQLite local por **Supabase**, para que distintos usuarios puedan crear una cuenta, cerrar la app y volver más tarde sin perder sus datos.

## 1. Crear Supabase
1. Entrá a https://supabase.com y creá un proyecto.
2. Abrí **SQL Editor**.
3. Pegá todo el contenido de `supabase_schema.sql`.
4. Ejecutá la consulta.
5. En **Project Settings → API** copiá:
   - Project URL
   - anon/public key

## 2. Probar localmente
Creá `.streamlit/secrets.toml`:

    SUPABASE_URL = "..."
    SUPABASE_ANON_KEY = "..."

Instalá:

    python -m pip install -r requirements.txt

Ejecutá:

    python -m streamlit run app.py

## 3. Subir a GitHub
Creá un repositorio, por ejemplo:

    companera-financiera

Subí:
- app.py
- requirements.txt
- supabase_schema.sql
- .streamlit/config.toml
- .gitignore
- README.md

**NO subas `.streamlit/secrets.toml`.**

## 4. Publicar en Streamlit Community Cloud
1. Entrá a https://share.streamlit.io
2. Conectá GitHub.
3. Elegí tu repositorio y `app.py`.
4. En **Advanced settings → Secrets**, pegá:

    SUPABASE_URL = "..."
    SUPABASE_ANON_KEY = "..."

5. Deploy.

Streamlit te dará una URL `*.streamlit.app` para compartir.

## Seguridad
La base usa Supabase Auth + Row Level Security. Cada fila tiene `user_id`, y las políticas SQL solo permiten que el usuario autenticado vea/modifique sus propios datos.

## Beta
Para una primera prueba comunitaria:
- invitá 10–20 personas;
- pediles probar desde celular;
- evitá usar datos ficticios mezclados con reales;
- recogé comentarios sobre claridad del lenguaje, errores de lectura de resúmenes y utilidad del plan.
