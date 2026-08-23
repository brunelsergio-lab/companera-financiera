
import io
import re
import math
from datetime import date, datetime
import streamlit as st
import pandas as pd
from pypdf import PdfReader
from PIL import Image
import fitz
from rapidocr import RapidOCR
from supabase import create_client

st.set_page_config(page_title="Compañera Financiera", page_icon="🌱", layout="wide")

# -------------------- UI --------------------
st.markdown("""
<style>
:root{
  --bg:#F6F8FC; --card:#FFFFFF; --text:#172033; --muted:#667085;
  --border:#E3E8F0; --green:#16A34A; --red:#DC2626; --blue:#2563EB; --amber:#D97706;
}
.stApp,[data-testid="stAppViewContainer"]{background:var(--bg)!important;color:var(--text)!important;}
[data-testid="stHeader"]{background:var(--bg)!important;}
.block-container{max-width:940px;padding-top:.7rem;padding-bottom:5rem;}
h1,h2,h3,h4,h5,h6,p,label,span,div{color:var(--text);}
input,textarea{background:#FFF!important;color:#172033!important;-webkit-text-fill-color:#172033!important;opacity:1!important;}
input::placeholder,textarea::placeholder{color:#7B8794!important;-webkit-text-fill-color:#7B8794!important;}
div[data-baseweb="input"]>div,div[data-baseweb="select"]>div{
  background:#FFF!important;color:#172033!important;border:1px solid #CBD5E1!important;border-radius:14px!important;
}
div[data-baseweb="select"] span,[role="listbox"],[role="option"],[role="option"] *{color:#172033!important;background:#FFF!important;}
[role="option"]:hover{background:#EEF4FF!important;}
[data-testid="stMetric"],div[data-testid="stForm"],.card{
  background:#FFF!important;border:1px solid var(--border)!important;border-radius:18px!important;
  padding:15px!important;box-shadow:0 3px 12px rgba(15,23,42,.04);
}
.card{margin:10px 0;}
.good{border-left:5px solid var(--green)!important}.bad{border-left:5px solid var(--red)!important}
.warn{border-left:5px solid var(--amber)!important}.info{border-left:5px solid var(--blue)!important}
.small{font-size:.92rem;color:var(--muted)!important}
.stButton>button,.stFormSubmitButton>button,[data-testid="stDownloadButton"] button{
 min-height:48px;border-radius:14px;font-weight:750;
}
div[role="radiogroup"]{display:flex;overflow-x:auto;gap:6px;padding-bottom:4px;scrollbar-width:none;}
div[role="radiogroup"] label{background:#FFF!important;border:1px solid var(--border)!important;border-radius:999px!important;padding:7px 12px!important;white-space:nowrap!important;}
div[role="radiogroup"] label *{color:#172033!important;}
@media(max-width:700px){
 .block-container{padding-left:.72rem;padding-right:.72rem;}
 [data-testid="column"]{width:100%!important;flex:1 1 100%!important;}
 h1{font-size:1.6rem!important;}
}
</style>
""", unsafe_allow_html=True)

# -------------------- Helpers --------------------
def num(v):
    try: return float(v or 0)
    except: return 0.0

def money(v):
    try: return "$" + f"{float(v):,.0f}".replace(",", ".")
    except: return "$0"

def parse_money(value):
    s=str(value or "").strip().replace("$","").replace(" ","")
    if not s: return 0.0
    try:
        if "." in s and "," in s:
            if s.rfind(",") > s.rfind("."): s=s.replace(".","").replace(",",".")
            else: s=s.replace(",","")
        elif "," in s:
            tail=s.split(",")[-1]
            s=s.replace(".","").replace(",",".") if len(tail)<=2 else s.replace(",","")
        elif "." in s:
            parts=s.split(".")
            if len(parts)>1 and all(len(p)==3 for p in parts[1:]): s="".join(parts)
        return float(s)
    except: return 0.0

def money_input(label, value=0, key=None, placeholder="$ 100.000"):
    initial="" if num(value)==0 else "$ "+f"{num(value):,.0f}".replace(",",".")
    return st.text_input(label,value=initial,key=key,placeholder=placeholder)

def french_payment(p,tna,n):
    p=num(p); n=int(n or 0); r=num(tna)/12/100
    if p<=0 or n<=0: return 0
    if r==0: return p/n
    return p*r/(1-(1+r)**(-n))

