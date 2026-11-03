# ColeSmart Web

Versión web de ColeSmart: HTML, CSS y JavaScript en el navegador; Python con Flask como servidor; SQLite para guardar estudiantes, notas, noticias y lecturas.

## 1. Requisitos
- Python 3.10 o superior.
- Navegador actualizado.

## 2. Instalar y ejecutar
Abre una terminal dentro de esta carpeta y ejecuta:

```bash
python -m venv .venv
```

En Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

En Linux/macOS activa el entorno con `source .venv/bin/activate` y después ejecuta los dos últimos comandos.

Abre `http://127.0.0.1:5000` en el navegador.

## 3. Usuarios de demostración
- Estudiante Samuel: código `1001`.
- Estudiante Hugo: código `1002`.
- Estudiante Juan David Tobar: código `1003`.
- Administración: clave inicial `admin123`.

La primera ejecución crea automáticamente `colesmart.db` y carga los datos de demostración. No borres ese archivo si quieres conservar los cambios.

## 4. Archivos
- `app.py`: servidor Flask, rutas y operaciones SQLite.
- `templates/index.html`: estructura HTML.
- `static/styles.css`: diseño visual.
- `static/app.js`: interacciones y llamadas al servidor.
- `colesmart.db`: base SQLite, se crea al ejecutar.

## 5. Cómo se comunican
El navegador muestra las páginas y ejecuta JavaScript. JavaScript consulta rutas como `/api/student/grades`. Flask recibe la solicitud, consulta o modifica SQLite y devuelve datos JSON. La contraseña administrativa se comprueba en Python; la sesión se mantiene en el servidor mediante una cookie.

## Seguridad antes de publicar en internet
Esta es una versión educativa/local. Antes de desplegarla en internet, configura variables de entorno `COLESMART_SECRET` y `COLESMART_ADMIN` con valores privados, desactiva `debug`, usa HTTPS y añade contraseñas individuales seguras para estudiantes y docentes. No uses la clave de demostración en un sitio público.
