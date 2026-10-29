# Instalación y ejecución

## Requisitos

Antes de comenzar, asegúrate de tener instalado:

- [Python](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads/)

## Instalación

### 1. Clonar el repositorio

```
git clone https://github.com/bruno0808/proyecto-inicial-grupo-5
cd proyecto-inicial-grupo-5
```

### 2. Crear un entorno virtual

```
python -m venv venv
```

### 3. Activar el entorno virtual

En Windows:

```
venv\Scripts\activate
```

En Linux o macOS:

```
source venv/bin/activate
```

### 4. Instalar las dependencias

```
pip install -r requirements.txt
```

### 5. Preparar la base de datos

```
python manage.py migrate
```

## Ejecución

Inicia el servidor de desarrollo:

```
python manage.py runserver
```

Abre la siguiente dirección en tu navegador:

[http://127.0.0.1:8000/](http://127.0.0.1:8000/)

Para detener el servidor, presiona `Ctrl + C` en la terminal.