def estimate_monthly_rate(balance,payment,months):
    p,a,n=num(balance),num(payment),int(months or 0)
    if p<=0 or a<=0 or n<=0:return None
    if a*n<=p:return 0.0
    lo,hi=0.0,1.0
    for _ in range(100):
        mid=(lo+hi)/2
        calc=p/n if mid==0 else p*mid/(1-(1+mid)**(-n))
        if calc<a:lo=mid
        else:hi=mid
    return (lo+hi)/2

def estimate_financing_cost(balance,payment,months):
    p,a,n=num(balance),num(payment),int(months or 0)
    if p<=0 or a<=0 or n<=0:return None
    total=a*n; extra=max(0,total-p); rm=estimate_monthly_rate(p,a,n)
    tea=((1+rm)**12-1)*100 if rm is not None else None
    return {"total":total,"extra":extra,"tea":tea}

# -------------------- Supabase / perfil simple --------------------
def get_supabase():
    try:
        url=st.secrets["SUPABASE_URL"]
        key=st.secrets["SUPABASE_ANON_KEY"]
    except Exception:
        st.error("Falta configurar SUPABASE_URL y SUPABASE_ANON_KEY en Secrets.")
        st.stop()
    return create_client(url,key)

sb=get_supabase()

if "access_token" not in st.session_state:
    st.session_state.access_token=None
if "refresh_token" not in st.session_state:
    st.session_state.refresh_token=None

# Si Streamlit vuelve a ejecutar el script durante la misma sesión,
# restauramos la sesión anónima para que RLS reconozca al usuario.
if st.session_state.access_token and st.session_state.refresh_token:
    try:
        sb.auth.set_session(st.session_state.access_token, st.session_state.refresh_token)
    except Exception:
        pass

def q(table):
    return sb.table(table)

# Beta simple: sin correo ni contraseña.
# Se crea un identificador aleatorio y se conserva en la URL (?u=...).
# Así cada tester puede guardar sus datos sin usar el flujo de Auth.
import uuid

if "user_id" not in st.session_state:
    st.session_state.user_id = None

def get_profile():
    if not st.session_state.user_id:
        return None
    r=q("profiles").select("*").eq("user_id",st.session_state.user_id).execute()
    return r.data[0] if r.data else None

def create_simple_profile(name, age):
    """
    El usuario no ve correo ni contraseña.
    Supabase crea una sesión anónima por detrás para que las políticas RLS sigan protegiendo sus datos.
    """
    res = sb.auth.sign_in_anonymously()
    if not res or not res.user:
        raise RuntimeError("No se pudo crear la sesión anónima.")
    uid = res.user.id

    # Guardamos tokens solo en la sesión actual de Streamlit.
    st.session_state.access_token = res.session.access_token if res.session else None
    st.session_state.refresh_token = res.session.refresh_token if res.session else None
    st.session_state.user_id = uid

    base={
        "user_id":uid,
        "name":name.strip() or "Usuario",
        "gastos_vivir":0,"meta_emergencia":0,"fondo_actual":0,
        "sueldo":0,"extras":0,"extraordinarios":0
    }
    try:
        q("profiles").insert({**base,"age":int(age)}).execute()
    except Exception:
        q("profiles").insert(base).execute()

    return uid

def get_rows(table):
    if not st.session_state.user_id:
        return []
    return q(table).select("*").eq("user_id",st.session_state.user_id).order("created_at").execute().data or []

def open_debts(ds): return [d for d in ds if d.get("estado")!="Pagada"]
def total_debt(ds): return sum(num(d.get("saldo")) for d in open_debts(ds))
def total_installments(ds): return sum(num(d.get("cuota")) for d in open_debts(ds))

def choose_target(ds, attack_cash):
    ds=open_debts(ds)
    if not ds:return None,"No hay deudas abiertas."
    scored=[]
    for d in ds:
        saldo,cuota,cft,oferta=num(d.get("saldo")),num(d.get("cuota")),num(d.get("cft")),num(d.get("oferta"))
        rest=int(num(d.get("cuotas_restantes")))
        if oferta>0 and saldo>0 and attack_cash>=oferta:
            ahorro=max(0,saldo-oferta); quita=ahorro/saldo if saldo else 0
            score=10000+quita*1000
            reason=f"Podés cerrar un saldo de {money(saldo)} pagando {money(oferta)}. La diferencia aproximada es {money(ahorro)}."
        elif cft>0:
            score=6000+cft
            reason=f"Es de las deudas más caras cargadas: su costo financiero informado es {cft:.1f}% anual."
        elif rest>0 and saldo>0 and cuota>0:
            est=estimate_financing_cost(saldo,cuota,rest)
            score=4000+(est["tea"] or 0)
            reason=f"Sin tasa informada, estimamos con saldo, cuota y {rest} cuotas restantes. Si seguís así pagarías cerca de {money(est['total'])}, unos {money(est['extra'])} por encima del saldo actual."
        else:
            lev=cuota/saldo if saldo>0 else 0
            score=1000+lev*10000
            reason="Faltan algunos datos. Por ahora miramos qué deuda te permitiría liberar más dinero mensual."
        scored.append((score,d,reason))
    scored.sort(key=lambda x:x[0],reverse=True)
    return scored[0][1],scored[0][2]

