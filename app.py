import os, sqlite3
from datetime import date, datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, jsonify, session

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, 'colesmart.db')
APP = Flask(__name__)
APP.secret_key = os.environ.get('COLESMART_SECRET', 'cambia-esta-clave-secreta-antes-de-publicar')
ADMIN_CLAVE = os.environ.get('COLESMART_ADMIN', 'admin123')
MATERIAS = ['Matemáticas','Lengua Castellana','Ciencias Naturales','Ciencias Sociales','Inglés','Educación Física','Tecnología e Informática','Ética y Valores','Educación Artística']
CATEGORIAS = ['Cambio de horario','Actividad','Día sin clase','General']
PERIODOS, APROBACION, ALERTA = 4, 3.0, 3.5

class BaseDatos:
    def __init__(self):
        self.con = sqlite3.connect(DB_PATH)
        self.con.row_factory = sqlite3.Row
        self.con.executescript('''
        CREATE TABLE IF NOT EXISTS estudiantes(codigo TEXT PRIMARY KEY,nombre TEXT NOT NULL,grado TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS notas(codigo TEXT,materia TEXT,periodo INTEGER,nota REAL,PRIMARY KEY(codigo,materia,periodo));
        CREATE TABLE IF NOT EXISTS noticias(id INTEGER PRIMARY KEY AUTOINCREMENT,titulo TEXT NOT NULL,contenido TEXT,categoria TEXT,fecha_evento TEXT,grado TEXT DEFAULT 'Todos',creada TEXT);
        CREATE TABLE IF NOT EXISTS leidas(codigo TEXT,noticia_id INTEGER,PRIMARY KEY(codigo,noticia_id));
        CREATE TABLE IF NOT EXISTS configuracion(clave TEXT PRIMARY KEY,valor TEXT NOT NULL);
        ''')
        if not self.con.execute("SELECT valor FROM configuracion WHERE clave='datos_demo_v2'").fetchone():
            self.seed()
    def q(self, sql, p=()): return self.con.execute(sql,p).fetchall()
    def x(self, sql, p=()): self.con.execute(sql,p); self.con.commit()
    def seed(self):
        alumnos=[('1001','Samuel Tangarife','11-2'),('1002','Hugo Saldarriaga','11-2'),('1003','Juan David Tobar','11-2')]
        for cod,nom,gra in alumnos: self.x('INSERT OR REPLACE INTO estudiantes VALUES(?,?,?)',(cod,nom,gra))
        notas={
        '1001':{'Matemáticas':[4.0,4.1,4.2],'Lengua Castellana':[4.2,4.3,4.1],'Ciencias Naturales':[4.1,4.2,4.3],'Ciencias Sociales':[4.3,4.1,4.2],'Inglés':[4.0,4.2,4.1],'Educación Física':[4.4,4.5,4.3],'Tecnología e Informática':[4.3,4.2,4.4],'Ética y Valores':[4.2,4.3,4.4],'Educación Artística':[4.1,4.2,4.3]},
        '1002':{'Matemáticas':[4.8,4.9,4.7],'Lengua Castellana':[4.7,4.8,4.9],'Ciencias Naturales':[4.8,4.7,4.9],'Ciencias Sociales':[4.6,4.8,4.7],'Inglés':[4.8,4.9,4.8],'Educación Física':[4.9,5.0,4.8],'Tecnología e Informática':[4.8,4.9,4.9],'Ética y Valores':[4.7,4.8,4.9],'Educación Artística':[4.9,4.8,4.9]},
        '1003':{'Matemáticas':[2.8,3.0,3.2],'Lengua Castellana':[3.6,3.5,3.7],'Ciencias Naturales':[3.5,3.6,3.4],'Ciencias Sociales':[3.7,3.6,3.5],'Inglés':[3.4,3.5,3.6],'Educación Física':[3.8,3.7,3.9],'Tecnología e Informática':[3.6,3.7,3.5],'Ética y Valores':[3.7,3.6,3.8],'Educación Artística':[3.8,3.7,3.6]}}
        for cod, mats in notas.items():
            self.x('DELETE FROM notas WHERE codigo=?',(cod,))
            for mat, vals in mats.items():
                for per, nota in enumerate(vals,1): self.x('INSERT OR REPLACE INTO notas VALUES(?,?,?,?)',(cod,mat,per,nota))
        hoy=date.today(); news=[(1,'Cambio de horario','Salida a las 12:00 m. por reunión de docentes','Mañana la jornada termina a las 12:00 m. El restaurante escolar funcionará en el horario habitual.','Todos'),(2,'Actividad','Feria de la Ciencia','Cada grupo presenta su proyecto en el patio central desde las 8:00 a. m. Lleva tu cartelera y tu maqueta.','Todos'),(5,'Día sin clase','No hay clases: jornada pedagógica','Los estudiantes no asisten. Los docentes estarán en jornada de planeación institucional.','Todos'),(8,'Actividad','Salida pedagógica al Zoológico de Cali','Recuerda traer la autorización firmada por tu acudiente y almuerzo.','11-2'),(10,'General','Entrega de boletines del tercer periodo','Los acudientes deben asistir a las 7:00 a. m. con el paz y salvo.','Todos'),(-3,'Actividad','Izada de bandera','Gracias a todos los grupos que participaron.','Todos')]
        if not self.q('SELECT id FROM noticias LIMIT 1'):
            for dias,cat,tit,txt,gra in news: self.x('INSERT INTO noticias(titulo,contenido,categoria,fecha_evento,grado,creada) VALUES(?,?,?,?,?,?)',(tit,txt,cat,(hoy+timedelta(days=dias)).isoformat(),gra,datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        self.x("INSERT OR REPLACE INTO configuracion VALUES('datos_demo_v2','1')")
    def student(self,cod):
        r=self.q('SELECT * FROM estudiantes WHERE codigo=?',(cod,)); return dict(r[0]) if r else None
    def students(self): return [dict(x) for x in self.q('SELECT * FROM estudiantes ORDER BY grado,nombre')]
    def grades(self,cod):
        rows=self.q('SELECT materia,periodo,nota FROM notas WHERE codigo=? ORDER BY materia,periodo',(cod,)); out={}
        for r in rows: out.setdefault(r['materia'],{})[str(r['periodo'])]=r['nota']
        return out
    def news(self, grado=None, codigo=None):
        if grado is None: rows=self.q('SELECT * FROM noticias ORDER BY fecha_evento DESC,id DESC')
        else: rows=self.q("SELECT n.*, (l.noticia_id IS NOT NULL) leida FROM noticias n LEFT JOIN leidas l ON l.noticia_id=n.id AND l.codigo=? WHERE n.grado IN ('Todos',?) ORDER BY n.fecha_evento DESC,n.id DESC",(codigo,grado))
        return [dict(r) for r in rows]

def avg(vals): return round(sum(vals)/len(vals),2) if vals else None
def level(n): return '—' if n is None else ('Superior' if n>=4.6 else 'Alto' if n>=4 else 'Básico' if n>=3 else 'Bajo')
def login_required(fn):
    @wraps(fn)
    def wrap(*a,**k):
        if not session.get('student') and not session.get('admin'): return jsonify(error='Inicia sesión nuevamente.'),401
        return fn(*a,**k)
    return wrap
def admin_required(fn):
    @wraps(fn)
    def wrap(*a,**k):
        if not session.get('admin'): return jsonify(error='Acceso exclusivo de administración.'),403
        return fn(*a,**k)
    return wrap

def db(): return BaseDatos()

@APP.get('/')
def index(): return render_template('index.html')
@APP.post('/api/login')
def login():
    data=request.get_json() or {}; cod=str(data.get('codigo','')).strip(); est=db().student(cod)
    if not est: return jsonify(error='Código no encontrado. Verifícalo con tu docente.'),401
    session.clear(); session['student']=cod
    return jsonify(role='student',student=est)
@APP.post('/api/admin/login')
def admin_login():
    if (request.get_json() or {}).get('clave') != ADMIN_CLAVE: return jsonify(error='La clave no es correcta.'),401
    session.clear(); session['admin']=True
    return jsonify(role='admin')
@APP.post('/api/logout')
def logout(): session.clear(); return jsonify(ok=True)
@APP.get('/api/me')
@login_required
def me():
    if session.get('admin'): return jsonify(role='admin')
    return jsonify(role='student',student=db().student(session['student']))
@APP.get('/api/student/dashboard')
@login_required
def dashboard():
    if not session.get('student'): return jsonify(error='No es una sesión de estudiante.'),403
    d=db(); est=d.student(session['student']); grades=d.grades(est['codigo']); rows=[]
    for m, ps in grades.items(): rows.append({'materia':m,'periodos':ps,'promedio':avg(list(ps.values()))})
    proms=[r['promedio'] for r in rows if r['promedio'] is not None]; general=avg(proms)
    news=d.news(est['grado'],est['codigo']); upcoming=sorted([n for n in news if n['fecha_evento']>=date.today().isoformat()],key=lambda n:n['fecha_evento'])
    return jsonify(student=est,promedio=general,materias_mejorar=sum(1 for x in proms if x<ALERTA),sin_leer=sum(1 for n in news if not n['leida']),proximo=upcoming[0] if upcoming else None,eventos=upcoming[:5],mejorar=[r for r in rows if r['promedio'] is not None and r['promedio']<ALERTA])
@APP.get('/api/student/grades')
@login_required
def student_grades():
    if not session.get('student'): return jsonify(error='No es una sesión de estudiante.'),403
    data=db().grades(session['student']); rows=[]
    for m,p in sorted(data.items()):
        a=avg(list(p.values())); rows.append({'materia':m,'periodos':p,'promedio':a,'desempeno':level(a)})
    return jsonify(rows=rows,aprobacion=APROBACION,alerta=ALERTA)
@APP.get('/api/student/news')
@login_required
def student_news():
    if not session.get('student'): return jsonify(error='No es una sesión de estudiante.'),403
    return jsonify(news=db().news(db().student(session['student'])['grado'],session['student']))
@APP.post('/api/student/news/<int:nid>/read')
@login_required
def read_news(nid):
    if not session.get('student'): return jsonify(error='No es una sesión de estudiante.'),403
    d=db(); d.x('INSERT OR IGNORE INTO leidas VALUES(?,?)',(session['student'],nid)); return jsonify(ok=True)
@APP.post('/api/student/news/read-all')
@login_required
def read_all():
    if not session.get('student'): return jsonify(error='No es una sesión de estudiante.'),403
    d=db(); est=d.student(session['student'])
    for n in d.news(est['grado'],est['codigo']): d.x('INSERT OR IGNORE INTO leidas VALUES(?,?)',(est['codigo'],n['id']))
    return jsonify(ok=True)
@APP.get('/api/admin/students')
@admin_required
def admin_students(): return jsonify(students=db().students())
@APP.post('/api/admin/students')
@admin_required
def save_student():
    x=request.get_json() or {}; cod=str(x.get('codigo','')).strip(); nom=str(x.get('nombre','')).strip().title(); gra=str(x.get('grado','')).strip().upper()
    if not all([cod,nom,gra]): return jsonify(error='Código, nombre y grado son obligatorios.'),400
    db().x('INSERT INTO estudiantes VALUES(?,?,?) ON CONFLICT(codigo) DO UPDATE SET nombre=excluded.nombre,grado=excluded.grado',(cod,nom,gra)); return jsonify(ok=True)
@APP.delete('/api/admin/students/<codigo>')
@admin_required
def delete_student(codigo):
    d=db(); d.x('DELETE FROM estudiantes WHERE codigo=?',(codigo,)); d.x('DELETE FROM notas WHERE codigo=?',(codigo,)); d.x('DELETE FROM leidas WHERE codigo=?',(codigo,)); return jsonify(ok=True)
@APP.get('/api/admin/news')
@admin_required
def admin_news(): return jsonify(news=db().news())
@APP.post('/api/admin/news')
@admin_required
def publish_news():
    x=request.get_json() or {}; tit=str(x.get('titulo','')).strip(); fecha=str(x.get('fecha_evento','')); cat=x.get('categoria'); grado=x.get('grado') or 'Todos'
    try: date.fromisoformat(fecha)
    except ValueError: return jsonify(error='Fecha inválida. Usa AAAA-MM-DD.'),400
    if not tit or cat not in CATEGORIAS: return jsonify(error='Completa el título y selecciona una categoría válida.'),400
    db().x('INSERT INTO noticias(titulo,contenido,categoria,fecha_evento,grado,creada) VALUES(?,?,?,?,?,?)',(tit,x.get('contenido',''),cat,fecha,grado,datetime.now().strftime('%Y-%m-%d %H:%M:%S'))); return jsonify(ok=True)
@APP.delete('/api/admin/news/<int:nid>')
@admin_required
def delete_news(nid):
    d=db(); d.x('DELETE FROM noticias WHERE id=?',(nid,)); d.x('DELETE FROM leidas WHERE noticia_id=?',(nid,)); return jsonify(ok=True)
@APP.get('/api/admin/grades/<codigo>')
@admin_required
def admin_grades(codigo): return jsonify(grades=db().grades(codigo))
@APP.post('/api/admin/grades')
@admin_required
def save_grade():
    x=request.get_json() or {}
    try: nota=round(float(str(x.get('nota','')).replace(',','.')),1); per=int(x.get('periodo'))
    except (ValueError,TypeError): return jsonify(error='La nota o el periodo no son válidos.'),400
    if not 1<=nota<=5 or not 1<=per<=4 or x.get('materia') not in MATERIAS or not db().student(str(x.get('codigo',''))): return jsonify(error='Verifica estudiante, materia, periodo y nota (1.0 a 5.0).'),400
    db().x('INSERT INTO notas VALUES(?,?,?,?) ON CONFLICT(codigo,materia,periodo) DO UPDATE SET nota=excluded.nota',(x['codigo'],x['materia'],per,nota)); return jsonify(ok=True)
@APP.delete('/api/admin/grades')
@admin_required
def delete_grade():
    x=request.get_json() or {}; db().x('DELETE FROM notas WHERE codigo=? AND materia=? AND periodo=?',(x.get('codigo'),x.get('materia'),x.get('periodo'))); return jsonify(ok=True)

if __name__ == '__main__':
    import os
    APP.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=False
    )
