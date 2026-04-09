"""
Script para extraer datos del sitio web https://www.consumovehicular.cl/comparador

Este script usa un enfoque híbrido:
1. Intenta encontrar APIs públicas del sitio
2. Analiza la estructura del sitio para identificar endpoints de datos
3. Extrae información disponible públicamente

Uso:
    python scrape_alternativo.py
"""

import json
import time
import requests
from urllib.parse import urljoin, urlparse


def buscar_api_endpoints(base_url):
    """Intenta encontrar endpoints de API comunes"""
    
    endpoints_posibles = [
        "/api/vehiculos",
        "/api/comparador", 
        "/api/listado",
        "/api/catalogo",
        "/api/modelos",
        "/api/marcas",
        "/api/data",
        "/api/v1/vehiculos",
        "/api/v1/comparador",
        "/datos/vehiculos.json",
        "/datos/comparador.json",
        "/assets/data.json",
        "/static/data.json",
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
    }
    
    resultados = []
    
    print("Buscando endpoints de API...")
    for endpoint in endpoints_posibles:
        url = urljoin(base_url, endpoint)
        try:
            response = requests.get(url, headers=headers, verify=False, timeout=5)
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'json' in content_type or response.text.strip().startswith('{') or response.text.strip().startswith('['):
                    print(f"✓ API encontrada: {url}")
                    try:
                        data = response.json()
                        resultados.append({
                            "endpoint": url,
                            "datos": data,
                            "tipo": "JSON"
                        })
                    except:
                        resultados.append({
                            "endpoint": url,
                            "datos": response.text[:500],
                            "tipo": "texto"
                        })
        except Exception as e:
            pass
    
    return resultados


def analizar_html_estatico(html_content, base_url):
    """Analiza el HTML en busca de datos embebidos o scripts con información"""
    
    import re
    
    datos_encontrados = {}
    
    # Buscar datos en variables JavaScript
    patrones_js = [
        r'window\.__INITIAL_STATE__\s*=\s*({[^}]+})',
        r'window\.data\s*=\s*({[^}]+})',
        r'var\s+data\s*=\s*({[^}]+})',
        r'"initialState"\s*:\s*({[^}]+})',
    ]
    
    for patron in patrones_js:
        matches = re.findall(patron, html_content, re.IGNORECASE)
        if matches:
            datos_encontrados['variables_js'] = matches
    
    # Buscar URLs de API en el código JavaScript
    urls_api = re.findall(r'(https?://[^\s\'"]+/api/[^\s\'"]+)', html_content)
    if urls_api:
        datos_encontrados['urls_api_encontradas'] = list(set(urls_api))
    
    # Buscar referencias a archivos JSON
    json_files = re.findall(r'([\'"]([^\'"]+\.json)[\'"])', html_content)
    if json_files:
        datos_encontrados['archivos_json'] = [f[1] for f in json_files[:10]]
    
    return datos_encontrados