def build_plan(profile,ds):
    ingresos=num(profile.get("sueldo"))+num(profile.get("extras"))
    vivir=num(profile.get("gastos_vivir")); ext=num(profile.get("extraordinarios"))
    cuotas=total_installments(ds); fondo=num(profile.get("fondo_actual")); meta=num(profile.get("meta_emergencia"))
    colchon=min(meta,vivir) if meta>0 else vivir
    falt=max(0,colchon-fondo)
    pre=ingresos-vivir-ext-cuotas
    aporte=min(max(pre,0),falt,ingresos*.10) if ingresos>0 else 0
    ataque=max(0,pre-aporte)
    target,reason=choose_target(ds,ataque)
    return {"ingresos":ingresos,"vivir":vivir,"extra":ext,"cuotas":cuotas,"fondo":fondo,"meta":meta,
            "colchon":colchon,"aporte":aporte,"ataque":ataque,"deficit":max(0,-pre),"target":target,"reason":reason}

# -------------------- Local PDF/OCR --------------------
@st.cache_resource
def get_ocr():
    return RapidOCR()

def extract_pdf_text(raw):
    reader=PdfReader(io.BytesIO(raw)); pages=[]
    for i,p in enumerate(reader.pages,1):
        try: txt=p.extract_text(extraction_mode="layout") or ""
        except:
            try: txt=p.extract_text() or ""
            except: txt=""
        pages.append(f"\n--- PÁGINA {i} ---\n{txt}")
    return "\n".join(pages),len(reader.pages)

def ocr_image(raw):
    img=Image.open(io.BytesIO(raw)).convert("RGB")
    res=get_ocr()(img)
    if res is None or not getattr(res,"txts",None):return ""
    return "\n".join(str(x) for x in res.txts if x)

def ocr_pdf(raw,max_pages=8):
    doc=fitz.open(stream=raw,filetype="pdf"); out=[]
    for i,p in enumerate(doc):
        if i>=max_pages:break
        pix=p.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
        out.append(ocr_image(pix.tobytes("png")))
    return "\n".join(out),min(len(doc),max_pages)

def extract_local(upload):
    raw=upload.getvalue(); name=(upload.name or "").lower(); mime=upload.type or ""
    if name.endswith(".pdf") or mime=="application/pdf":
        txt,n=extract_pdf_text(raw)
        if len(txt.strip())<120:
            txt,n=ocr_pdf(raw); return txt,n,"OCR local"
        return txt,n,"texto del PDF"
    if mime.startswith("image/") or any(name.endswith(x) for x in [".png",".jpg",".jpeg",".webp"]):
        return ocr_image(raw),1,"OCR local"
    raise ValueError("Formato no compatible")

def ar_money(raw):
    if raw is None:return None
    s=str(raw).strip().replace("$","").replace("ARS","").replace(" ","")
    if "," in s:s=s.replace(".","").replace(",",".")
    try:return float(s)
    except:return None

def after_money(text,labels):
    for label in labels:
        m=re.search(rf"(?is){label}.{{0,100}}?(?:ARS\s*)?\$?\s*([0-9][0-9\.,\s]{{1,22}})",text)
        if m:
            v=ar_money(m.group(1))
            if v is not None:return v,m.group(0).strip()
    return None,""

def after_pct(text,labels):
    for label in labels:
        m=re.search(rf"(?is){label}.{{0,50}}?([0-9]+(?:[\.,][0-9]+)?)\s*%",text)
        if m:return float(m.group(1).replace(",",".")),m.group(0).strip()
    return None,""

