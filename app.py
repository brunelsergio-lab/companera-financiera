
import io
import re
import math
import json
from datetime import date, datetime, timedelta
import calendar
import streamlit as st
import pandas as pd
from io import BytesIO
from pypdf import PdfReader
from PIL import Image
import fitz
from rapidocr import RapidOCR
from supabase import create_client
import extra_streamlit_components as stx

st.set_page_config(page_title="Compañera Financiera", page_icon="🌱", layout="wide")

# -------------------- UI --------------------
st.markdown("""
<style>
:root{
  --bg:#F7F9FC; --card:#FFFFFF; --text:#182230; --muted:#667085;
  --border:#DDE5EF; --blue:#2F6FED; --blue-soft:#EEF4FF;
  --green:#169B62; --green-soft:#ECFDF3; --red:#D64545; --red-soft:#FFF1F1;
  --amber:#B7791F; --amber-soft:#FFF8E7; --lav:#F4F0FF; --control:#F8FAFD;
}
.stApp,[data-testid="stAppViewContainer"]{background:var(--bg)!important;color:var(--text)!important;}
[data-testid="stHeader"]{background:var(--bg)!important;}
.block-container{max-width:940px;padding-top:.7rem;padding-bottom:5rem;}
h1,h2,h3,h4,h5,h6,p,label,span,div{color:var(--text);}
input,textarea{
  background:#FFFFFF!important;color:var(--text)!important;
  -webkit-text-fill-color:var(--text)!important;opacity:1!important;
}
input::placeholder,textarea::placeholder{color:#98A2B3!important;-webkit-text-fill-color:#98A2B3!important;}
div[data-baseweb="input"]>div,div[data-baseweb="select"]>div{
  background:#FFFFFF!important;color:var(--text)!important;
  border:1px solid #C9D4E2!important;border-radius:14px!important;
}
div[data-baseweb="select"] span,[role="listbox"],[role="option"],[role="option"] *{
  color:var(--text)!important;background:#FFFFFF!important;
}
[role="option"]:hover{background:var(--blue-soft)!important;}
[data-testid="stMetric"],div[data-testid="stForm"],.card{
  background:var(--card)!important;border:1px solid var(--border)!important;
  border-radius:18px!important;padding:15px!important;box-shadow:0 3px 12px rgba(15,23,42,.04);
}
.card{margin:10px 0;}
.good{background:var(--green-soft)!important;border-left:5px solid var(--green)!important;}
.bad{background:var(--red-soft)!important;border-left:5px solid var(--red)!important;}
.warn{background:var(--amber-soft)!important;border-left:5px solid var(--amber)!important;}
.info{background:var(--blue-soft)!important;border-left:5px solid var(--blue)!important;}
.small{font-size:.92rem;color:var(--muted)!important;}

.stButton>button,.stFormSubmitButton>button,[data-testid="stDownloadButton"] button{
 min-height:48px;border-radius:14px;font-weight:750;
 background:#F4F7FB!important;color:var(--text)!important;
 border:1px solid #CCD7E5!important;box-shadow:none!important;
}
.stButton>button:hover,.stFormSubmitButton>button:hover,[data-testid="stDownloadButton"] button:hover{
 background:#EAF1FA!important;color:var(--text)!important;border-color:#AABBD0!important;
}
button[kind="primary"],[data-testid="stBaseButton-primary"]{
 background:var(--blue)!important;color:#FFFFFF!important;border-color:var(--blue)!important;
}
button[kind="primary"] *,[data-testid="stBaseButton-primary"] *{color:#FFFFFF!important;}
button[kind="primary"]:hover,[data-testid="stBaseButton-primary"]:hover{
 background:#245FD0!important;color:#FFFFFF!important;border-color:#245FD0!important;
}

/* Uploader: nunca negro en tema claro */
[data-testid="stFileUploaderDropzone"],
[data-testid="stFileUploader"] section{
 background:#F8FBFF!important;color:var(--text)!important;
 border:1px dashed #A9BCD3!important;border-radius:16px!important;
}
[data-testid="stFileUploaderDropzone"] *,
[data-testid="stFileUploader"] section *{color:var(--text)!important;}
[data-testid="stFileUploaderDropzone"] button{
 background:var(--blue-soft)!important;color:#245FD0!important;border:1px solid #C8D8FF!important;
}
/* archivo ya elegido */
[data-testid="stFileUploaderFile"],
[data-testid="stFileUploaderFile"] *,
[data-testid="stFileUploaderFileName"],
[data-testid="stFileUploaderFileName"] *{
 background:#EEF4FF!important;color:var(--text)!important;
}

/* Expanders: claros en interfaz clara */
[data-testid="stExpander"]{
 background:#F5F8FC!important;border:1px solid var(--border)!important;border-radius:14px!important;
}
[data-testid="stExpander"] details,
[data-testid="stExpander"] summary,
[data-testid="stExpander"] details > div{
 background:#F5F8FC!important;color:var(--text)!important;
}
[data-testid="stExpander"] *{color:var(--text)!important;}

[data-testid="stAlert"]{border-radius:14px!important;}
[data-testid="stTabs"] button{color:var(--text)!important;}
div[role="radiogroup"]{display:flex;overflow-x:auto;gap:6px;padding-bottom:4px;scrollbar-width:none;}
div[role="radiogroup"] label{
 background:#FFFFFF!important;border:1px solid var(--border)!important;
 border-radius:999px!important;padding:7px 12px!important;white-space:nowrap!important;
}
div[role="radiogroup"] label *{color:var(--text)!important;}

@media (prefers-color-scheme: dark){
 :root{
   --bg:#0F1722; --card:#172230; --text:#EEF3F8; --muted:#A7B3C3;
   --border:#314155; --blue:#6EA0FF; --blue-soft:#182B46;
   --green:#50C98A; --green-soft:#163127; --red:#FF7B7B; --red-soft:#3A2023;
   --amber:#F4C66A; --amber-soft:#352B18; --control:#1C2938;
 }
 .stApp,[data-testid="stAppViewContainer"],[data-testid="stHeader"]{background:var(--bg)!important;color:var(--text)!important;}
 h1,h2,h3,h4,h5,h6,p,label,span,div{color:var(--text);}
 input,textarea{background:#182536!important;color:var(--text)!important;-webkit-text-fill-color:var(--text)!important;}
 div[data-baseweb="input"]>div,div[data-baseweb="select"]>div{background:#182536!important;border-color:#40536B!important;}
 div[data-baseweb="select"] span,[role="listbox"],[role="option"],[role="option"] *{background:#182536!important;color:var(--text)!important;}
 [data-testid="stMetric"],div[data-testid="stForm"],.card{background:var(--card)!important;border-color:var(--border)!important;}
 .stButton>button,.stFormSubmitButton>button,[data-testid="stDownloadButton"] button{background:#1B2A3A!important;color:var(--text)!important;border-color:#40536B!important;}
 [data-testid="stFileUploaderDropzone"],[data-testid="stFileUploader"] section{background:#172536!important;border-color:#536A84!important;}
 [data-testid="stFileUploaderFile"],[data-testid="stFileUploaderFile"] *{background:#20344B!important;color:var(--text)!important;}
 [data-testid="stExpander"],[data-testid="stExpander"] details,[data-testid="stExpander"] summary,[data-testid="stExpander"] details > div{background:#172536!important;color:var(--text)!important;}
 div[role="radiogroup"] label{background:#172536!important;border-color:#40536B!important;}
}
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

def format_money_state(key):
    raw=str(st.session_state.get(key,"") or "").strip()
    if not raw:
        st.session_state[key]=""
        return
    val=parse_money(raw)
    st.session_state[key]=money(val)

def money_input(label, value=0, key=None, placeholder="$ 100.000"):
    initial="" if num(value)==0 else money(value)
    return st.text_input(label,value=initial,key=key,placeholder=placeholder)

def money_input_live(label, value=0, key=None, placeholder="$ 100.000"):
    """Formatea a $ 1.000.000 al salir del campo, sin exigir Enter."""
    if key not in st.session_state:
        st.session_state[key]="" if num(value)==0 else money(value)
    return st.text_input(
        label,
        key=key,
        placeholder=placeholder,
        on_change=format_money_state,
        args=(key,)
    )

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

# Cookie persistente: permite volver otro día desde el mismo navegador
# sin pedir correo ni contraseña.
cookie_manager = stx.CookieManager(key="cf_cookie_manager")

if "access_token" not in st.session_state:
    st.session_state.access_token=None
if "refresh_token" not in st.session_state:
    st.session_state.refresh_token=None
if "user_id" not in st.session_state:
    st.session_state.user_id=None

def save_browser_session(access_token, refresh_token):
    expires=datetime.now()+timedelta(days=180)
    cookie_manager.set(
        "cf_access_token", access_token, key="set_cf_access",
        expires_at=expires, secure=True, same_site="strict"
    )
    cookie_manager.set(
        "cf_refresh_token", refresh_token, key="set_cf_refresh",
        expires_at=expires, secure=True, same_site="strict"
    )

def clear_browser_session():
    try: cookie_manager.delete("cf_access_token", key="del_cf_access")
    except Exception: pass
    try: cookie_manager.delete("cf_refresh_token", key="del_cf_refresh")
    except Exception: pass

def restore_browser_session():
    access=st.session_state.access_token or cookie_manager.get("cf_access_token")
    refresh=st.session_state.refresh_token or cookie_manager.get("cf_refresh_token")
    if not access or not refresh:
        return False
    try:
        res=sb.auth.set_session(access,refresh)
        user=sb.auth.get_user()
        if user and user.user:
            st.session_state.access_token=res.access_token if hasattr(res,"access_token") else access
            st.session_state.refresh_token=res.refresh_token if hasattr(res,"refresh_token") else refresh
            st.session_state.user_id=user.user.id
            # Renovamos cookie si Supabase refrescó tokens.
            save_browser_session(st.session_state.access_token,st.session_state.refresh_token)
            return True
    except Exception:
        clear_browser_session()
    return False

restore_browser_session()

def q(table):
    return sb.table(table)

# Beta simple: sin correo ni contraseña.
# Se crea un identificador aleatorio y se conserva en la URL (?u=...).
# Así cada tester puede guardar sus datos sin usar el flujo de Auth.
import uuid

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
    if st.session_state.access_token and st.session_state.refresh_token:
        save_browser_session(st.session_state.access_token,st.session_state.refresh_token)

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
            total_cuotas=cuota*rest
            if total_cuotas < saldo:
                score=3500
                reason=(f"Los datos cargados necesitan una revisión: {rest} cuotas de {money(cuota)} "
                        f"suman {money(total_cuotas)}, menos que el saldo informado de {money(saldo)}. "
                        "Antes de decidir, confirmá saldo y cantidad de cuotas.")
            else:
                est=estimate_financing_cost(saldo,cuota,rest)
                score=4000+(est["tea"] or 0)
                reason=(f"Sin tasa informada, usamos saldo, cuota y {rest} cuotas para orientarte. "
                        f"Si todo se mantiene igual, pagarías cerca de {money(est['total'])} en total, "
                        f"aproximadamente {money(est['extra'])} por encima del saldo actual.")
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


def debt_strategy_order(ds):
    """Orden práctico: ofertas de cancelación, costo/tasa más alta y luego saldo menor."""
    rows=[]
    for d in open_debts(ds):
        saldo=num(d.get("saldo")); cuota=num(d.get("cuota")); tasa=num(d.get("cft")); oferta=num(d.get("oferta"))
        if oferta>0 and oferta<saldo:
            priority=(0, -(saldo-oferta), saldo)
            why=f"Hay una oferta para cerrar {money(saldo)} pagando {money(oferta)}."
        elif tasa>0:
            priority=(1,-tasa,saldo)
            why=f"Tiene una tasa/costo informado de {tasa:.1f}% y conviene vigilarla primero."
        else:
            priority=(2,saldo,0)
            why="No hay tasa cargada; se prioriza un saldo manejable para liberar una cuota más rápido."
        rows.append((priority,d,why))
    rows.sort(key=lambda x:x[0])
    return rows

def long_term_roadmap(profile, ds, months_limit=120):
    """
    Mapa orientativo de caja. No intenta reproducir el contrato bancario:
    usa saldos cargados, cuotas y excedente mensual para enseñar una secuencia.
    """
    p=build_plan(profile,ds)
    active=[dict(d) for d in open_debts(ds)]
    if not active:
        return {"months":0,"milestones":[],"capacity":0,"order":[]}
    base_extra=max(0,p["ataque"])
    # Si no hay excedente, las cuotas siguen siendo la capacidad ordinaria.
    total_capacity=total_installments(active)+base_extra
    order=debt_strategy_order(active)
    if total_capacity<=0:
        return {"months":None,"milestones":[],"capacity":0,"order":order}

    balances={d["id"]:num(d.get("saldo")) for d in active}
    monthly_min={d["id"]:num(d.get("cuota")) for d in active}
    milestones=[]
    month=0

    while month<months_limit and any(v>0.5 for v in balances.values()):
        month+=1
        # 1) cuotas normales a todas las deudas
        freed=0.0
        for d in active:
            did=d["id"]
            if balances[did]<=0: continue
            pay=min(monthly_min[did],balances[did])
            balances[did]-=pay
            if balances[did]<=0.5:
                balances[did]=0
                freed += monthly_min[did]
                if not any(m["id"]==did for m in milestones):
                    milestones.append({"id":did,"name":d["name"],"month":month,"freed":monthly_min[did]})

        # 2) excedente + cuotas que se liberan van al objetivo prioritario
        extra=base_extra+freed
        if extra>0:
            current_order=[x for x in debt_strategy_order([d for d in active if balances[d["id"]]>0]) if balances[x[1]["id"]]>0]
            for _,d,_why in current_order:
                if extra<=0: break
                did=d["id"]
                pay=min(extra,balances[did])
                balances[did]-=pay
                extra-=pay
                if balances[did]<=0.5:
                    balances[did]=0
                    if not any(m["id"]==did for m in milestones):
                        milestones.append({"id":did,"name":d["name"],"month":month,"freed":monthly_min[did]})
                    extra += monthly_min[did]

    remaining=sum(balances.values())
    return {
        "months": month if remaining<=0.5 else None,
        "milestones":sorted(milestones,key=lambda x:x["month"]),
        "capacity":total_capacity,
        "extra":base_extra,
        "order":order,
        "remaining":remaining
    }

def habit_checklist():
    return [
        ("Día de cobro","Separá primero el dinero para vivir y las cuotas obligatorias."),
        ("Una vez por semana","Revisá saldos 5 minutos. No hace falta mirar las deudas todos los días."),
        ("Antes de una compra en cuotas","Preguntate si retrasa tu fecha estimada de salida de deudas."),
        ("Cuando cobres un extra","Decidí una parte para tu colchón y otra para la deuda prioritaria."),
        ("Al cerrar el mes","Actualizá saldos y guardá una foto de progreso. El plan se recalcula."),
    ]


MONTHS_ES = ["enero","febrero","marzo","abril","mayo","junio",
             "julio","agosto","septiembre","octubre","noviembre","diciembre"]

def month_label(dt):
    return f"{MONTHS_ES[dt.month-1].capitalize()} {dt.year}"

def personalized_rules(profile, ds):
    rules=[
        "No crear deuda nueva de consumo mientras el plan esté activo.",
        "Separar primero el dinero para vivir, salud y servicios esenciales.",
        "Pagar los vencimientos obligatorios antes de hacer pagos extraordinarios.",
        "Cada cuota que termina se reutiliza para acelerar la siguiente deuda; no se transforma en gasto nuevo.",
        "Antes de precancelar una deuda, pedir el monto exacto y comparar si realmente reduce el costo total.",
    ]
    fondo=num(profile.get("fondo_actual")); vivir=num(profile.get("gastos_vivir")); meta=num(profile.get("meta_emergencia"))
    objetivo=max(meta, vivir*2 if vivir>0 else 0)
    if objetivo>0 and fondo<objetivo:
        rules.append(f"Construir gradualmente un fondo de seguridad de al menos {money(objetivo)}.")
    if any(num(d.get("oferta"))>0 for d in open_debts(ds)):
        rules.append("Cuando exista una quita u oferta de cancelación, exigir la propuesta por escrito y confirmar libre deuda antes de pagar.")
    return rules

def build_personal_month_plan(profile, ds, months=18):
    """
    Crea un plan pedagógico, mes a mes, basado en los datos actuales.
    Se recalcula cada vez que cambian ingresos, gastos o saldos.
    """
    base=build_plan(profile,ds)
    road=long_term_roadmap(profile,ds,months_limit=max(120,months*6))
    order=road.get("order",[])
    milestones={m["month"]:m for m in road.get("milestones",[])}
    start=date.today().replace(day=1)
    out=[]

    for i in range(1,months+1):
        y=start.year + (start.month-1+i-1)//12
        m=(start.month-1+i-1)%12+1
        dt=date(y,m,1)
        title=month_label(dt)
        actions=[]

        # Base monthly discipline
        actions.append(f"Separá {money(base['vivir'])} para vivir antes de destinar dinero extra a deudas.")
        if base["cuotas"]>0:
            actions.append(f"Reservá aproximadamente {money(base['cuotas'])} para cuotas obligatorias.")
        if base["extra"]>0:
            actions.append(f"Contemplá {money(base['extra'])} de gastos extraordinarios cargados.")
        if base["aporte"]>0 and i<=3:
            actions.append(f"Destiná hasta {money(base['aporte'])} a tu fondo de seguridad mientras siga incompleto.")

        if i in milestones:
            mm=milestones[i]
            actions.append(f"Objetivo del mes: terminar **{mm['name']}**. Al cerrarla se liberarían cerca de {money(mm['freed'])} por mes.")
            actions.append("La cuota liberada pasa automáticamente a la siguiente deuda del plan.")

        if order:
            idx=min(i-1,len(order)-1)
            _,target,why=order[idx]
            if i==1:
                actions.append(f"Deuda prioritaria: **{target['name']}**. {why}")
            elif i<=len(order):
                actions.append(f"Seguimiento: revisá si **{target['name']}** sigue siendo la mejor deuda para concentrar el excedente.")

        if i==1:
            actions.append("Objetivo de cierre: llegar al próximo cobro sin crear deuda nueva.")
        elif i==2:
            actions.append("Revisá los saldos reales y corregí cualquier diferencia en la app.")
        elif i==3:
            actions.append("Comprobá qué cuotas ya terminaron y sumalas al dinero de ataque del mes siguiente.")
        elif i%3==0:
            actions.append("Revisión trimestral: actualizá saldos, cuotas y condiciones de precancelación.")
        elif i%6==0:
            actions.append("Revisión semestral: compará cuánto capital bajó y si conviene cambiar el orden de ataque.")
        elif i==12:
            actions.append("Balance anual: contá cuántas deudas cerraste, cuánto flujo mensual liberaste y cuánto aumentó tu reserva.")

        out.append({"month":i,"title":title,"actions":actions})
    return out

def priority_steps(profile, ds):
    steps=[
        "No caer en mora nueva.",
        "Cubrir vivienda, comida, salud y servicios esenciales.",
        "Pagar cuotas y vencimientos del mes.",
        "Proteger o construir un fondo de seguridad.",
    ]
    for _,d,why in debt_strategy_order(ds):
        steps.append(f"Atacar {d['name']}: {why}")
    return steps

def projection_rows(profile, ds, months_limit=120):
    """Proyección simple del saldo usando cuotas + excedente; no inventa intereses no informados."""
    active=[dict(d) for d in open_debts(ds)]
    if not active:
        return [],[]
    p=build_plan(profile,ds)
    extra=max(0,p["ataque"])
    rows=[{"Mes":0,"Saldo":sum(num(d["saldo"]) for d in active)}]
    milestones=[]
    prev_names={d["name"] for d in active}
    for month in range(1,months_limit+1):
        # cuotas normales
        for d in active:
            d["saldo"]=max(0,num(d["saldo"])-min(num(d["cuota"]),num(d["saldo"])))
        # excedente a prioridad actual
        alive=[d for d in active if num(d["saldo"])>0]
        if alive and extra>0:
            ranked=debt_strategy_order(alive)
            target=ranked[0][1] if ranked else alive[0]
            target["saldo"]=max(0,num(target["saldo"])-min(extra,num(target["saldo"])))
        alive=[d for d in active if num(d["saldo"])>0]
        names={d["name"] for d in alive}
        for finished in sorted(prev_names-names):
            milestones.append({"month":month,"name":finished})
        prev_names=names
        total=sum(num(d["saldo"]) for d in alive)
        rows.append({"Mes":month,"Saldo":total})
        active=alive
        if total<=0:
            break
    return rows,milestones

def plan_text_export(profile, ds):
    plan=build_plan(profile,ds)
    road=long_term_roadmap(profile,ds)
    monthly=build_personal_month_plan(profile,ds,months=min(24,max(12,road.get("months") or 18)))
    lines=[
        "COMPAÑERA FINANCIERA — MI PLAN PERSONAL",
        f"Generado: {date.today().strftime('%d/%m/%Y')}",
        "",
        "1. MI SITUACIÓN ACTUAL",
        f"Deuda pendiente: {money(total_debt(ds))}",
        f"Cuotas mensuales: {money(total_installments(ds))}",
        f"Dinero protegido para vivir: {money(plan['vivir'])}",
        f"Margen estimado para acelerar: {money(max(0,plan['ataque']))}",
        "",
        "2. REGLAS DEL PLAN",
    ]
    lines += [f"- {x}" for x in personalized_rules(profile,ds)]
    lines += ["","3. ORDEN DE PRIORIDAD"]
    lines += [f"{i}. {x}" for i,x in enumerate(priority_steps(profile,ds),1)]
    lines += ["","4. PLAN MES A MES"]
    for item in monthly:
        lines.append("")
        lines.append(item["title"].upper())
        lines += [f"- {a.replace('**','')}" for a in item["actions"]]
    lines += [
        "","IMPORTANTE",
        "Este es un mapa orientativo basado en tus datos actuales. Si cambia tu situación, actualizá los datos y el plan se recalcula.",
        "Antes de refinanciar, precancelar o firmar una propuesta, confirmá importes, tasas y condiciones con la entidad."
    ]
    return "\n".join(lines)

def plan_pdf_bytes(profile, ds):
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.enums import TA_CENTER
        buf=BytesIO()
        doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=16*mm,bottomMargin=16*mm)
        styles=getSampleStyleSheet()
        title=ParagraphStyle("CFTitle",parent=styles["Title"],alignment=TA_CENTER,fontSize=20,leading=24,spaceAfter=10)
        h=ParagraphStyle("CFH",parent=styles["Heading2"],fontSize=13,leading=16,spaceBefore=8,spaceAfter=6)
        body=ParagraphStyle("CFBody",parent=styles["BodyText"],fontSize=10.5,leading=15,spaceAfter=5)
        story=[Paragraph("Compañera Financiera",title),Paragraph("Mi plan personal para salir de deudas",styles["Heading2"]),
               Paragraph(f"Generado el {date.today().strftime('%d/%m/%Y')}",body),Spacer(1,6)]
        txt=plan_text_export(profile,ds)
        for line in txt.splitlines()[3:]:
            if re.match(r"^\d+\.",line):
                story.append(Paragraph(line,h))
            elif line.isupper() and len(line)<45:
                story.append(Paragraph(line,h))
            elif line.startswith("- "):
                story.append(Paragraph("• "+line[2:],body))
            elif line.strip():
                story.append(Paragraph(line,body))
            else:
                story.append(Spacer(1,4))
        doc.build(story)
        return buf.getvalue()
    except Exception:
        return None

def offer_traffic_light(profile, ds, new_payment, new_total=0, current_total=0):
    p=build_plan(profile,ds)
    ingresos=p["ingresos"]; vivir=p["vivir"]; extra=p["extra"]
    # Existing installments excluding the debt being refinanced cannot be known reliably here,
    # so use total current installments as conservative baseline.
    other=max(0,total_installments(ds))
    after=ingresos-vivir-extra-other-new_payment
    survival=max(vivir*0.10, ingresos*0.05, 1)
    if ingresos<=0 or vivir<=0:
        return "⚪ Faltan datos","Completá ingreso y dinero necesario para vivir para evaluar si la cuota es sostenible.",after
    if after<0:
        return "🔴 Te deja demasiado ajustado",f"La cuota supera tu margen estimado por {money(abs(after))}. No sacrifiques gastos esenciales para sostenerla.",after
    if after<survival:
        return "🟡 Revisar con cuidado",f"Después de tus gastos y obligaciones quedarían cerca de {money(after)}. El margen es muy pequeño para absorber imprevistos.",after
    msg=f"Después de tus gastos y obligaciones quedarían cerca de {money(after)} de margen estimado."
    if new_total and current_total and new_total>current_total:
        msg+=f" Además, el costo total estimado sería {money(new_total-current_total)} mayor que continuar con el esquema cargado."
        return "🟡 Revisar con cuidado",msg,after
    return "🟢 Parece sostenible",msg+" Confirmá CFT, seguros, comisiones y costo total antes de aceptar.",after


def current_cycle_key():
    today=date.today()
    return f"{today.year:04d}-{today.month:02d}"

def due_auto_debits(ds):
    """Devuelve débitos automáticos que ya deberían haberse producido este mes y aún no fueron confirmados."""
    today=date.today()
    cycle=current_cycle_key()
    out=[]
    for d in open_debts(ds):
        if not d.get("automatic_debit"):
            continue
        day=int(num(d.get("debit_day")))
        if day<=0:
            continue
        if today.day >= day and (d.get("last_payment_month") or "") != cycle:
            out.append(d)
    return out

def debts_needing_monthly_check(ds):
    """Entre el 1 y el 15, recuerda revisar deudas no automáticas que aún no fueron confirmadas este mes."""
    today=date.today()
    if today.day>15:
        return []
    cycle=current_cycle_key()
    return [
        d for d in open_debts(ds)
        if not d.get("automatic_debit") and (d.get("last_payment_month") or "") != cycle
    ]

def confirm_debt_payment(d):
    """
    Confirma una cuota efectivamente pagada.
    No descuenta automáticamente por fecha: el usuario confirma que el débito/pago ocurrió.
    """
    old_balance=num(d.get("saldo"))
    installment=max(0,num(d.get("cuota")))
    remaining=max(0,int(num(d.get("cuotas_restantes"))))
    paid=min(old_balance,installment) if installment>0 else 0
    new_balance=max(0,old_balance-paid)
    new_remaining=max(0,remaining-1) if remaining>0 else 0
    new_state="Pagada" if new_balance<=0.5 or (remaining>0 and new_remaining==0) else d.get("estado","Activa")

    q("debts").update({
        "saldo":new_balance,
        "cuotas_restantes":new_remaining,
        "last_payment_month":current_cycle_key(),
        "estado":new_state
    }).eq("id",d["id"]).execute()

    try:
        q("payments").insert({
            "user_id":st.session_state.user_id,
            "debt_id":d["id"],
            "debt_name":d["name"],
            "amount":paid,
            "balance_before":old_balance,
            "balance_after":new_balance,
            "payment_date":str(date.today()),
            "cycle_key":current_cycle_key(),
            "source":"automatic" if d.get("automatic_debit") else "manual"
        }).execute()
    except Exception:
        pass
    return paid,new_balance,new_state

def payments_this_month():
    try:
        return q("payments").select("*").eq("user_id",st.session_state.user_id).eq("cycle_key",current_cycle_key()).order("payment_date").execute().data or []
    except Exception:
        return []

def month_update_summary(before_total, after_total, count):
    reduced=max(0,before_total-after_total)
    if reduced<=0:
        return "Actualizamos tu estado financiero. Seguimos desde acá."
    return f"🌱 ¡Bien! Confirmaste {count} pago(s) y tu deuda registrada bajó aproximadamente {money(reduced)}."

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

def parse_debt_document(text):
    """Reconoce datos comunes de préstamos, refinanciaciones y resúmenes."""
    saldo,ev_s=after_money(text,[
        r"saldo\s+de\s+capital", r"saldo\s+capital", r"capital\s+pendiente",
        r"saldo\s+actual", r"total\s+(?:a\s+)?pagar", r"importe\s+refinanciado"
    ])
    cuota,ev_c=after_money(text,[
        r"(?:monto|importe)\s+de\s+la\s+cuota",
        r"cuota\s+(?:mensual|actual)",
        r"pago\s+m[ií]nimo"
    ])
    tna,ev_t=after_pct(text,[r"TNA\s+Vigente",r"TNA",r"tasa\s+nominal\s+anual"])
    cft,ev_cf=after_pct(text,[r"CFT(?:\s*\(?TEA\)?)?",r"costo\s+financiero\s+total"])

    pagadas=totales=None
    ev_q=""
    m=re.search(r"(?is)cuotas\s+pagas\s*[:\-]?\s*([0-9]+)\s*/\s*([0-9]+)",text)
    if m:
        pagadas,totales=int(m.group(1)),int(m.group(2)); ev_q=m.group(0).strip()
    if totales is None:
        m=re.search(r"(?is)(?:cantidad\s+de\s+cuotas|cuotas)\s*[:\-]?\s*([0-9]{1,3})",text)
        if m:
            totales=int(m.group(1)); pagadas=0; ev_q=m.group(0).strip()
    if totales is None:
        m=re.search(r"(?is)pr[oó]xima\s+cuota\s*[:\-]?\s*([0-9]+)\s+(?:de|/)\s*([0-9]+)",text)
        if m:
            pagadas=max(0,int(m.group(1))-1); totales=int(m.group(2)); ev_q=m.group(0).strip()

    rest=max(0,totales-pagadas) if totales is not None and pagadas is not None else 0

    entity=""
    if re.search(r"(?i)\bBNA\b|BANCO\s+DE\s+LA\s+NACI[ÓO]N|BANCO\s+NACI[ÓO]N",text): entity="BNA"
    elif re.search(r"(?i)NARANJA\s*X",text): entity="Naranja X"
    elif re.search(r"(?i)MERCADO\s*PAGO",text): entity="Mercado Pago"

    name=""
    for line in [" ".join(x.split()) for x in text.splitlines() if x.strip()]:
        if re.search(r"(?i)\b(pr[eé]stamo|refinanciaci[oó]n|convenio|consumo\s+tc|naci[oó]n\s+ahora)\b",line) and len(line)<120:
            name=line
            break
    if not name:
        name="Deuda"

    return {
        "name":name,"entity":entity,"saldo":saldo,"cuota":cuota,
        "tna":tna,"cft":cft,"cuotas_pagadas":pagadas,
        "cuotas_totales":totales,"cuotas_restantes":rest,
        "evidence":[x for x in [ev_s,ev_c,ev_t,ev_cf,ev_q] if x]
    }

def merge_debt_documents(items):
    out={"name":"","entity":"","saldo":None,"cuota":None,"tna":None,"cft":None,
         "cuotas_pagadas":None,"cuotas_totales":None,"cuotas_restantes":0,"evidence":[]}
    for r in items:
        for k in ["name","entity","saldo","cuota","tna","cft","cuotas_pagadas","cuotas_totales"]:
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
        nombre=st.text_input("👤 ¿Cómo te llamás?",value="")
        edad_txt=st.text_input("🎂 ¿Qué edad tenés?",value="")
        if st.form_submit_button("🌱 Empezar",type="primary",use_container_width=True):
            nombre_ok=nombre.strip()
            try:
                edad=int(edad_txt.strip())
            except Exception:
                edad=None

            if not nombre_ok:
                st.warning("Escribí tu nombre para empezar.")
            elif edad is None:
                st.warning("Escribí tu edad.")
            elif edad < 13 or edad > 100:
                st.warning("Ingresá una edad válida.")
            else:
                try:
                    create_simple_profile(nombre_ok,edad)
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
    st.caption("Completá estos datos y la app recalcula tu situación. Los importes se formatean al pasar al siguiente campo.")

    auto_due=due_auto_debits(debts)
    manual_due=debts_needing_monthly_check(debts)
    month_payments=payments_this_month()

    if auto_due:
        st.markdown(
            '<div class="card info"><b>🏦 Hoy toca revisar tus débitos automáticos</b><br>'
            '<span class="small">No voy a descontarlos solo por la fecha: primero confirmá que el banco realmente los cobró.</span></div>',
            unsafe_allow_html=True
        )
        for d in auto_due:
            c1,c2=st.columns([8,2],vertical_alignment="center")
            c1.markdown(f"**{d['name']}** · cuota {money(d['cuota'])} · débito previsto día {int(num(d.get('debit_day')))}")
            if c2.button("✅ Se debitó",key=f"confirm_auto_{d['id']}",use_container_width=True):
                before=total_debt(debts)
                confirm_debt_payment(d)
                fresh=get_rows("debts")
                after=total_debt(fresh)
                st.session_state["payment_success_message"]=month_update_summary(before,after,1)
                st.rerun()

    if manual_due:
        with st.expander(f"📅 Revisión mensual · {len(manual_due)} deuda(s) pendientes de confirmar"):
            st.write("Entre los días 1 y 15 te recuerdo revisar estas deudas:")
            for d in manual_due:
                c1,c2=st.columns([8,2],vertical_alignment="center")
                c1.write(f"**{d['name']}** · {money(d['cuota'])}")
                if c2.button("✅ Ya pagué",key=f"confirm_manual_{d['id']}",use_container_width=True):
                    before=total_debt(debts)
                    confirm_debt_payment(d)
                    fresh=get_rows("debts")
                    after=total_debt(fresh)
                    st.session_state["payment_success_message"]=month_update_summary(before,after,1)
                    st.rerun()

    if st.session_state.get("payment_success_message"):
        st.success(st.session_state.pop("payment_success_message"))

    sueldo=money_input_live("💰 Sueldo / ingreso principal ($)",profile.get("sueldo"),"home_sueldo")
    gastos=money_input_live("🏠 ¿Cuánto necesitás para vivir este mes? ($)",profile.get("gastos_vivir"),"home_gastos")
    extras=money_input_live("🎁 Ingresos extra ($)",profile.get("extras"),"home_extras")
    ext=money_input_live("🩺 Gastos extraordinarios ($)",profile.get("extraordinarios"),"home_ext")
    fondo=money_input_live("🛟 Fondo de emergencia actual ($)",profile.get("fondo_actual"),"home_fondo")

    if st.button("💾 Guardar y recalcular",type="primary",use_container_width=True,key="save_home"):
        q("profiles").update({
            "sueldo":parse_money(sueldo),
            "gastos_vivir":parse_money(gastos),
            "extras":parse_money(extras),
            "extraordinarios":parse_money(ext),
            "fondo_actual":parse_money(fondo)
        }).eq("user_id",st.session_state.user_id).execute()
        st.rerun()

    plan=build_plan(get_profile(),debts)
    x,y,z=st.columns(3)
    x.metric("💰 Ingresos",money(plan["ingresos"]))
    y.metric("🏠 Para vivir",money(plan["vivir"]))
    z.metric("📆 Cuotas",money(plan["cuotas"]))

    if month_payments:
        total_paid=sum(num(x.get("amount")) for x in month_payments)
        st.markdown(
            f'<div class="card good"><b>✅ Este mes ya confirmaste {len(month_payments)} pago(s)</b><br>'
            f'<span class="small">Registraste aproximadamente {money(total_paid)} en cuotas pagadas. '
            'Tu plan y tu progreso ya usan los saldos actualizados.</span></div>',
            unsafe_allow_html=True
        )

    if plan["vivir"]<=0:
        st.markdown(
            '<div class="card warn"><b>🏠 Falta un dato importante</b><br>'
            '<span class="small">Decime cuánto necesitás para vivir antes de recomendarte dinero para adelantar deudas.</span></div>',
            unsafe_allow_html=True
        )
    elif plan["target"]:
        st.markdown(
            f'<div class="card good"><b>🎯 Prioridad sugerida: {plan["target"]["name"]}</b><br>'
            f'<span class="small">{plan["reason"]}</span></div>',
            unsafe_allow_html=True
        )

# -------------------- Lector gratuito --------------------
elif nav=="📄 Leer resumen GRATIS":
    st.subheader("📄 Entender mi resumen")
    st.write("Subí PDF, PNG, JPG/JPEG o WEBP. Además de leerlo, la app te explica qué significa y qué camino parece más razonable según tus datos cargados.")
    up=st.file_uploader("📎 Subí el archivo",type=["pdf","png","jpg","jpeg","webp"],key="summary_upload")

    if up and st.button("🔍 Leer y orientarme",type="primary",use_container_width=True,key="read_summary"):
        try:
            with st.spinner("Leyendo y analizando..."):
                txt,n,method=extract_local(up)
                st.session_state.local_text=txt
                st.session_state.local_method=method
                st.session_state.local_parse=parse_summary(txt)
        except Exception as e:
            st.error(f"No pude leerlo: {e}")

    r=st.session_state.get("local_parse")
    if r:
        st.success(f"✅ Lectura por {st.session_state.get('local_method','método local')}. Revisá los números.")
        a,b=st.columns(2)
        a.metric("🧾 Total",money(r["total"]) if r["total"] else "No encontrado")
        b.metric("🪙 Pago mínimo",money(r["minimum"]) if r["minimum"] else "No encontrado")

        if r["cft"] is not None:
            st.write(f"**Costo financiero anual encontrado:** {r['cft']:.1f}%")

        total=num(r.get("total")); minimo=num(r.get("minimum")); cft=num(r.get("cft"))
        p=get_profile()
        ingresos=num(p.get("sueldo"))+num(p.get("extras"))
        vivir=num(p.get("gastos_vivir"))
        extraordinarios=num(p.get("extraordinarios"))
        otras_cuotas=total_installments(debts)
        margen=max(0,ingresos-vivir-extraordinarios-otras_cuotas)

        st.markdown("### 🧭 ¿Qué significa para vos?")
        if total>0 and minimo>0:
            resto=max(0,total-minimo)
            pct=(minimo/total*100) if total else 0
            st.markdown(
                f'<div class="card info"><b>Si pagás solamente el mínimo</b><br>'
                f'<span class="small">El mínimo representa aproximadamente {pct:.0f}% del resumen. '
                f'Quedarían cerca de {money(resto)} sin cancelar, antes de los costos de financiación.</span></div>',
                unsafe_allow_html=True
            )

        if vivir<=0 or ingresos<=0:
            st.markdown(
                '<div class="card warn"><b>Para darte una recomendación personal falta completar Inicio</b><br>'
                '<span class="small">Necesito al menos tu ingreso del mes y cuánto necesitás para vivir. '
                'Con eso puedo comparar el resumen contra tu margen real.</span></div>',
                unsafe_allow_html=True
            )
        elif total<=0:
            st.markdown(
                '<div class="card warn"><b>No pude identificar el total con suficiente seguridad</b><br>'
                '<span class="small">Revisá el documento o cargá ese valor manualmente antes de tomar una decisión.</span></div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(f"**Después de cubrir lo básico y las otras cuotas registradas, tu margen estimado es {money(margen)}.**")

            if margen >= total:
                st.markdown(
                    f'<div class="card good"><b>✅ Camino que parece más conveniente: cancelar el total</b><br>'
                    f'<span class="small">Con los datos cargados podrías cubrir {money(total)} sin usar el dinero reservado para vivir ni tus otras cuotas. '
                    'Pagar el total evita financiar este saldo y, en general, es la opción de menor costo.</span></div>',
                    unsafe_allow_html=True
                )
            elif minimo>0 and margen >= minimo:
                extra=max(0,margen-minimo)
                st.markdown(
                    f'<div class="card warn"><b>⚠️ Podés cubrir el mínimo, pero no conviene detenerse ahí si podés pagar más</b><br>'
                    f'<span class="small">Tu margen estimado es {money(margen)}. El mínimo es {money(minimo)}. '
                    f'Si podés destinar hasta {money(margen)} sin tocar gastos básicos, reducirías más rápido el saldo financiado. '
                    'Evitá seguir usando la tarjeta mientras ordenás este saldo.</span></div>',
                    unsafe_allow_html=True
                )
            elif minimo>0 and margen < minimo:
                st.markdown(
                    f'<div class="card bad"><b>🚨 El mínimo supera tu margen disponible</b><br>'
                    f'<span class="small">Tu margen estimado es {money(margen)} y el pago mínimo es {money(minimo)}. '
                    'No sacrifiques vivienda, comida, salud o servicios esenciales para cubrirlo. '
                    'Antes del vencimiento, consultá alternativas con la entidad y compará cuota, plazo y costo total antes de aceptar una refinanciación.</span></div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div class="card info"><b>💡 Prioridad: evitar financiar más de lo necesario</b><br>'
                    '<span class="small">Como no pude identificar un pago mínimo, usá el total y tu margen mensual como referencia. '
                    'Si no podés cancelar todo, confirmá con la entidad las condiciones de financiación antes de decidir.</span></div>',
                    unsafe_allow_html=True
                )

            if cft>=100:
                st.markdown(
                    f'<div class="card bad"><b>📈 Atención al costo financiero: {cft:.1f}% anual</b><br>'
                    '<span class="small">Es un costo anual muy elevado. No significa que te cobren ese porcentaje completo este mes, '
                    'pero sí que mantener saldo financiado puede resultar caro. Si comparás otra opción, mirá CFT, cuota, plazo y total final.</span></div>',
                    unsafe_allow_html=True
                )

        if r["evidence"]:
            with st.expander("🔎 Ver de dónde salieron los datos"):
                for e in r["evidence"]:
                    st.write(e)

# -------------------- Deudas --------------------
elif nav=="💳 Deudas":
    st.subheader("💳 Mis deudas")
    st.markdown(
        '<div class="card info"><b>💚 Subí lo que tengas</b><br>'
        '<span class="small">Una foto, una captura, un PDF o un resumen. '
        'La app intenta completar los datos por vos y vos los revisás antes de guardar.</span></div>',
        unsafe_allow_html=True
    )

    if open_debts(debts):
        st.markdown("### Tus deudas")
        for d in open_debts(debts):
            c_info,c_edit,c_del=st.columns([8,1,1],vertical_alignment="center")
            with c_info:
                st.markdown(
                    f'<div class="card bad"><b>{d["name"]}</b><br>'
                    f'<span class="small">{d.get("entity") or ""} · saldo {money(d["saldo"])} · cuota {money(d["cuota"])}'
                    f'{" · débito automático día "+str(int(num(d.get("debit_day")))) if d.get("automatic_debit") else ""}</span></div>',
                    unsafe_allow_html=True
                )
            with c_edit:
                if st.button("✏️",key=f"edit_debt_btn_{d['id']}",help="Editar"):
                    st.session_state["edit_debt_id"]=d["id"]
                    st.session_state.pop("delete_debt_id",None)
                    st.rerun()
            with c_del:
                if st.button("🗑️",key=f"del_debt_btn_{d['id']}",help="Quitar"):
                    st.session_state["delete_debt_id"]=d["id"]
                    st.session_state.pop("edit_debt_id",None)
                    st.rerun()

            if st.session_state.get("edit_debt_id")==d["id"]:
                with st.form(f"inline_edit_debt_{d['id']}"):
                    st.markdown(f"**Editar {d['name']}**")
                    ename=st.text_input("Nombre",value=d["name"],key=f"en_{d['id']}")
                    esaldo=money_input("Saldo pendiente",d["saldo"],f"esaldo_{d['id']}")
                    ecuota=money_input("Cuota mensual",d["cuota"],f"ecuota_{d['id']}")
                    erest=st.number_input("Cuotas restantes",min_value=0,value=int(num(d.get("cuotas_restantes"))),step=1,key=f"erest_{d['id']}")
                    eauto=st.checkbox("🏦 Débito automático",value=bool(d.get("automatic_debit")),key=f"eauto_{d['id']}")
                    eday=st.number_input("Día del débito",min_value=1,max_value=28,value=int(num(d.get("debit_day")) or 1),step=1,disabled=not eauto,key=f"eday_{d['id']}")
                    a,b=st.columns(2)
                    save=a.form_submit_button("💾 Guardar",use_container_width=True)
                    cancel=b.form_submit_button("Cancelar",use_container_width=True)
                if save:
                    q("debts").update({
                        "name":ename or d["name"],"saldo":parse_money(esaldo),
                        "cuota":parse_money(ecuota),"cuotas_restantes":int(erest),
                        "automatic_debit":bool(eauto),"debit_day":int(eday) if eauto else None
                    }).eq("id",d["id"]).execute()
                    st.session_state.pop("edit_debt_id",None); st.rerun()
                if cancel:
                    st.session_state.pop("edit_debt_id",None); st.rerun()

            if st.session_state.get("delete_debt_id")==d["id"]:
                st.warning(f"¿Quitar **{d['name']}**? Esta acción elimina la deuda guardada.")
                a,b=st.columns(2)
                if a.button("Sí, quitar",key=f"confirm_del_debt_{d['id']}",use_container_width=True):
                    q("debts").delete().eq("id",d["id"]).execute()
                    st.session_state.pop("delete_debt_id",None); st.rerun()
                if b.button("Cancelar",key=f"cancel_del_debt_{d['id']}",use_container_width=True):
                    st.session_state.pop("delete_debt_id",None); st.rerun()

    tab_auto,tab_fast=st.tabs(["📸 Subir lo que tengo","⚡ Cargar en 30 segundos"])

    with tab_auto:
        st.write("Acepta **PDF, foto o captura**. Si son varias imágenes del mismo préstamo, subilas juntas.")
        files=st.file_uploader(
            "📎 Elegir archivos",
            type=["pdf","png","jpg","jpeg","webp"],
            accept_multiple_files=True,
            key="debt_documents"
        )

        # La cámara NO se abre automáticamente.
        # El usuario decide explícitamente si quiere usarla.
        if "show_debt_camera" not in st.session_state:
            st.session_state.show_debt_camera = False

        if not st.session_state.show_debt_camera:
            if st.button("📷 Quiero sacar una foto", use_container_width=True, key="open_debt_camera"):
                st.session_state.show_debt_camera = True
                st.rerun()
            camera = None
        else:
            st.info("La cámara se activa solamente porque vos la elegiste.")
            camera = st.camera_input("📷 Sacar foto", key="debt_camera")
            if st.button("✖️ Cerrar cámara", use_container_width=True, key="close_debt_camera"):
                st.session_state.show_debt_camera = False
                st.rerun()

        inputs=list(files or [])
        if camera is not None:
            inputs.append(camera)

        if inputs and st.button("✨ Completar por mí",type="primary",use_container_width=True,key="auto_debt"):
            try:
                found=[]
                with st.spinner("Estoy leyendo lo que subiste..."):
                    for f in inputs:
                        txt,_,_=extract_local(f)
                        found.append(parse_debt_document(txt))
                st.session_state["auto_debt_result"]=merge_debt_documents(found)
            except Exception as e:
                st.error(f"No pude leer uno de los archivos: {e}")

        r=st.session_state.get("auto_debt_result")
        if r:
            st.success("Encontré estos datos. Corregí lo que haga falta y confirmá.")
            a,b=st.columns(2)
            a.metric("💰 Falta pagar",money(r["saldo"]) if r["saldo"] else "No encontrado")
            b.metric("💳 Cuota",money(r["cuota"]) if r["cuota"] else "No encontrada")

            with st.form("confirm_auto_debt"):
                name=st.text_input("¿Cómo querés llamarla?",value=r["name"] or "Deuda")
                entity=st.text_input("Banco / entidad",value=r["entity"] or "")
                saldo=money_input("Saldo pendiente ($)",r["saldo"] or 0,"auto_saldo")
                cuota=money_input("Cuota mensual ($)",r["cuota"] or 0,"auto_cuota")
                rest=st.number_input("Cuotas que faltan",min_value=0,value=int(r["cuotas_restantes"] or 0),step=1)
                auto=st.checkbox("🏦 Se paga por débito automático")
                debit_day=st.number_input("Día habitual del débito",min_value=1,max_value=28,value=1,step=1,disabled=not auto)
                with st.expander("Datos opcionales que encontré"):
                    cft=st.number_input("Costo financiero anual (%)",min_value=0.0,value=float(r["cft"] or 0),step=1.0)
                    tna=st.number_input("TNA (%)",min_value=0.0,value=float(r["tna"] or 0),step=1.0)
                confirmed=st.checkbox("Revisé los datos.")
                save=st.form_submit_button("💚 Guardar esta deuda",type="primary",use_container_width=True)
            if save:
                if not confirmed:
                    st.warning("Marcá que revisaste los datos antes de guardar.")
                else:
                    ss=parse_money(saldo)
                    q("debts").insert({
                        "user_id":st.session_state.user_id,
                        "name":name or "Deuda","entity":entity,
                        "saldo":ss,"saldo_inicial":ss,
                        "cuota":parse_money(cuota),
                        "cuotas_restantes":int(rest),
                        "cft":float(cft or tna or 0),
                        "oferta":0,"estado":"Activa",
                        "automatic_debit":bool(auto),
                        "debit_day":int(debit_day) if auto else None
                    }).execute()
                    st.session_state.pop("auto_debt_result",None)
                    st.rerun()

            if r.get("evidence"):
                with st.expander("🔎 Qué pudo leer"):
                    for e in r["evidence"]:
                        st.write("• "+e)

    with tab_fast:
        st.write("Si no tenés ningún archivo, alcanza con estos datos.")
        with st.form("quick_debt",clear_on_submit=True):
            name=st.text_input("Nombre",placeholder="Ej.: Préstamo BNA")
            saldo=money_input("¿Cuánto falta pagar? ($)",key="quick_saldo")
            cuota=money_input("¿Cuánto pagás por mes? ($)",key="quick_cuota")
            rest=st.number_input("¿Cuántas cuotas faltan?",min_value=0,value=0,step=1)
            auto=st.checkbox("🏦 Se paga por débito automático",key="quick_auto")
            debit_day=st.number_input("Día habitual del débito",min_value=1,max_value=28,value=1,step=1,disabled=not auto,key="quick_debit_day")
            if st.form_submit_button("💚 Guardar",type="primary",use_container_width=True):
                ss=parse_money(saldo)
                q("debts").insert({
                    "user_id":st.session_state.user_id,
                    "name":name or "Deuda","entity":"",
                    "saldo":ss,"saldo_inicial":ss,
                    "cuota":parse_money(cuota),
                    "cuotas_restantes":int(rest),
                    "cft":0,"oferta":0,"estado":"Activa",
                    "automatic_debit":bool(auto),
                    "debit_day":int(debit_day) if auto else None
                }).execute()
                st.rerun()

# -------------------- Recurrentes --------------------
elif nav=="🔁 Recurrentes":
    st.subheader("🔁 Pagos recurrentes")
    st.caption("Servicios y gastos que se repiten. Podés corregirlos o quitarlos desde la misma fila.")

    for r in recurrents:
        c_info,c_edit,c_del=st.columns([8,1,1],vertical_alignment="center")
        with c_info:
            st.markdown(
                f'<div class="card warn"><b>{r["name"]}</b><br>'
                f'<span class="small">{money(r["importe"])} · {r["frecuencia"]}</span></div>',
                unsafe_allow_html=True
            )
        with c_edit:
            if st.button("✏️",key=f"edit_rec_btn_{r['id']}",help="Editar"):
                st.session_state["edit_rec_id"]=r["id"]; st.session_state.pop("delete_rec_id",None); st.rerun()
        with c_del:
            if st.button("🗑️",key=f"del_rec_btn_{r['id']}",help="Quitar"):
                st.session_state["delete_rec_id"]=r["id"]; st.session_state.pop("edit_rec_id",None); st.rerun()

        if st.session_state.get("edit_rec_id")==r["id"]:
            with st.form(f"edit_rec_{r['id']}"):
                rn=st.text_input("Nombre",value=r["name"],key=f"rn_{r['id']}")
                ri=money_input("Importe",r["importe"],f"rimp_{r['id']}")
                opts=["Semanal","Quincenal","Mensual","Bimestral","Trimestral","Anual"]
                rf=st.selectbox("Frecuencia",opts,index=opts.index(r["frecuencia"]) if r.get("frecuencia") in opts else 2,key=f"rf_{r['id']}")
                a,b=st.columns(2)
                save=a.form_submit_button("💾 Guardar",use_container_width=True)
                cancel=b.form_submit_button("Cancelar",use_container_width=True)
            if save:
                q("recurrents").update({"name":rn or r["name"],"importe":parse_money(ri),"frecuencia":rf}).eq("id",r["id"]).execute()
                st.session_state.pop("edit_rec_id",None); st.rerun()
            if cancel:
                st.session_state.pop("edit_rec_id",None); st.rerun()

        if st.session_state.get("delete_rec_id")==r["id"]:
            st.warning(f"¿Quitar **{r['name']}** de tus pagos recurrentes?")
            a,b=st.columns(2)
            if a.button("Sí, quitar",key=f"confirm_del_rec_{r['id']}",use_container_width=True):
                q("recurrents").delete().eq("id",r["id"]).execute()
                st.session_state.pop("delete_rec_id",None); st.rerun()
            if b.button("Cancelar",key=f"cancel_del_rec_{r['id']}",use_container_width=True):
                st.session_state.pop("delete_rec_id",None); st.rerun()

    st.markdown("### ➕ Agregar")
    with st.form("add_rec",clear_on_submit=True):
        name=st.text_input("Nombre")
        imp=money_input("Importe ($)",key="ri")
        freq=st.selectbox("Frecuencia",["Semanal","Quincenal","Mensual","Bimestral","Trimestral","Anual"])
        if st.form_submit_button("Agregar",type="primary",use_container_width=True):
            q("recurrents").insert({
                "user_id":st.session_state.user_id,"name":name or "Pago",
                "importe":parse_money(imp),"frecuencia":freq,"activo":True
            }).execute()
            st.rerun()

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
    st.subheader("🚦 Semáforo de decisiones")
    st.caption("Probá una propuesta antes de aceptarla. La app compara la cuota con tu margen real y te explica qué mirar.")

    with st.form("offers"):
        sa=money_input("Saldo actual ($)",key="osa")
        ca=money_input("Cuota actual ($)",key="oca")
        ma=st.number_input("Meses que faltan",0,120,0,1)
        mn=money_input("Monto a refinanciar / financiar ($)",key="omn")
        tna=st.number_input("TNA nueva (%)",0.0,1000.0,0.0,1.0)
        plazo=st.number_input("Plazo nuevo (meses)",1,120,12,1)
        submit=st.form_submit_button("🚦 Analizar propuesta",type="primary",use_container_width=True)

    if submit:
        sa,ca,mn=parse_money(sa),parse_money(ca),parse_money(mn)
        cn=french_payment(mn,tna,plazo)
        actual_total=ca*ma if ca>0 and ma>0 else 0
        nuevo_total=cn*plazo
        label,msg,after=offer_traffic_light(get_profile(),debts,cn,nuevo_total,actual_total)

        klass="good" if label.startswith("🟢") else ("bad" if label.startswith("🔴") else "warn")
        st.markdown(f'<div class="card {klass}"><b style="font-size:1.15rem">{label}</b><br><span class="small">{msg}</span></div>',unsafe_allow_html=True)

        x,y,z=st.columns(3)
        x.metric("Cuota nueva estimada",money(cn))
        y.metric("Margen después de pagarla",money(max(0,after)))
        z.metric("Total nuevo estimado",money(nuevo_total))

        if ca>0:
            dif=ca-cn
            st.write(f"La cuota {'bajaría' if dif>=0 else 'subiría'} aproximadamente **{money(abs(dif))}** por mes.")
        if actual_total>0:
            dif_total=nuevo_total-actual_total
            st.write(f"Comparación aproximada de pagos restantes: actual **{money(actual_total)}** · propuesta **{money(nuevo_total)}**.")
            if dif_total>0:
                st.warning(f"⚠️ La propuesta implicaría aproximadamente {money(dif_total)} más en pagos nominales.")
            else:
                st.success(f"✅ La propuesta implicaría aproximadamente {money(abs(dif_total))} menos en pagos nominales.")

        st.info("El semáforo evalúa sostenibilidad con los datos cargados. No reemplaza el contrato: confirmá CFT, seguros, comisiones, gastos y condiciones de precancelación con la entidad.")

# -------------------- Plan --------------------
elif nav=="📅 Mi plan":
    st.subheader("📅 Tu plan personal para salir de deudas")
    st.caption("Este plan no es una foto de un solo mes. Se recalcula cuando cambian tus ingresos, gastos, cuotas o saldos.")

    p=get_profile()
    active=open_debts(debts)
    plan=build_plan(p,debts)

    if plan["ingresos"]<=0:
        st.info("Primero cargá tu ingreso en Inicio.")
    elif plan["vivir"]<=0:
        st.warning("Primero completá cuánto necesitás para vivir. Ese dinero se protege antes de acelerar deudas.")
    elif not active:
        st.success("🎉 No tenés deudas abiertas cargadas.")
    else:
        road=long_term_roadmap(p,debts)
        monthly=build_personal_month_plan(p,debts,months=18)

        st.markdown(
            '<div class="card good"><b>🎯 Objetivo general</b><br>'
            '<span class="small">Recuperar liquidez, cerrar deudas una por una y evitar volver a financiar consumo.</span></div>',
            unsafe_allow_html=True
        )

        st.markdown("### 1. 📸 Tu situación actual")
        a,b,c=st.columns(3)
        a.metric("Deuda pendiente",money(total_debt(debts)))
        b.metric("Cuotas mensuales",money(total_installments(debts)))
        c.metric("Margen para acelerar",money(max(0,plan["ataque"])))

        for d in active:
            treatment="Pagar cuota normal."
            if num(d.get("oferta"))>0 and num(d.get("oferta"))<num(d.get("saldo")):
                treatment="Comparar la oferta de cancelación y exigirla por escrito."
            elif num(d.get("cft"))>0:
                treatment="Vigilar el costo y comparar precancelación antes de adelantar."
            elif num(d.get("cuotas_restantes"))<=3 and num(d.get("cuotas_restantes"))>0:
                treatment="Deuda corta: terminar y reutilizar esa cuota."
            st.markdown(
                f'<div class="card"><b>{d["name"]}</b><br>'
                f'<span class="small">Saldo {money(d["saldo"])} · cuota {money(d["cuota"])} · '
                f'{int(num(d.get("cuotas_restantes")))} cuotas restantes<br><b>Tratamiento:</b> {treatment}</span></div>',
                unsafe_allow_html=True
            )

        st.markdown("### 2. 🧱 Reglas hasta quedar libre")
        for rule in personalized_rules(p,debts):
            st.markdown(f'<div class="card"><b>•</b> <span class="small">{rule}</span></div>',unsafe_allow_html=True)

        st.markdown("### 3. 🗓️ Plan mes a mes")
        st.write("Los montos cambian; la secuencia del plan no. Actualizá tus saldos y esta hoja se recalcula.")
        for item in monthly:
            with st.expander(f"{item['title']}"):
                for action in item["actions"]:
                    st.markdown(f"- {action}")

        st.markdown("### 4. 📊 Tablero de seguimiento")
        st.write("Al cerrar cada mes, revisá estos cinco puntos:")
        cols=st.columns(5)
        labels=["Ingreso neto","Gastos + salud","Cuotas","Extra a deuda","Reserva cierre"]
        vals=[
            money(plan["ingresos"]),
            money(plan["vivir"]+plan["extra"]),
            money(plan["cuotas"]),
            money(max(0,plan["ataque"])),
            money(num(p.get("fondo_actual")))
        ]
        for col,label,val in zip(cols,labels,vals):
            col.metric(label,val)

        st.markdown("### 5. 🥇 Orden de prioridad")
        for i,step in enumerate(priority_steps(p,debts),1):
            st.markdown(f'<div class="card"><b>{i})</b> <span class="small">{step}</span></div>',unsafe_allow_html=True)

        st.markdown("### 6. 🔁 Hábito de salida")
        for title,desc in habit_checklist():
            st.markdown(f'<div class="card info"><b>{title}</b><br><span class="small">{desc}</span></div>',unsafe_allow_html=True)

        st.markdown(
            '<div class="card good"><b style="font-size:1.15rem">Cada deuda que termina no libera dinero para gastar: '
            'libera dinero para terminar la siguiente.</b></div>',
            unsafe_allow_html=True
        )

        if road.get("months"):
            st.markdown(
                f'<div class="card warn"><b>⏳ Horizonte orientativo actual: alrededor de {road["months"]} meses</b><br>'
                '<span class="small">No es una promesa. Cambia con intereses, ingresos, gastos y condiciones del acreedor. '
                'La app recalcula el camino cuando actualizás tus datos.</span></div>',
                unsafe_allow_html=True
            )


        st.markdown("### 7. 📄 Llevate tu plan")
        st.caption("Guardalo para consultarlo sin abrir la app o compartilo por el medio que prefieras.")
        export_txt=plan_text_export(p,debts)
        pdf_bytes=plan_pdf_bytes(p,debts)
        c1,c2=st.columns(2)
        c1.download_button("📝 Descargar en texto",data=export_txt,file_name="mi_plan_companera_financiera.txt",mime="text/plain",use_container_width=True)
        if pdf_bytes:
            c2.download_button("📄 Descargar PDF",data=pdf_bytes,file_name="mi_plan_companera_financiera.pdf",mime="application/pdf",use_container_width=True)
        else:
            c2.info("Para habilitar PDF agregá reportlab a requirements.txt.")

# -------------------- Progreso --------------------
elif nav=="📊 Progreso":
    st.subheader("📊 Tu camino hacia $0")
    st.caption("Cada pago que confirmás actualiza el saldo, las cuotas restantes, el plan y esta proyección.")
    p=get_profile()
    actual=total_debt(debts)
    inicial=sum(num(d.get("saldo_inicial")) for d in debts)
    eliminado=max(0,inicial-actual)
    avance=eliminado/inicial if inicial>0 else 0

    a,b,c=st.columns(3)
    a.metric("Pendiente",money(actual))
    b.metric("Ya eliminaste",money(eliminado))
    c.metric("Avance",f"{avance*100:.0f}%")
    if inicial>0:
        st.progress(min(1,max(0,avance)))

    rows,milestones=projection_rows(p,debts)
    if rows and num(p.get("gastos_vivir"))>0 and (num(p.get("sueldo"))+num(p.get("extras")))>0:
        df=pd.DataFrame(rows).set_index("Mes")
        st.markdown("### 📉 Proyección orientativa")
        st.line_chart(df["Saldo"],use_container_width=True)
        st.caption("Este es un mapa orientativo basado en tus datos actuales. Si un mes no podés hacer un pago extra, actualizá tus números: el gráfico se recalcula y seguimos desde ahí.")

        if milestones:
            st.markdown("### 🎉 Hitos del camino")
            for m in milestones:
                st.markdown(f'<div class="card good"><b>Mes {m["month"]}: ¡adiós a {m["name"]}!</b><br><span class="small">La cuota que se libera pasa a fortalecer el siguiente objetivo.</span></div>',unsafe_allow_html=True)
    elif debts:
        st.info("Para proyectar el camino necesito tu ingreso y cuánto necesitás para vivir.")

    st.markdown("### 🧪 ¿Qué pasa si pongo un poco más?")
    extra_sim=st.number_input("Extra mensual para simular ($)",min_value=0,step=5000,value=0,key="sim_extra")
    if rows:
        base_months=max(0,len(rows)-1)
        if extra_sim>0:
            # simulate without touching stored profile
            pp=dict(p)
            pp["extras"]=num(pp.get("extras"))+extra_sim
            sim_rows,_=projection_rows(pp,debts)
            sim_months=max(0,len(sim_rows)-1)
            saved=max(0,base_months-sim_months)
            st.markdown(
                f'<div class="card info"><b>Con {money(extra_sim)} extra por mes</b><br>'
                f'<span class="small">La proyección pasaría de aproximadamente {base_months} meses a {sim_months} meses. '
                f'Podrías acortar el camino cerca de <b>{saved} meses</b>. Esto es una simulación: todavía no modifica tu plan real.</span></div>',
                unsafe_allow_html=True
            )

    if st.button("📌 Guardar foto de hoy",use_container_width=True):
        q("snapshots").insert({"user_id":st.session_state.user_id,"fecha":str(date.today()),"deuda_total":actual,"fondo":num(profile.get("fondo_actual"))}).execute()
        st.rerun()

    if snapshots:
        st.markdown("### 🗂️ Tus registros")
        for snap in reversed(snapshots[-6:]):
            st.markdown(f'<div class="card"><b>{snap["fecha"]}</b><br><span class="small">Deuda {money(snap["deuda_total"])} · Fondo {money(snap["fondo"])}</span></div>',unsafe_allow_html=True)

# -------------------- Ajustes --------------------
elif nav=="⚙️ Ajustes":
    st.subheader("⚙️ Ajustes")
    with st.form("settings"):
        name=st.text_input("Nombre",value=profile.get("name") or "")
        gastos=money_input("Necesario para vivir por mes ($)",profile.get("gastos_vivir"),"ag")
        meta=money_input("Meta de fondo de emergencia ($)",profile.get("meta_emergencia"),"am")
        if st.form_submit_button("Guardar",type="primary",use_container_width=True):
            q("profiles").update({"name":name,"gastos_vivir":parse_money(gastos),"meta_emergencia":parse_money(meta)}).eq("user_id",st.session_state.user_id).execute(); st.rerun()
    st.markdown("### 🔐 Privacidad")
    st.markdown(
        '<div class="card info"><b>Tu información financiera es privada.</b><br>'
        '<span class="small">Tus datos se utilizan para construir tu plan y mostrarte tus propios resultados. '
        'Cada usuario accede únicamente a su información. No mostramos tus datos financieros a otros usuarios.</span></div>',
        unsafe_allow_html=True
    )
    st.markdown("### 📱 Tus datos en este dispositivo")
    st.info("La app recuerda tu sesión en este navegador durante la beta. Si volvés desde este mismo dispositivo, debería recuperar tus datos automáticamente.")
    if st.button("🚪 Empezar como otra persona",use_container_width=True):
        try: sb.auth.sign_out()
        except Exception: pass
        clear_browser_session()
        st.session_state.user_id=None
        st.session_state.access_token=None
        st.session_state.refresh_token=None
        st.rerun()

st.caption("Beta comunitaria. La app orienta y organiza; antes de refinanciar o firmar, confirmá siempre los importes con la entidad.")