def extraer_informacion_pagina():
    """Extrae toda la información disponible de la página"""
    
    base_url = "https://www.consumovehicular.cl"
    url_comparador = f"{base_url}/comparador"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
    }
    
    print("=" * 60)
    print("Extracción de datos - Consumo Vehicular")
    print("=" * 60)
    
    resultado_final = {
        "fecha_extraccion": time.strftime("%Y-%m-%d %H:%M:%S"),
        "url_base": base_url,
        "apis_encontradas": [],
        "analisis_html": {},
        "informacion_general": {}
    }
    
    # 1. Obtener el HTML de la página principal
    print(f"\n1. Obteniendo página: {url_comparador}")
    try:
        response = requests.get(url_comparador, headers=headers, verify=False, timeout=15)
        html_content = response.text
        
        print(f"   Estado: {response.status_code}")
        print(f"   Tamaño: {len(html_content)} caracteres")
        
        # Guardar HTML
        with open("consumovehicular_html.txt", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("   ✓ HTML guardado en 'consumovehicular_html.txt'")
        
        # 2. Analizar HTML en busca de datos
        print("\n2. Analizando HTML en busca de datos...")
        analisis = analizar_html_estatico(html_content, base_url)
        resultado_final["analisis_html"] = analisis
        
        if analisis:
            print(f"   Se encontraron {len(analisis)} tipos de datos")
            for clave, valor in analisis.items():
                if isinstance(valor, list):
                    print(f"   - {clave}: {len(valor)} elementos")
                else:
                    print(f"   - {clave}: encontrado")
        
        # Extraer títulos y meta información
        import re
        titulo_match = re.search(r'<title>([^<]+)</title>', html_content)
        if titulo_match:
            resultado_final["informacion_general"]["titulo"] = titulo_match.group(1).strip()
            print(f"\n   Título: {titulo_match.group(1).strip()}")
        
        # Buscar enlaces a otras páginas importantes
        enlaces = re.findall(r'href=["\']([^"\']+comparador[^"\']*)["\']', html_content)
        if enlaces:
            resultado_final["informacion_general"]["enlaces_relacionados"] = list(set(enlaces))[:10]
        
    except Exception as e:
        print(f"   Error: {e}")
    
    # 3. Buscar APIs
    print("\n3. Buscando endpoints de API...")
    apis = buscar_api_endpoints(base_url)
    resultado_final["apis_encontradas"] = apis
    
    if apis:
        print(f"\n   ✓ Se encontraron {len(apis)} endpoint(s) con datos")
    else:
        print("   No se encontraron APIs públicas directamente accesibles")
    
    # 4. Información sobre el sitio
    print("\n4. Información general del sitio:")
    
    # Verificar otras páginas del sitio
    paginas_importance = [
        "/",
        "/vehiculos",
        "/marcas",
        "/modelos",
    ]
    
    for pagina in paginas_importance:
        url = urljoin(base_url, pagina)
        try:
            resp = requests.head(url, headers=headers, verify=False, timeout=5)
            if resp.status_code == 200:
                print(f"   ✓ {pagina} - disponible")
        except:
            pass
    
    # Guardar resultados completos
    print("\n" + "=" * 60)
    print("Guardando resultados...")
    
    with open("datos_consumovehicular_completos.json", "w", encoding="utf-8") as f:
        json.dump(resultado_final, f, ensure_ascii=False, indent=2, default=str)
    
    print("✓ Archivo guardado: 'datos_consumovehicular_completos.json'")
    
    # Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"URL analizada: {url_comparador}")
    print(f"Fecha: {resultado_final['fecha_extraccion']}")
    print(f"Título: {resultado_final['informacion_general'].get('titulo', 'N/A')}")
    print(f"APIs encontradas: {len(apis)}")
    print(f"Datos en HTML: {'Sí' if analisis else 'No'}")
    
    print("\nArchivos generados:")
    print("  - consumovehicular_html.txt (HTML crudo)")
    print("  - datos_consumovehicular_completos.json (datos estructurados)")
    
    # Nota importante sobre limitaciones
    print("\n" + "=" * 60)
    print("NOTA IMPORTANTE")
    print("=" * 60)
    print("""
Este sitio web es una aplicación de una sola página (SPA) construida con React.
Los datos se cargan dinámicamente mediante JavaScript, por lo que:

1. El HTML estático solo contiene la estructura básica
2. Los datos reales de vehículos se cargan después mediante llamadas AJAX
3. Para obtener todos los datos, se necesita:
   - Un navegador real (Chrome/Firefox) con Selenium o Playwright
   - O identificar las endpoints de API específicas inspeccionando las 
     llamadas de red en el navegador (F12 -> Network)

Recomendación: Abre el sitio en tu navegador, abre las herramientas de 
desarrollador (F12), ve a la pestaña Network/Red, y observa qué llamadas 
se hacen cuando cargas la página del comparador. Esas URLs son las APIs 
que contienen los datos reales.
""")
    
    return resultado_final


if __name__ == "__main__":
    extraer_informacion_pagina()