def parse_summary(text):
    total,ev1=after_money(text,[r"saldo\s+actual",r"total\s+(?:a\s+)?pagar",r"total\s+del\s+resumen"])
    minimum,ev2=after_money(text,[r"pago\s+m[ií]nimo",r"m[ií]nimo\s+a\s+pagar"])
    cft,ev3=after_pct(text,[r"CFT(?:\s*TEA)?",r"costo\s+financiero\s+total"])
    tna,_=after_pct(text,[r"TNA",r"tasa\s+nominal\s+anual"])
    tea,_=after_pct(text,[r"TEA",r"tasa\s+efectiva\s+anual"])
    if total is not None and total<100:total=None
    if minimum is not None and minimum<100:minimum=None
    return {"total":total,"minimum":minimum,"cft":cft,"tna":tna,"tea":tea,"evidence":[x for x in [ev1,ev2,ev3] if x]}

def first_number_after(text, labels):
    for label in labels:
        m=re.search(rf"(?is){label}.{{0,60}}?([0-9]{{1,3}})", text)
        if m:
            try:return int(m.group(1)),m.group(0).strip()
            except:pass
    return None,""

def parse_loan_screenshot(text):
    """Busca datos típicos de préstamos BNA y pantallas similares."""
    result={}
    saldo,ev_s=after_money(text,[
        r"saldo\s+de\s+capital\s*[:\-]?",
        r"saldo\s+capital\s*[:\-]?",
        r"capital\s+pendiente\s*[:\-]?",
        r"saldo\s*[:\-]?"
    ])
    cuota,ev_c=after_money(text,[
        r"(?:monto|importe)\s+de\s+la\s+cuota\s*[:\-]?",
        r"pr[oó]xima\s+cuota.{0,25}?(?:monto|importe)?\s*[:\-]?"
    ])
    tna,ev_t=after_pct(text,[r"TNA\s+Vigente",r"TNA"])
    cap_orig,ev_o=after_money(text,[r"capital\s+original\s*[:\-]?"])

    pagadas,total=None,None
    ev_q=""
    m=re.search(r"(?is)cuotas\s+pagas\s*([0-9]+)\s*/\s*([0-9]+)",text)
    if m:
        pagadas,total=int(m.group(1)),int(m.group(2)); ev_q=m.group(0).strip()
    if total is None:
        # otra forma: "Próxima cuota: 22 de 36"
        m=re.search(r"(?is)pr[oó]xima\s+cuota\s*[:\-]?\s*([0-9]+)\s+de\s+([0-9]+)",text)
        if m:
            # si la próxima es 22, generalmente 21 están pagas
            pagadas=max(0,int(m.group(1))-1); total=int(m.group(2)); ev_q=m.group(0).strip()

    rest=max(0,total-pagadas) if total is not None and pagadas is not None else 0

    # Nombre / tipo: tomamos una línea representativa.
    name=""
    lines=[" ".join(x.split()) for x in text.splitlines() if x.strip()]
    for line in lines:
        if re.search(r"(?i)\b(REG|REFI|CONVENIO|NACION AHORA|CONSUMO TC)\b",line) and len(line)<120:
            name=line
            break
    if not name:
        name="Préstamo"

    result.update({
        "name":name,
        "entity":"BNA" if re.search(r"(?i)\bBNA\b|BANCO\s+NACION|NACI[ÓO]N",text) else "",
        "saldo":saldo,
        "cuota":cuota,
        "tna":tna,
        "capital_original":cap_orig,
        "cuotas_pagadas":pagadas,
        "cuotas_totales":total,
        "cuotas_restantes":rest,
        "evidence":[x for x in [ev_s,ev_c,ev_t,ev_o,ev_q] if x]
    })
    return result

def merge_loan_results(results):
    """Combina varias capturas del mismo préstamo, quedándose con datos no vacíos."""
    out={"name":"","entity":"","saldo":None,"cuota":None,"tna":None,"capital_original":None,
         "cuotas_pagadas":None,"cuotas_totales":None,"cuotas_restantes":0,"evidence":[]}
    for r in results:
        for k in ["name","entity","saldo","cuota","tna","capital_original","cuotas_pagadas","cuotas_totales"]:
            v=r.get(k)
            if v not in [None,"",0]:
                out[k]=v
        out["evidence"] += r.get("evidence",[])
    if out["cuotas_totales"] is not None and out["cuotas_pagadas"] is not None:
        out["cuotas_restantes"]=max(0,out["cuotas_totales"]-out["cuotas_pagadas"])
    return out

