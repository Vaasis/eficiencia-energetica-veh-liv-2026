"""
Script para extraer datos del sitio web https://www.consumovehicular.cl/comparador

Este sitio es una SPA (Single Page Application) construida con React.
Hay dos enfoques posibles:

OPCIÓN 1: Usar Playwright con un navegador real (recomendado para obtener todos los datos visibles)
OPCIÓN 2: Inspeccionar las llamadas de red en el navegador para encontrar la API backend

Requisitos:
    pip install playwright
    playwright install chromium

Uso:
    python scrape_consumovehicular.py
"""

import json
import time
from playwright.sync_api import sync_playwright


def scrape_comparador():
    """Extrae los datos del comparador de vehículos"""
    url = "https://www.consumovehicular.cl/comparador"
    
    print(f"Navegando a {url}...")
    
    with sync_playwright() as p:
        # Lanzar el navegador en modo headless
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        try:
            # Navegar a la página y esperar a que cargue
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Dar tiempo adicional para que React renderice completamente
            page.wait_for_timeout(5000)
            
            # Extraer el texto completo de la página
            body_text = page.inner_text("body")
            
            # Intentar encontrar elementos específicos del comparador
            # Buscar tablas, listas de vehículos, etc.
            vehiculos_data = []
            
            # Intentar capturar cualquier tabla en la página
            tables = page.query_selector_all("table")
            if tables:
                print(f"Se encontraron {len(tables)} tabla(s)")
                for i, table in enumerate(tables):
                    table_text = table.inner_text()
                    if table_text.strip():
                        vehiculos_data.append({
                            "tipo": "tabla",
                            "indice": i,
                            "contenido": table_text[:500]
                        })
            
            # Buscar elementos con clases comunes en comparadores
            selectores_comunes = [
                "[class*='vehicle']",
                "[class*='auto']",
                "[class*='carro']",
                "[class*='comparador']",
                "[class*='tabla']",
                ".row",
                ".card",
                ".item"
            ]
            
            for selector in selectores_comunes:
                try:
                    elementos = page.query_selector_all(selector)
                    if elementos:
                        print(f"Selector '{selector}': {len(elementos)} elemento(s)")
                        for elem in elementos[:5]:
                            texto = elem.inner_text().strip()
                            if texto and len(texto) > 10:
                                vehiculos_data.append({
                                    "tipo": "elemento",
                                    "selector": selector,
                                    "contenido": texto[:200]
                                })
                except:
                    pass
            
            # Obtener el HTML completo renderizado
            html_renderizado = page.content()
            
            # Ejecutar JavaScript para obtener información adicional
            info_js = page.evaluate("""() => {
                return {
                    titulo: document.title,
                    url: window.location.href,
                    bodyLength: document.body.innerText.length,
                    metaDescription: document.querySelector('meta[name="description"]')?.content || '',
                    totalElementos: document.querySelectorAll('*').length
                };
            }""")
            
            # Capturar una captura de pantalla (opcional)
            try:
                page.screenshot(path="captura_comparador.png", full_page=True)
                print("Captura de pantalla guardada como 'captura_comparador.png'")
            except Exception as e:
                print(f"No se pudo guardar la captura: {e}")
            
            # Preparar resultados
            resultado = {
                "url": url,
                "fecha_extraccion": time.strftime("%Y-%m-%d %H:%M:%S"),
                "info_js": info_js,
                "vehiculos_encontrados": len(vehiculos_data),
                "datos_vehiculos": vehiculos_data,
                "html_renderizado_longitud": len(html_renderizado),
                "body_text_muestra": body_text[:2000] if body_text else ""
            }
            
            # Guardar resultados en JSON
            with open("datos_consumovehicular.json", "w", encoding="utf-8") as f:
                json.dump(resultado, f, ensure_ascii=False, indent=2)
            
            # Guardar HTML completo
            with open("consumovehicular_renderizado.html", "w", encoding="utf-8") as f:
                f.write(html_renderizado)
            
            # Guardar texto completo
            with open("consumovehicular_texto.txt", "w", encoding="utf-8") as f:
                f.write(body_text)
            
            print("\n" + "=" * 60)
            print("=== Resultados ===")
            print("=" * 60)
            print(f"Título: {info_js.get('titulo', 'N/A')}")
            print(f"URL: {info_js.get('url', 'N/A')}")
            print(f"Largo del texto: {info_js.get('bodyLength', 0)} caracteres")
            print(f"Elementos encontrados: {len(vehiculos_data)}")
            print(f"HTML renderizado: {len(html_renderizado)} caracteres")
            print("\nArchivos guardados:")
            print("  - datos_consumovehicular.json")
            print("  - consumovehicular_renderizado.html")
            print("  - consumovehicular_texto.txt")
            
            if vehiculos_data:
                print("\n=== Muestra de datos encontrados ===")
                for i, item in enumerate(vehiculos_data[:5], 1):
                    print(f"\n{i}. Tipo: {item['tipo']}")
                    contenido_preview = item['contenido'].replace('\n', ' ')[:150]
                    print(f"   Contenido: {contenido_preview}...")
            
            return resultado
            
        except Exception as e:
            print(f"Error durante el scraping: {e}")
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Scraper para Consumo Vehicular - Comparador")
    print("=" * 60)
    
    scrape_comparador()