# -------------------- Entrada simple --------------------
if not st.session_state.user_id or not get_profile():
    st.title("🌱 Compañera Financiera")
    st.caption("Una ayuda sencilla para ordenar tus números y empezar a salir de las deudas.")

    st.markdown(
        '<div class="card good"><b>👋 Bienvenido/a</b><br>'
        '<span class="small">No necesitás saber de finanzas. Contanos un poquito de vos y empezamos.</span></div>',
        unsafe_allow_html=True
    )

    with st.form("simple_start"):
        nombre=st.text_input("👤 ¿Cómo te llamás?",placeholder="Ej.: Sergio")
        edad=st.number_input("🎂 ¿Qué edad tenés?",min_value=13,max_value=100,value=30,step=1)
        if st.form_submit_button("🌱 Empezar",type="primary",use_container_width=True):
            if not nombre.strip():
                st.warning("Decime tu nombre para poder acompañarte.")
            else:
                try:
                    create_simple_profile(nombre,edad)
                    st.rerun()
                except Exception as e:
                    st.error(f"No pude crear tu perfil. Revisemos la conexión con la base de datos. Detalle: {e}")
    st.stop()

profile=get_profile()
debts=get_rows("debts"); recurrents=get_rows("recurrents"); people=get_rows("people"); snapshots=get_rows("snapshots")
plan=build_plan(profile,debts)

st.title(f"🌱 Hola, {profile.get('name') or 'amigo/a'}")
st.caption("Vamos paso a paso. No necesitás resolver todo hoy.")
nav=st.radio("nav",["🏠 Inicio","📄 Leer resumen GRATIS","💳 Deudas","🔁 Recurrentes","👥 Personas","⚖️ Ofertas","📅 Mi plan","📊 Progreso","⚙️ Ajustes"],horizontal=True,label_visibility="collapsed")

# -------------------- Inicio --------------------
if nav=="🏠 Inicio":
    st.subheader("🏠 Este mes")
    with st.form("month"):
        sueldo=money_input("💰 Sueldo / ingreso principal ($)",profile.get("sueldo"),"sueldo")
        extras=money_input("🎁 Ingresos extra ($)",profile.get("extras"),"extras")
        ext=money_input("🩺 Gastos extraordinarios ($)",profile.get("extraordinarios"),"ext")
        fondo=money_input("🛟 Fondo de emergencia actual ($)",profile.get("fondo_actual"),"fondo")
        if st.form_submit_button("💾 Guardar y recalcular",type="primary",use_container_width=True):
            q("profiles").update({"sueldo":parse_money(sueldo),"extras":parse_money(extras),
                                  "extraordinarios":parse_money(ext),"fondo_actual":parse_money(fondo)}).eq("user_id",st.session_state.user_id).execute()
            st.rerun()
    plan=build_plan(get_profile(),debts)
    x,y,z=st.columns(3); x.metric("💰 Ingresos",money(plan["ingresos"])); y.metric("🏠 Vivir",money(plan["vivir"])); z.metric("📆 Cuotas",money(plan["cuotas"]))
    if plan["target"]:
        st.markdown(f'<div class="card good"><b>🎯 Objetivo sugerido: {plan["target"]["name"]}</b><br><span class="small">{plan["reason"]}</span></div>',unsafe_allow_html=True)

# -------------------- Lector gratuito --------------------
elif nav=="📄 Leer resumen GRATIS":
    st.subheader("📄 Leer un resumen o captura")
    st.write("Podés subir PDF, PNG, JPG/JPEG o WEBP. La lectura se hace sin API paga.")
    up=st.file_uploader("📎 Subí el archivo",type=["pdf","png","jpg","jpeg","webp"])
    if up and st.button("🔍 Leer",type="primary",use_container_width=True):
        try:
            with st.spinner("Leyendo localmente..."):
                txt,n,method=extract_local(up)
                st.session_state.local_text=txt; st.session_state.local_method=method; st.session_state.local_parse=parse_summary(txt)
        except Exception as e: st.error(f"No pude leerlo: {e}")
    r=st.session_state.get("local_parse")
    if r:
        st.success(f"✅ Lectura por {st.session_state.get('local_method','método local')}. Revisá los números.")
        a,b=st.columns(2); a.metric("🧾 Total",money(r["total"]) if r["total"] else "No encontrado"); b.metric("🪙 Pago mínimo",money(r["minimum"]) if r["minimum"] else "No encontrado")
        st.write(f"**Costo financiero encontrado:** {str(r['cft'])+'%' if r['cft'] is not None else 'No encontrado'}")
        if r["evidence"]:
            with st.expander("🔎 Ver de dónde salieron los datos"):
                for e in r["evidence"]: st.write(e)

# -------------------- Deudas --------------------
elif nav=="💳 Deudas":
    st.subheader("💳 Mis deudas")
    st.caption("Podés cargar una deuda en menos de un minuto o subir capturas para que la app intente completar los datos.")

    # Existing debts
    for d in open_debts(debts):
        st.markdown(
            f'<div class="card bad"><b>{d["name"]}</b><br>'
            f'<span class="small">{d.get("entity") or ""} · saldo {money(d["saldo"])} · cuota {money(d["cuota"])}</span></div>',
            unsafe_allow_html=True
        )

    tab1,tab2=st.tabs(["📸 Subir capturas","✍️ Cargar rápido"])

    with tab1:
        st.write("Subí una o varias capturas del **mismo préstamo o deuda**. La app intenta leer saldo, cuota, cuotas y tasa.")
        shots=st.file_uploader(
            "📎 Elegí capturas",
            type=["png","jpg","jpeg","webp"],
            accept_multiple_files=True,
            key="debt_shots"
        )
        if shots and st.button("🔍 Leer capturas",type="primary",use_container_width=True,key="read_debt_shots"):
            try:
                parsed=[]
                with st.spinner("Leyendo las capturas..."):
                    for f in shots:
                        txt=ocr_image(f.getvalue())
                        parsed.append(parse_loan_screenshot(txt))
                st.session_state["debt_scan_result"]=merge_loan_results(parsed)
            except Exception as e:
                st.error(f"No pude leer las capturas: {e}")

        r=st.session_state.get("debt_scan_result")
        if r:
            st.success("✅ Encontré estos datos. Revisalos antes de guardar.")
            c1,c2=st.columns(2)
            c1.metric("💰 Saldo",money(r["saldo"]) if r["saldo"] else "No encontrado")
            c1.metric("📆 Cuotas restantes",str(r["cuotas_restantes"]) if r["cuotas_restantes"] else "No encontrado")
            c2.metric("💳 Cuota",money(r["cuota"]) if r["cuota"] else "No encontrada")
            c2.metric("📈 TNA",f'{r["tna"]:.1f}%' if r["tna"] is not None else "No encontrada")

            with st.form("save_scanned_debt"):
                name=st.text_input("Nombre",value=r["name"] or "Préstamo")
                entity=st.text_input("Banco / entidad",value=r["entity"] or "")
                saldo=money_input("Saldo pendiente ($)",r["saldo"] or 0,"scan_saldo")
                cuota=money_input("Cuota mensual ($)",r["cuota"] or 0,"scan_cuota")
                rest=st.number_input("Cuotas que faltan",min_value=0,value=int(r["cuotas_restantes"] or 0),step=1)
                tna=st.number_input("Tasa anual (%) — si apareció",min_value=0.0,value=float(r["tna"] or 0),step=1.0)
                ok=st.checkbox("Revisé los datos y están correctos.")
                save=st.form_submit_button("✅ Guardar deuda",type="primary",use_container_width=True)
            if save:
                if not ok:
                    st.warning("Revisá los datos y marcá la confirmación.")
                else:
                    ss=parse_money(saldo)
                    # Guardamos TNA en cft solo como referencia cuando no tenemos CFT.
                    q("debts").insert({
                        "user_id":st.session_state.user_id,
                        "name":name or "Deuda","entity":entity,
                        "saldo":ss,"saldo_inicial":ss,
                        "cuota":parse_money(cuota),
                        "cuotas_restantes":int(rest),
                        "cft":float(tna or 0),
                        "oferta":0,"estado":"Activa"
                    }).execute()
                    st.session_state.pop("debt_scan_result",None)
                    st.success("💚 Deuda guardada.")
                    st.rerun()

            if r.get("evidence"):
                with st.expander("🔎 Ver qué leyó la app"):
                    for e in r["evidence"]:
                        st.write("• "+e)

    with tab2:
        st.write("Solo lo esencial. Lo demás lo podés completar después.")
        with st.form("add_debt_short",clear_on_submit=True):
            name=st.text_input("¿Cómo la reconocés?",placeholder="Ej.: Préstamo BNA")
            saldo=money_input("¿Cuánto falta pagar? ($)",key="d_sal_short")
            cuota=money_input("¿Cuánto pagás por mes? ($)",key="d_cuo_short")
            rest=st.number_input("¿Cuántas cuotas faltan?",min_value=0,value=0,step=1)
            if st.form_submit_button("➕ Guardar deuda",type="primary",use_container_width=True):
                ss=parse_money(saldo)
                q("debts").insert({
                    "user_id":st.session_state.user_id,
                    "name":name or "Deuda","entity":"",
                    "saldo":ss,"saldo_inicial":ss,
                    "cuota":parse_money(cuota),
                    "cuotas_restantes":int(rest),
                    "cft":0,"oferta":0,"estado":"Activa"
                }).execute()
                st.rerun()

    if debts:
        st.markdown("### ✏️ Actualizar")
        for d in debts:
            with st.expander(f"{d['name']} · {money(d['saldo'])}"):
                with st.form(f"edit_{d['id']}"):
                    s2=money_input("Saldo",d["saldo"],f"es_{d['id']}")
                    c2=money_input("Cuota",d["cuota"],f"ec_{d['id']}")
                    estado=st.selectbox(
                        "Estado",
                        ["Activa","En negociación","Pagada","Vencida","Suspendida"],
                        index=["Activa","En negociación","Pagada","Vencida","Suspendida"].index(d["estado"])
                        if d["estado"] in ["Activa","En negociación","Pagada","Vencida","Suspendida"] else 0,
                        key=f"ee_{d['id']}"
                    )
                    if st.form_submit_button("Guardar",use_container_width=True):
                        q("debts").update({"saldo":parse_money(s2),"cuota":parse_money(c2),"estado":estado}).eq("id",d["id"]).execute()
                        st.rerun()

# -------------------- Recurrentes --------------------
elif nav=="🔁 Recurrentes":
    st.subheader("🔁 Pagos recurrentes")
    for r in recurrents: st.markdown(f'<div class="card warn"><b>{r["name"]}</b><br><span class="small">{money(r["importe"])} · {r["frecuencia"]}</span></div>',unsafe_allow_html=True)
    with st.form("add_rec",clear_on_submit=True):
        name=st.text_input("Nombre"); imp=money_input("Importe ($)",key="ri")
        freq=st.selectbox("Frecuencia",["Semanal","Quincenal","Mensual","Bimestral","Trimestral","Anual"])
        if st.form_submit_button("Agregar",type="primary",use_container_width=True):
            q("recurrents").insert({"user_id":st.session_state.user_id,"name":name or "Pago","importe":parse_money(imp),"frecuencia":freq,"activo":True}).execute(); st.rerun()

# -------------------- Personas --------------------
elif nav=="👥 Personas":
    st.subheader("👥 Personas")
    for p in people:
        st.markdown(f'<div class="card {"bad" if p["tipo"]=="Yo debo" else "good"}"><b>{p["name"]}</b><br><span class="small">{p["tipo"]} · {money(p["saldo"])}</span></div>',unsafe_allow_html=True)
    with st.form("add_person",clear_on_submit=True):
        name=st.text_input("Nombre"); tipo=st.selectbox("Relación",["Yo debo","Me deben"]); saldo=money_input("Saldo ($)",key="psi")
        if st.form_submit_button("Agregar",type="primary",use_container_width=True):
            s=parse_money(saldo); q("people").insert({"user_id":st.session_state.user_id,"name":name or "Persona","tipo":tipo,"saldo":s,"saldo_inicial":s,"estado":"Activa"}).execute(); st.rerun()

# -------------------- Ofertas --------------------
elif nav=="⚖️ Ofertas":
    st.subheader("⚖️ Comparar ofertas")
    with st.form("offers"):
        sa=money_input("Saldo actual ($)",key="osa"); ca=money_input("Cuota actual ($)",key="oca"); ma=st.number_input("Meses que faltan",0,120,0,1)
        mn=money_input("Monto nuevo ($)",key="omn"); tna=st.number_input("TNA nueva (%)",0.0,1000.0,0.0,1.0); plazo=st.number_input("Plazo nuevo",1,120,12,1)
        if st.form_submit_button("Comparar",type="primary",use_container_width=True):
            sa,ca,mn=parse_money(sa),parse_money(ca),parse_money(mn); cn=french_payment(mn,tna,plazo)
            st.metric("Cuota nueva estimada",money(cn))
            if ca>0:
                dif=ca-cn
                st.write(f"La cuota {'bajaría' if dif>=0 else 'subiría'} aproximadamente {money(abs(dif))} por mes.")
            if ca>0 and ma>0:
                ta=ca*ma; tn=cn*plazo
                st.write(f"Total aproximado actual: **{money(ta)}** · nueva opción: **{money(tn)}**.")

# -------------------- Plan --------------------
elif nav=="📅 Mi plan":
    st.subheader("📅 Mi plan")
    plan=build_plan(get_profile(),debts)
    if plan["ingresos"]<=0: st.info("Primero cargá tu sueldo en Inicio.")
    elif not debts: st.info("Cargá tus deudas para armar el plan.")
    else:
        for lab,val in [("🏠 Para vivir",plan["vivir"]),("📆 Cuotas obligatorias",plan["cuotas"]),("🩺 Extraordinarios",plan["extra"])]:
            st.markdown(f'<div class="card"><b>{lab}</b><span style="float:right"><b>{money(val)}</b></span></div>',unsafe_allow_html=True)
        if plan["deficit"]>0:
            st.markdown(f'<div class="card bad"><b>⚠️ Este mes faltan {money(plan["deficit"])}</b><br><span class="small">No adelantes deuda. Primero asegurá gastos básicos y vencimientos.</span></div>',unsafe_allow_html=True)
        else:
            if plan["aporte"]>0: st.markdown(f'<div class="card info"><b>🛟 Guardá {money(plan["aporte"])}</b><br><span class="small">Es un colchón pequeño para no volver a pedir prestado ante un imprevisto.</span></div>',unsafe_allow_html=True)
            if plan["target"] and plan["ataque"]>0:
                st.markdown(f'<div class="card good"><b>🎯 Este mes priorizá {plan["target"]["name"]}</b><br><span style="font-size:1.35rem;font-weight:800">{money(plan["ataque"])}</span><br><span class="small">{plan["reason"]}</span></div>',unsafe_allow_html=True)
                st.markdown("### ✅ Instrucciones")
                steps=[f"Separá {money(plan['vivir'])} para vivir.",f"Reservá {money(plan['cuotas'])} para cuotas.",f"Contemplá {money(plan['extra'])} de gastos extraordinarios."]
                if plan["aporte"]>0:steps.append(f"Guardá {money(plan['aporte'])} como colchón.")
                steps.append(f"Destiná hasta {money(plan['ataque'])} a {plan['target']['name']}, luego de confirmar el saldo exacto.")
                for i,s in enumerate(steps,1): st.markdown(f'<div class="card"><b>{i}. {s}</b></div>',unsafe_allow_html=True)

# -------------------- Progreso --------------------
elif nav=="📊 Progreso":
    st.subheader("📊 Progreso")
    actual=total_debt(debts); inicial=sum(num(d.get("saldo_inicial")) for d in debts); eliminado=max(0,inicial-actual); avance=eliminado/inicial if inicial>0 else 0
    a,b,c=st.columns(3); a.metric("Pendiente",money(actual)); b.metric("Eliminado",money(eliminado)); c.metric("Avance",f"{avance*100:.0f}%")
    if inicial>0:st.progress(min(1,max(0,avance)))
    if st.button("📌 Guardar foto de hoy",use_container_width=True):
        q("snapshots").insert({"user_id":st.session_state.user_id,"fecha":str(date.today()),"deuda_total":actual,"fondo":num(profile.get("fondo_actual"))}).execute(); st.rerun()
    if snapshots:
        for s in reversed(snapshots[-6:]): st.markdown(f'<div class="card"><b>{s["fecha"]}</b><br><span class="small">Deuda {money(s["deuda_total"])} · Fondo {money(s["fondo"])}</span></div>',unsafe_allow_html=True)

# -------------------- Ajustes --------------------
elif nav=="⚙️ Ajustes":
    st.subheader("⚙️ Ajustes")
    with st.form("settings"):
        name=st.text_input("Nombre",value=profile.get("name") or "")
        gastos=money_input("Necesario para vivir por mes ($)",profile.get("gastos_vivir"),"ag")
        meta=money_input("Meta de fondo de emergencia ($)",profile.get("meta_emergencia"),"am")
        if st.form_submit_button("Guardar",type="primary",use_container_width=True):
            q("profiles").update({"name":name,"gastos_vivir":parse_money(gastos),"meta_emergencia":parse_money(meta)}).eq("user_id",st.session_state.user_id).execute(); st.rerun()
    st.markdown("### 📱 Tu acceso")
    st.info("Esta versión de prueba no te pide correo ni contraseña. Supabase crea una sesión anónima por detrás para proteger tus datos mientras usás la app.")
    if st.button("🚪 Empezar como otra persona",use_container_width=True):
        st.session_state.user_id=None
        try:
            st.query_params.clear()
        except Exception:
            pass
        st.rerun()

st.caption("Beta comunitaria. La app orienta y organiza; antes de refinanciar o firmar, confirmá siempre los importes con la entidad.")
